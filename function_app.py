import azure.functions as func
import os
import json
import asyncio
import threading
import pandas as pd
import logging
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Initialize the Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# --- Configuration & Global Data ---
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME      = os.getenv("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist")
AGENT_VERSION   = os.getenv("AZURE_AI_AGENT_VERSION", "3")
AGENT_MODEL     = os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano")
EXCEL_PATH      = os.path.join(os.getcwd(), os.getenv("EXCEL_PATH", "data.xlsx"))

_db: dict = {}

def load_excel():
    global _db
    if not os.path.exists(EXCEL_PATH):
        logging.warning(f"Excel file not found at '{EXCEL_PATH}'.")
        return
    xl = pd.ExcelFile(EXCEL_PATH)
    _db["price"]      = xl.parse("Price Sheet")
    _db["sales"]      = xl.parse("Sales History")
    _db["competitor"] = xl.parse("Competitor Pricing")
    _db["crm"]        = xl.parse("CRM Sheet")
    for key in _db:
        _db[key].columns = _db[key].columns.str.strip()
    logging.info(f"Loaded Excel: {EXCEL_PATH}")

load_excel()

def get_openai_client():
    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set.")
    return AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    ).get_openai_client()

# --- Endpoints ---

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(json.dumps({"status": "ok"}), mimetype="application/json")

@app.route(route="debug/columns", methods=["GET"])
def debug_columns(req: func.HttpRequest) -> func.HttpResponse:
    if not _db:
        return func.HttpResponse("Excel not loaded", status_code=503)
    res = {sheet: list(_db[sheet].columns) for sheet in _db}
    return func.HttpResponse(json.dumps(res), mimetype="application/json")

@app.route(route="customers", methods=["GET"])
def get_customers(req: func.HttpRequest) -> func.HttpResponse:
    if "crm" not in _db:
        return func.HttpResponse("Excel not loaded", status_code=503)
    crm = _db["crm"]
    customers = (
        crm[["Customer ID", "Customer Name"]]
        .drop_duplicates()
        .sort_values("Customer Name")
        .to_dict(orient="records")
    )
    return func.HttpResponse(json.dumps(customers), mimetype="application/json")

@app.route(route="items", methods=["GET"])
def get_items(req: func.HttpRequest) -> func.HttpResponse:
    if "price" not in _db:
        return func.HttpResponse("Excel not loaded", status_code=503)
    price = _db["price"]
    items = (
        price[["Item Code", "Item Name", "Category"]]
        .drop_duplicates()
        .sort_values("Item Name")
        .to_dict(orient="records")
    )
    return func.HttpResponse(json.dumps(items), mimetype="application/json")

@app.route(route="pricing", methods=["POST"])
async def pricing_analysis(req: func.HttpRequest) -> func.HttpResponse:
    if not _db:
        return func.HttpResponse("Excel not loaded", status_code=503)

    try:
        req_body = req.get_json()
        customer_id = req_body.get("customer_id")
        item_code = req_body.get("item_code")
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    # ---- Data Gathering (same logic as your FastAPI version) ----
    crm = _db["crm"]
    price_df = _db["price"]
    sales_df = _db["sales"]
    comp_df = _db["competitor"]

    customer_row = crm[crm["Customer ID"] == customer_id]
    item_row = price_df[price_df["Item Code"] == item_code]
    comp_row = comp_df[comp_df["Item Code"] == item_code]

    if customer_row.empty or item_row.empty:
        return func.HttpResponse("Customer or Item not found", status_code=404)

    customer = customer_row.iloc[0].to_dict()
    item = item_row.iloc[0].to_dict()
    comp = comp_row.iloc[0].to_dict() if not comp_row.empty else {}

    history = sales_df[(sales_df["Customer ID"] == customer_id) & (sales_df["Item Code"] == item_code)].sort_values("Date")
    history_records = history[["Date", "Qty Ordered", "Unit Price Given (RM)", "List Price (RM)", "Discount %", "Total Value (RM)"]].to_dict(orient="records")

    actual_points = [{"qty": float(r["Qty Ordered"]), "price": float(r["Unit Price Given (RM)"])} for r in history_records if pd.notna(r["Qty Ordered"]) and pd.notna(r["Unit Price Given (RM)"])]

    list_price = float(item.get("List Price (RM)", 0))
    market_low = float(comp.get("Market Low (RM)", list_price * 0.80)) if comp else list_price * 0.80
    market_high = float(comp.get("Market High (RM)", list_price)) if comp else list_price

    prompt = f"..." # (Use the exact prompt string from your original code)

    async def event_stream():
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        def run_agent():
            try:
                client = get_openai_client()
                full_text = ""
                with client.responses.stream(
                    model=AGENT_MODEL,
                    input=[{"role": "user", "content": prompt}],
                    extra_body={"agent_reference": {"name": AGENT_NAME, "version": AGENT_VERSION, "type": "agent_reference"}},
                ) as stream:
                    for event in stream:
                        # ... (Streaming parsing logic exactly as you have it)
                        pass 

                # Result construction logic...
                result = {"type": "result", "data": {}} # Simplified for brevity, use your full merge logic
                loop.call_soon_threadsafe(queue.put_nowait, f"data: {json.dumps(result)}\n\n")
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        threading.Thread(target=run_agent, daemon=True).start()

        while True:
            chunk = await queue.get()
            if chunk is None: break
            yield chunk

    return func.HttpResponse(event_stream(), mimetype="text/event-stream")