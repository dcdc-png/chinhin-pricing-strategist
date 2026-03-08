"""
blueprints/pricing.py
Azure Functions v2 Blueprint — Foundry Pricing API
Routes: /api/customers, /api/items, /api/pricing, /api/chat
"""
import os
import json
import asyncio
import logging
import threading

import azure.functions as func

bp = func.Blueprint()

# ---------------------------------------------------------------------------
# Config (from Application Settings / local.settings.json)
# ---------------------------------------------------------------------------
def get_config():
    """Helper to fetch config only when needed (after env vars load)."""
    return {
        "PROJECT_ENDPOINT": os.getenv("PROJECT_ENDPOINT", ""),
        "PROJECT_KEY":      os.getenv("AZURE_AI_PROJECT_KEY", ""),
        "AGENT_NAME":       os.getenv("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist"),
        "AGENT_VERSION":    os.getenv("AZURE_AI_AGENT_VERSION", "3"),
        "AGENT_MODEL":      os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano"),
        "EXCEL_PATH":       os.getenv("EXCEL_PATH", "data.xlsx"),
    }

# ---------------------------------------------------------------------------
# Excel DB (loaded once at cold-start via module import in function_app.py)
# ---------------------------------------------------------------------------
_db: dict = {}


def load_excel():
    """Ensures Excel data is loaded into memory."""
    global _db
    if _db:
        return True # already loaded

    cfg = get_config()
    excel_path = cfg["EXCEL_PATH"]
    abs_path = os.path.abspath(excel_path)
    
    logging.info("Current working directory: %s", os.getcwd())
    logging.info("Attempting to load Excel from: %s", abs_path)

    if not os.path.exists(abs_path):
        logging.error("Excel file NOT FOUND at '%s'.", abs_path)
        return False

    try:
        import pandas as pd
        xl = pd.ExcelFile(abs_path)
        _db["price"]      = xl.parse("Price Sheet")
        _db["sales"]      = xl.parse("Sales History")
        _db["competitor"] = xl.parse("Competitor Pricing")
        _db["crm"]        = xl.parse("CRM Sheet")
        for key in _db:
            _db[key].columns = _db[key].columns.str.strip()
        logging.info("Successfully loaded Excel with sheets: %s", list(_db.keys()))
        return True
    except Exception as e:
        logging.error("Failed to load Excel: %s", str(e))
        return False


# ---------------------------------------------------------------------------
# Authentication Workaround for AIProjectClient
# ---------------------------------------------------------------------------
from azure.core.pipeline.policies import SansIOHTTPPolicy

class ApiKeyPolicy(SansIOHTTPPolicy):
    """Bypasses TokenCredential logic by injecting the api-key header manually."""
    def __init__(self, key: str):
        super().__init__()
        self.key = key
    def on_request(self, request):
        request.http_request.headers["api-key"] = self.key
        if "Authorization" in request.http_request.headers:
            del request.http_request.headers["Authorization"]

class DummyTokenCredential:
    """Satisfies AIProjectClient's requirement for a credential object."""
    def get_token(self, *scopes, **kwargs):
        from azure.core.credentials import AccessToken
        import time
        return AccessToken("dummy", int(time.time()) + 3600)

def _get_project_client():
    """Returns a configured AIProjectClient with key-based policy injection."""
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential

    cfg = get_config()
    if not cfg["PROJECT_ENDPOINT"]:
        raise RuntimeError("PROJECT_ENDPOINT is not configured.")
    
    if cfg["PROJECT_KEY"]:
        logging.info("Using AIProjectClient with ApiKeyPolicy injection")
        # Initialize with dummy token to avoid attribute errors, then inject key policy
        client = AIProjectClient(
            endpoint=cfg["PROJECT_ENDPOINT"],
            credential=DummyTokenCredential(),
        )
        # Inject the policy at the start of the pipeline
        client._client._pipeline._policies.insert(0, ApiKeyPolicy(cfg["PROJECT_KEY"]))
        return client
    else:
        logging.info("Using AIProjectClient with DefaultAzureCredential")
        return AIProjectClient(
            endpoint=cfg["PROJECT_ENDPOINT"],
            credential=DefaultAzureCredential(),
        )

def _get_openai_client():
    """Returns the OpenAI-compatible client from the project."""
    return _get_project_client().get_openai_client()

# ---------------------------------------------------------------------------
# Helper: SSE header dict
# ---------------------------------------------------------------------------
def _sse_headers() -> dict:
    return {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
    }


# ---------------------------------------------------------------------------
# CORS preflight helper
# ---------------------------------------------------------------------------
def _cors_preflight() -> func.HttpResponse:
    return func.HttpResponse(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


@bp.route(route="diag", methods=["GET", "OPTIONS"])
def diagnostics(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()
    
    import sys
    cfg = get_config()
    
    pandas_status = "Not checked"
    try:
        import pandas as pd
        pandas_status = f"Success (v{pd.__version__})"
    except Exception as e:
        pandas_status = f"Failed: {str(e)}"

    expected_env_vars = [
        "PROJECT_ENDPOINT",
        "AZURE_AI_PROJECT_KEY",
        "AZURE_AI_AGENT_NAME",
        "AZURE_AI_AGENT_VERSION",
        "AZURE_AI_AGENT_MODEL",
        "EXCEL_PATH"
    ]

    # Check for keys but don't leak them
    key_val = os.getenv("AZURE_AI_PROJECT_KEY", "")
    if len(key_val) > 8:
        masked_key = f"{key_val[:4]}...{key_val[-4:]}"
    elif key_val:
        masked_key = "Present"
    else:
        masked_key = "Missing"

    diag_data = {
        "cwd": os.getcwd(),
        "sys_path": sys.path,
        "python_version": sys.version,
        "files_in_root": os.listdir("."),
        "has_pkg": os.path.exists("python_packages"),
        "pandas_import": pandas_status,
        "project_key_detected": masked_key,
        "model_name": cfg["AGENT_MODEL"],
        "endpoint": cfg["PROJECT_ENDPOINT"],
        "excel_exists": os.path.exists(os.path.abspath(cfg["EXCEL_PATH"])),
        "env_keys_present": [k for k in expected_env_vars if os.getenv(k)],
        "missing_env_vars": [k for k in expected_env_vars if not os.getenv(k)],
    }
    return func.HttpResponse(
        json.dumps(diag_data, indent=2),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ===========================================================================
# GET /api/customers
# ===========================================================================
@bp.route(route="customers", methods=["GET", "OPTIONS"])
def get_customers(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()

    import pandas as pd
    if not load_excel() or "crm" not in _db:
        err_msg = "Excel data not loaded. "
        if not os.path.exists(os.path.abspath(get_config()["EXCEL_PATH"])):
            err_msg += f"File not found at {os.path.abspath(get_config()['EXCEL_PATH'])}"
        return func.HttpResponse(
            json.dumps({"error": err_msg}),
            status_code=503,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    crm = _db["crm"]
    customers = (
        crm[["Customer ID", "Customer Name"]]
        .drop_duplicates()
        .sort_values("Customer Name")
        .to_dict(orient="records")
    )
    return func.HttpResponse(
        json.dumps(customers, default=str),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ===========================================================================
# GET /api/items
# ===========================================================================
@bp.route(route="items", methods=["GET", "OPTIONS"])
def get_items(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()

    import pandas as pd
    if not load_excel() or "price" not in _db:
        return func.HttpResponse(
            json.dumps({"error": "Excel data not available (check logs)"}),
            status_code=503,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    price = _db["price"]
    items = (
        price[["Item Code", "Item Name", "Category"]]
        .drop_duplicates()
        .sort_values("Item Name")
        .to_dict(orient="records")
    )
    return func.HttpResponse(
        json.dumps(items, default=str),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


# ===========================================================================
# POST /api/pricing  — SSE stream
# ===========================================================================
@bp.route(route="pricing", methods=["POST", "OPTIONS"])
def pricing_analysis(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()

    import pandas as pd
    if not load_excel():
        return func.HttpResponse(
            json.dumps({"error": "Excel data not available"}),
            status_code=503,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json",
        )

    customer_id = body.get("customer_id", "")
    item_code   = body.get("item_code", "")

    if not customer_id or not item_code:
        return func.HttpResponse(
            json.dumps({"error": "customer_id and item_code are required"}),
            status_code=400,
            mimetype="application/json",
        )

    crm      = _db["crm"]
    price_df = _db["price"]
    sales_df = _db["sales"]
    comp_df  = _db["competitor"]

    customer_row = crm[crm["Customer ID"] == customer_id]
    item_row     = price_df[price_df["Item Code"] == item_code]

    if customer_row.empty:
        return func.HttpResponse(
            json.dumps({"error": f"Customer '{customer_id}' not found"}),
            status_code=404,
            mimetype="application/json",
        )
    if item_row.empty:
        return func.HttpResponse(
            json.dumps({"error": f"Item '{item_code}' not found"}),
            status_code=404,
            mimetype="application/json",
        )

    customer = customer_row.iloc[0].to_dict()
    item     = item_row.iloc[0].to_dict()
    comp_row = comp_df[comp_df["Item Code"] == item_code]
    comp     = comp_row.iloc[0].to_dict() if not comp_row.empty else {}

    history = sales_df[
        (sales_df["Customer ID"] == customer_id) &
        (sales_df["Item Code"]   == item_code)
    ].sort_values("Date")

    history_records = history[
        ["Date", "Qty Ordered", "Unit Price Given (RM)", "List Price (RM)", "Discount %", "Total Value (RM)"]
    ].to_dict(orient="records")

    actual_points = [
        {"qty": float(r["Qty Ordered"]), "price": float(r["Unit Price Given (RM)"])}
        for r in history_records
        if pd.notna(r["Qty Ordered"]) and pd.notna(r["Unit Price Given (RM)"])
    ]

    list_price  = float(item.get("List Price (RM)", 0))
    market_low  = float(comp.get("Market Low (RM)",  list_price * 0.80)) if comp else list_price * 0.80
    market_high = float(comp.get("Market High (RM)", list_price))        if comp else list_price

    prompt = f"""
You are a pricing strategist. Analyze the following data and return a JSON object (and ONLY a JSON object, no markdown, no explanation) with this exact structure:

{{
  "optimal_price_points": [
    {{"qty": <number>, "price": <number>}},
    ...
  ],
  "min_price": <number>,
  "recommended_price": <number>,
  "reasoning": "<2–3 sentence plain English explanation>",
  "discount_ceiling": <number>
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
- optimal_price_points should show how price decreases as qty increases (volume discount curve, 5–8 points)
- factor in the customer's Loyalty Tier, Price Sensitivity, and Avg Discount Requested %
- recommended_price is the best single price for a typical order from this customer
- Respond with ONLY the JSON object, no code fences, no extra text.
"""

    # Run agent synchronously in a thread and collect SSE output
    result_chunks: list[str] = []
    error_chunks: list[str]  = []
    done_event = threading.Event()

    def run_agent():
        try:
            cfg       = get_config()
            client    = _get_openai_client()
            full_text = ""

            with client.responses.stream(
                model=cfg["AGENT_MODEL"],
                input=[{"role": "user", "content": prompt}],
                extra_body={
                    "agent": {
                        "name": cfg["AGENT_NAME"],
                        "version": cfg["AGENT_VERSION"],
                        "type": "agent_reference",
                    }
                },
            ) as stream:
                for event in stream:
                    event_type = getattr(event, "type", None)
                    if event_type == "response.output_text.delta":
                        delta = getattr(event, "delta", None)
                        if delta:
                            full_text += delta
                    elif event_type and "delta" in event_type:
                        delta = getattr(event, "delta", None)
                        if isinstance(delta, str) and delta:
                            full_text += delta
                        elif delta:
                            text = getattr(delta, "text", None) or getattr(delta, "content", None)
                            if text:
                                full_text += text

            clean      = full_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            agent_data = json.loads(clean)

            result = {
                "actual_points":         actual_points,
                "list_price":            list_price,
                "market_low":            market_low,
                "market_high":           market_high,
                "min_price":             agent_data.get("min_price", market_low),
                "recommended_price":     agent_data.get("recommended_price", list_price),
                "optimal_price_points":  agent_data.get("optimal_price_points", []),
                "discount_ceiling":      agent_data.get("discount_ceiling", 0),
                "reasoning":             agent_data.get("reasoning", ""),
                "customer_name":         customer.get("Customer Name", ""),
                "item_name":             item.get("Item Name", ""),
                "loyalty_tier":          customer.get("Loyalty Tier", ""),
                "price_sensitivity":     customer.get("Price Sensitivity", ""),
            }
            result_chunks.append(f"data: {json.dumps({'type': 'result', 'data': result})}\n\n")

        except json.JSONDecodeError as exc:
            error_chunks.append(
                f"data: {json.dumps({'type': 'error', 'message': f'Agent returned invalid JSON: {exc}'})}\n\n"
            )
        except Exception as exc:
            error_chunks.append(
                f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            )
        finally:
            done_event.set()

    t = threading.Thread(target=run_agent, daemon=True)
    t.start()
    done_event.wait(timeout=120)  # 2-min hard timeout

    body_text = result_chunks[0] if result_chunks else (
        error_chunks[0] if error_chunks else
        f"data: {json.dumps({'type': 'error', 'message': 'Agent timed out or returned no data'})}\n\n"
    )

    return func.HttpResponse(
        body_text,
        status_code=200,
        headers=_sse_headers(),
    )


# ===========================================================================
# POST /api/chat  — SSE stream (free-text conversation with Foundry agent)
# ===========================================================================
@bp.route(route="chat", methods=["POST", "OPTIONS"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return _cors_preflight()

    import pandas as pd
    # Load data (even if not strictly needed for chat, often good for context)
    load_excel()

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            status_code=400,
            mimetype="application/json",
        )

    message        = body.get("message", "").strip()
    context_blurb  = body.get("context", "")   # optional context (customer, item, pricing result)

    if not message:
        return func.HttpResponse(
            json.dumps({"error": "message is required"}),
            status_code=400,
            mimetype="application/json",
        )

    system_prompt = (
        "You are Fiamma's AI Pricing Strategist. You help sales managers make smart pricing decisions "
        "for hardware products. Answer concisely and practically. Use Malaysian Ringgit (RM) for prices."
    )
    if context_blurb:
        system_prompt += f"\n\nCurrent pricing context:\n{context_blurb}"

    # Run agent, collect full reply, send back in one SSE chunk
    reply_chunks: list[str] = []
    error_chunks: list[str] = []
    done_event = threading.Event()

    def run_chat():
        try:
            cfg       = get_config()
            client    = _get_openai_client()
            full_text = ""

            with client.responses.stream(
                model=cfg["AGENT_MODEL"],
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": message},
                ],
                extra_body={
                    "agent": {
                        "name": cfg["AGENT_NAME"],
                        "version": cfg["AGENT_VERSION"],
                        "type": "agent_reference",
                    }
                },
            ) as stream:
                for event in stream:
                    event_type = getattr(event, "type", None)
                    if event_type == "response.output_text.delta":
                        delta = getattr(event, "delta", None)
                        if delta:
                            full_text += delta
                    elif event_type and "delta" in event_type:
                        delta = getattr(event, "delta", None)
                        if isinstance(delta, str) and delta:
                            full_text += delta
                        elif delta:
                            text = getattr(delta, "text", None) or getattr(delta, "content", None)
                            if text:
                                full_text += text

            reply_chunks.append(
                f"data: {json.dumps({'type': 'message', 'text': full_text.strip()})}\n\n"
            )
        except Exception as exc:
            error_chunks.append(
                f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            )
        finally:
            done_event.set()

    t = threading.Thread(target=run_chat, daemon=True)
    t.start()
    done_event.wait(timeout=60)

    body_text = reply_chunks[0] if reply_chunks else (
        error_chunks[0] if error_chunks else
        f"data: {json.dumps({'type': 'error', 'message': 'Agent timed out'})}\n\n"
    )

    return func.HttpResponse(
        body_text,
        status_code=200,
        headers=_sse_headers(),
    )
