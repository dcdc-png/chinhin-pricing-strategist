import os
import json
import asyncio
import threading

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME      = os.getenv("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist")
AGENT_VERSION   = os.getenv("AZURE_AI_AGENT_VERSION", "3")
AGENT_MODEL     = os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano")
EXCEL_PATH      = os.getenv("EXCEL_PATH", "data.xlsx")


# ---------------------------------------------------------------------------
# Excel loader (cached at startup)
# ---------------------------------------------------------------------------

_db: dict = {}

def load_excel():
    global _db
    if not os.path.exists(EXCEL_PATH):
        print(f"[WARN] Excel file not found at '{EXCEL_PATH}'. "
              "Set EXCEL_PATH in .env and restart.")
        return
    xl = pd.ExcelFile(EXCEL_PATH)
    _db["price"]      = xl.parse("Price Sheet")
    _db["sales"]      = xl.parse("Sales History")
    _db["competitor"] = xl.parse("Competitor Pricing")
    _db["crm"]        = xl.parse("CRM Sheet")
    # normalise column names: strip whitespace
    for key in _db:
        _db[key].columns = _db[key].columns.str.strip()
    print(f"[INFO] Loaded Excel: {EXCEL_PATH}")

load_excel()


# ---------------------------------------------------------------------------
# OpenAI client helper
# ---------------------------------------------------------------------------

def get_openai_client():
    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set.")
    return AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    ).get_openai_client()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Foundry Pricing Backend")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/debug/columns")
async def debug_columns():
    """Returns actual column names from each sheet - use this to verify column name mapping."""
    if not _db:
        raise HTTPException(503, "Excel not loaded")
    return {sheet: list(_db[sheet].columns) for sheet in _db}




# ---------------------------------------------------------------------------
# Data endpoints (dropdowns)
# ---------------------------------------------------------------------------

@app.get("/api/customers")
async def get_customers():
    if "crm" not in _db:
        raise HTTPException(503, "Excel not loaded")
    crm = _db["crm"]
    customers = (
        crm[["Customer ID", "Customer Name"]]
        .drop_duplicates()
        .sort_values("Customer Name")
        .to_dict(orient="records")
    )
    return customers


@app.get("/api/items")
async def get_items():
    if "price" not in _db:
        raise HTTPException(503, "Excel not loaded")
    price = _db["price"]
    items = (
        price[["Item Code", "Item Name", "Category"]]
        .drop_duplicates()
        .sort_values("Item Name")
        .to_dict(orient="records")
    )
    return items


# ---------------------------------------------------------------------------
# Pricing analysis endpoint
# ---------------------------------------------------------------------------

class PricingRequest(BaseModel):
    customer_id: str
    item_code: str


@app.post("/api/pricing")
async def pricing_analysis(request: PricingRequest):
    if not _db:
        raise HTTPException(503, "Excel not loaded")

    # ---- gather context data ----
    crm       = _db["crm"]
    price_df  = _db["price"]
    sales_df  = _db["sales"]
    comp_df   = _db["competitor"]

    customer_row = crm[crm["Customer ID"] == request.customer_id]
    item_row     = price_df[price_df["Item Code"] == request.item_code]
    comp_row     = comp_df[comp_df["Item Code"] == request.item_code]

    if customer_row.empty:
        raise HTTPException(404, f"Customer '{request.customer_id}' not found")
    if item_row.empty:
        raise HTTPException(404, f"Item '{request.item_code}' not found")

    customer = customer_row.iloc[0].to_dict()
    item     = item_row.iloc[0].to_dict()
    comp     = comp_row.iloc[0].to_dict() if not comp_row.empty else {}

    # sales history for this customer + item
    history = sales_df[
        (sales_df["Customer ID"] == request.customer_id) &
        (sales_df["Item Code"]   == request.item_code)
    ].sort_values("Date")

    history_records = history[
        ["Date", "Qty Ordered", "Unit Price Given (RM)", "List Price (RM)", "Discount %", "Total Value (RM)"]
    ].to_dict(orient="records")

    # derive chart data from sales history
    actual_points = [
        {"qty": float(r["Qty Ordered"]), "price": float(r["Unit Price Given (RM)"])}
        for r in history_records
        if pd.notna(r["Qty Ordered"]) and pd.notna(r["Unit Price Given (RM)"])
    ]

    list_price   = float(item.get("List Price (RM)", 0))
    market_low   = float(comp.get("Market Low (RM)", list_price * 0.80)) if comp else list_price * 0.80
    market_high  = float(comp.get("Market High (RM)", list_price)) if comp else list_price

    # ---- build prompt for agent ----
    prompt = f"""
You are a pricing strategist. Analyze the following data and return a JSON object (and ONLY a JSON object, no markdown, no explanation) with this exact structure:

{{
  "optimal_price_points": [
    {{"qty": <number>, "price": <number>}},
    ...  // 5–8 points covering the realistic qty range for this customer/item
  ],
  "min_price": <number>,       // absolute floor price (below this = loss)
  "recommended_price": <number>, // single best price for this customer
  "reasoning": "<2–3 sentence plain English explanation>",
  "discount_ceiling": <number>  // maximum % discount to offer this customer
}}

CUSTOMER PROFILE:
{json.dumps(customer, default=str, indent=2)}

ITEM DETAILS:
{json.dumps(item, default=str, indent=2)}

COMPETITOR PRICING:
{json.dumps(comp, default=str, indent=2)}

SALES HISTORY (this customer × this item, chronological):
{json.dumps(history_records, default=str, indent=2)}

Rules:
- min_price must be >= market_low and must preserve at least 10% margin
- optimal_price_points should show how price can decrease as qty increases (volume discount curve)
- factor in the customer's Loyalty Tier, Price Sensitivity, and Avg Discount Requested %
- recommended_price is the best single price for a typical order from this customer
- Respond with ONLY the JSON object, no code fences, no extra text.
"""

    # ---- call agent (sync in thread, stream back SSE) ----
    async def event_stream():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def run_agent():
            try:
                client = get_openai_client()
                full_text = ""

                with client.responses.stream(
                    model=AGENT_MODEL,
                    input=[{"role": "user", "content": prompt}],
                    extra_body={
                        "agent_reference": {
                            "name": AGENT_NAME,
                            "version": AGENT_VERSION,
                            "type": "agent_reference",
                        }
                    },
                ) as stream:
                    for event in stream:
                        event_type = getattr(event, "type", None)
                        if event_type == "response.output_text.delta":
                            text = getattr(event, "delta", None)
                            if text:
                                full_text += text
                        elif event_type and "delta" in event_type:
                            delta = getattr(event, "delta", None)
                            if isinstance(delta, str) and delta:
                                full_text += delta
                            elif delta:
                                text = getattr(delta, "text", None) or getattr(delta, "content", None)
                                if text:
                                    full_text += text

                # parse agent JSON
                clean = full_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                agent_data = json.loads(clean)

                # merge with chart context
                result = {
                    "actual_points":  actual_points,
                    "list_price":     list_price,
                    "market_low":     market_low,
                    "market_high":    market_high,
                    "min_price":      agent_data.get("min_price", market_low),
                    "recommended_price": agent_data.get("recommended_price", list_price),
                    "optimal_price_points": agent_data.get("optimal_price_points", []),
                    "discount_ceiling": agent_data.get("discount_ceiling", 0),
                    "reasoning":      agent_data.get("reasoning", ""),
                    "customer_name":  customer.get("Customer Name", ""),
                    "item_name":      item.get("Item Name", ""),
                    "loyalty_tier":   customer.get("Loyalty Tier", ""),
                    "price_sensitivity": customer.get("Price Sensitivity", ""),
                }

                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    f"data: {json.dumps({'type': 'result', 'data': result})}\n\n",
                )

            except json.JSONDecodeError as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    f"data: {json.dumps({'type': 'error', 'message': f'Agent returned invalid JSON: {exc}'})}\n\n",
                )
            except Exception as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n",
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        t = threading.Thread(target=run_agent, daemon=True)
        t.start()

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )