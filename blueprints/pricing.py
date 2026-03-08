import azure.functions as func
import asyncio
import threading
import json
import pandas as pd
from shared.data import get_db
from shared.ai import get_openai_client
from shared.config import AGENT_MODEL, AGENT_NAME, AGENT_VERSION

bp = func.Blueprint()

@bp.route(route="pricing", methods=["POST"])
async def pricing_analysis(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
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
