# app/__init__.py
from fastapi import FastAPI
from .api.routes_search import router as search_router
from .api.routes_recrawl import router as recrawl_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Search Engine API",
        version="1.0.0",
        description="Scalable web search and re-crawl API"
    )

    # include routers
    app.include_router(search_router, prefix="", tags=["search"])
    app.include_router(recrawl_router, prefix="", tags=["recrawl"])

    return app

app = create_app()


