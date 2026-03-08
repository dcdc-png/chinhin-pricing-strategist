"""
function_app.py – Azure Functions v2 entry point.

Registers all blueprints:
  - health  : GET /  and GET /health
  - data    : GET /api/customers, GET /api/items, GET /api/debug/columns
  - pricing : POST /api/pricing
"""

import azure.functions as func

from blueprints.health  import bp as health_bp
from blueprints.data    import bp as data_bp
from blueprints.pricing import bp as pricing_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_functions(health_bp)
app.register_functions(data_bp)
app.register_functions(pricing_bp)
