import json
import threading
import asyncio
import os
import azure.functions as func
import pandas as pd
from db import get_db

bp = func.Blueprint()

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME       = os.getenv("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist")
AGENT_VERSION    = os.getenv("AZURE_AI_AGENT_VERSION", "3")
AGENT_MODEL      = os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano")


def get_openai_client():
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set.")
    return AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    ).get_openai_client()


@bp.route(route="api/pricing", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def pricing_analysis(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
    if not _db:
        return func.HttpResponse(
            json.dumps({"error": "Excel not loaded"}),
            mimetype="application/json",
            status_code=503,
        )

    # ---- parse request body ----
    try:
        body = req.get_json()
        customer_id = body["customer_id"]
        item_code   = body["item_code"]
    except (ValueError, KeyError) as exc:
        return func.HttpResponse(
            json.dumps({"error": f"Invalid request body: {exc}"}),
            mimetype="application/json",
            status_code=400,
        )

    # ---- gather context data ----
    crm      = _db["crm"]
    price_df = _db["price"]
    sales_df = _db["sales"]
    comp_df  = _db["competitor"]

    customer_row = crm[crm["Customer ID"] == customer_id]
    item_row     = price_df[price_df["Item Code"] == item_code]
    comp_row     = comp_df[comp_df["Item Code"] == item_code]

    if customer_row.empty:
        return func.HttpResponse(
            json.dumps({"error": f"Customer '{customer_id}' not found"}),
            mimetype="application/json",
            status_code=404,
        )
    if item_row.empty:
        return func.HttpResponse(
            json.dumps({"error": f"Item '{item_code}' not found"}),
            mimetype="application/json",
            status_code=404,
        )

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

    list_price  = float(item.get("List Price (RM)", 0))
    market_low  = float(comp.get("Market Low (RM)",  list_price * 0.80)) if comp else list_price * 0.80
    market_high = float(comp.get("Market High (RM)", list_price))        if comp else list_price

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

    # ---- call agent synchronously (Azure Functions does not support true streaming) ----
    result_container = {}
    error_container  = {}

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
            result_container["data"] = {
                "actual_points":         actual_points,
                "list_price":            list_price,
                "market_low":            market_low,
                "market_high":           market_high,
                "min_price":             agent_data.get("min_price",             market_low),
                "recommended_price":     agent_data.get("recommended_price",     list_price),
                "optimal_price_points":  agent_data.get("optimal_price_points",  []),
                "discount_ceiling":      agent_data.get("discount_ceiling",       0),
                "reasoning":             agent_data.get("reasoning",             ""),
                "customer_name":         customer.get("Customer Name", ""),
                "item_name":             item.get("Item Name", ""),
                "loyalty_tier":          customer.get("Loyalty Tier", ""),
                "price_sensitivity":     customer.get("Price Sensitivity", ""),
            }

        except json.JSONDecodeError as exc:
            error_container["message"] = f"Agent returned invalid JSON: {exc}"
        except Exception as exc:
            error_container["message"] = str(exc)

    t = threading.Thread(target=run_agent, daemon=True)
    t.start()
    t.join()

    # Azure Functions HTTP triggers do not support true streaming;
    # return the full buffered SSE payload as a single response.
    if error_container:
        sse_body = f"data: {json.dumps({'type': 'error', 'message': error_container['message']})}\n\n"
        return func.HttpResponse(
            sse_body,
            mimetype="text/event-stream",
            status_code=200,
        )

    sse_body = f"data: {json.dumps({'type': 'result', 'data': result_container['data']}, default=str)}\n\n"
    return func.HttpResponse(
        sse_body,
        mimetype="text/event-stream",
        status_code=200,
    )
