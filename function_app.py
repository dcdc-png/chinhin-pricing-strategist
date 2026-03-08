"""
function_app.py
Azure Functions v2 — main entry point.
Loads Excel at cold-start and registers the pricing blueprint.
"""
import logging
import azure.functions as func

from blueprints.pricing import bp, load_excel

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_blueprint(bp)

@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("pong", status_code=200)
