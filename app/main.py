"""Application entrypoint for local development and deployment."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.api.routes import router
from app.core.startup import register_startup_events


def create_app() -> FastAPI:
    app = FastAPI(title="Fast Slide Maker", version="0.1.0")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.state.templates = Jinja2Templates(directory="templates")

    app.include_router(router)
    register_startup_events(app)
    return app


app = create_app()
