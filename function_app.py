import azure.functions as func

from blueprints.health import bp as health_bp
from blueprints.data_endpoints import bp as data_bp
from blueprints.pricing import bp as pricing_bp

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_blueprint(health_bp)
app.register_blueprint(data_bp)
app.register_blueprint(pricing_bp)