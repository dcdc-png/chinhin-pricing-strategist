import azure.functions as func

from api import bp as api_bp
from pricing import bp as pricing_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_functions(api_bp)
app.register_functions(pricing_bp)