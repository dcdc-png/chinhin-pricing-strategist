import json
import azure.functions as func
from db import get_db

bp = func.Blueprint()


@bp.route(route="api/customers", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_customers(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
    if "crm" not in _db:
        return func.HttpResponse(
            json.dumps({"error": "Excel not loaded"}),
            mimetype="application/json",
            status_code=503,
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
        status_code=200,
    )


@bp.route(route="api/items", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def get_items(req: func.HttpRequest) -> func.HttpResponse:
    _db = get_db()
    if "price" not in _db:
        return func.HttpResponse(
            json.dumps({"error": "Excel not loaded"}),
            mimetype="application/json",
            status_code=503,
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
        status_code=200,
    )


@bp.route(route="api/debug/columns", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def debug_columns(req: func.HttpRequest) -> func.HttpResponse:
    """Returns actual column names from each sheet - use this to verify column name mapping."""
    _db = get_db()
    if not _db:
        return func.HttpResponse(
            json.dumps({"error": "Excel not loaded"}),
            mimetype="application/json",
            status_code=503,
        )
    result = {sheet: list(_db[sheet].columns) for sheet in _db}
    return func.HttpResponse(
        json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )
