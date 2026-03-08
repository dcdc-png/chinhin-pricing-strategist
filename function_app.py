"""
function_app.py
Azure Functions v2 — main entry point.
Loads Excel at cold-start and registers the pricing blueprint.
"""
import logging
import os
import sys
import azure.functions as func

# Ensure local dependencies in .python_packages are in the path
# This is required for "No Build" deployments where we bundle our own libs
site_packages = os.path.join(os.getcwd(), ".python_packages", "lib", "site-packages")
if os.path.exists(site_packages) and site_packages not in sys.path:
    sys.path.insert(0, site_packages)

from blueprints.pricing import bp, load_excel

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_blueprint(bp)

@app.route(route="ping", methods=["GET"])
def ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("pong", status_code=200)
