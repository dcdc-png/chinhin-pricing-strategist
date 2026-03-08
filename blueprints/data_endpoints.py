import azure.functions as func
import json
from shared.data import get_db

bp = func.Blueprint()

@bp.route(route="debug/columns", methods=["GET"])
def debug_columns(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
    if not _db:
        return func.HttpResponse("Excel not loaded", status_code=503)
    res = {sheet: list(_db[sheet].columns) for sheet in _db}
    return func.HttpResponse(json.dumps(res), mimetype="application/json")


@bp.route(route="customers", methods=["GET"])
def get_customers(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
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


@bp.route(route="items", methods=["GET"])
def get_items(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
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
