import azure.functions as func

bp = func.Blueprint()


@bp.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        '{"status": "ok"}',
        mimetype="application/json",
        status_code=200,
    )


@bp.route(route="", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def root(req: func.HttpRequest) -> func.HttpResponse:
    """Serve the frontend index.html."""
    import os
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    index_path = os.path.normpath(index_path)
    if not os.path.exists(index_path):
        return func.HttpResponse("index.html not found", status_code=404)
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return func.HttpResponse(content, mimetype="text/html", status_code=200)
