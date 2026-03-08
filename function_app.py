import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="hello")
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP trigger function received a request 123456789.")

    name = req.params.get("name", "World")

    return func.HttpResponse(
        f"Hello, {name}!",
        status_code=200
    )