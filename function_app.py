import json
import asyncio
import threading
import pandas as pd
import azure.functions as func
import logging

from utils.data_loader import get_db
from utils.agent import get_openai_client

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "ok"}),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="api/debug/columns", methods=["GET"])
def debug_columns(req: func.HttpRequest) -> func.HttpResponse:
    """Returns actual column names from each sheet - use this to verify column name mapping."""
    db = get_db()
    if not db:
        return func.HttpResponse(
            json.dumps({"detail": "Excel not loaded"}), 
            status_code=503, 
            mimetype="application/json"
        )
        
    columns = {sheet: list(db[sheet].columns) for sheet in db}
    return func.HttpResponse(
        json.dumps(columns), 
        status_code=200, 
        mimetype="application/json"
    )

@app.route(route="api/customers", methods=["GET"])
def get_customers(req: func.HttpRequest) -> func.HttpResponse:
    """Returns a list of customer dictionaries."""
    db = get_db()
    if not db or "crm" not in db:
        return func.HttpResponse(
            json.dumps({"detail": "Excel not loaded"}), 
            status_code=503, 
            mimetype="application/json"
        )
        
    crm = db["crm"]
    customers = (
        crm[["Customer ID", "Customer Name"]]
        .drop_duplicates()
        .sort_values("Customer Name")
        .to_dict(orient="records")
    )
    
    return func.HttpResponse(
        json.dumps(customers),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="api/items", methods=["GET"])
def get_items(req: func.HttpRequest) -> func.HttpResponse:
    """Returns a list of item dictionaries."""
    db = get_db()
    if not db or "price" not in db:
        return func.HttpResponse(
            json.dumps({"detail": "Excel not loaded"}), 
            status_code=503, 
            mimetype="application/json"
        )
        
    price = db["price"]
    items = (
        price[["Item Code", "Item Name", "Category"]]
        .drop_duplicates()
        .sort_values("Item Name")
        .to_dict(orient="records")
    )
    
    return func.HttpResponse(
        json.dumps(items),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="api/pricing", methods=["POST"])
async def pricing_analysis(req: func.HttpRequest) -> func.HttpResponse:
    db = get_db()
    if not db:
        return func.HttpResponse(
            "Excel not loaded", 
            status_code=503
        )

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    customer_id = req_body.get("customer_id")
    item_code = req_body.get("item_code")

    if not customer_id or not item_code:
        return func.HttpResponse("Missing customer_id or item_code", status_code=400)

    # ---- gather context data ----
    crm       = db["crm"]
    price_df  = db["price"]
    sales_df  = db["sales"]
    comp_df   = db["competitor"]

    customer_row = crm[crm["Customer ID"] == customer_id]
    item_row     = price_df[price_df["Item Code"] == item_code]
    comp_row     = comp_df[comp_df["Item Code"] == item_code]

    if customer_row.empty:
        return func.HttpResponse(f"Customer '{customer_id}' not found", status_code=404)
    if item_row.empty:
        return func.HttpResponse(f"Item '{item_code}' not found", status_code=404)

    customer = customer_row.iloc[0].to_dict()
    item     = item_row.iloc[0].to_dict()
    comp     = comp_row.iloc[0].to_dict() if not comp_row.empty else {}

    # sales history for this customer + item
    history = sales_df[
        (sales_df["Customer ID"] == customer_id) &
        (sales_df["Item Code"]   == item_code)
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

    async def event_stream():
        import os
        agent_model = os.environ.get("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano")
        agent_name = os.environ.get("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist")
        agent_version = os.environ.get("AZURE_AI_AGENT_VERSION", "3")
        
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def run_agent():
            try:
                client = get_openai_client()
                full_text = ""

                with client.responses.stream(
                    model=agent_model,
                    input=[{"role": "user", "content": prompt}],
                    extra_body={
                        "agent_reference": {
                            "name": agent_name,
                            "version": agent_version,
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
                    f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
                )

            except json.JSONDecodeError as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    f"data: {json.dumps({'type': 'error', 'message': f'Agent returned invalid JSON: {exc}'})}\n\n"
                )
            except Exception as exc:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
                )
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        t = threading.Thread(target=run_agent, daemon=True)
        t.start()

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk.encode('utf-8')

    return func.HttpResponse(
        body=event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )