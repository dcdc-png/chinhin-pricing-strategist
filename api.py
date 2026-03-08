import json
import azure.functions as func

# Use absolute import because this will be executed from the root function_app.py
from utils.data_loader import get_db

bp = func.Blueprint()

@bp.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Simple health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "ok"}),
        status_code=200,
        mimetype="application/json"
    )

@bp.route(route="api/debug/columns", methods=["GET"])
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

@bp.route(route="api/customers", methods=["GET"])
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

@bp.route(route="api/items", methods=["GET"])
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
