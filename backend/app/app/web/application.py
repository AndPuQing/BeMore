from fastapi import FastAPI
from fastapi.responses import UJSONResponse

import app as appx  # just to get version
from app.core.config import settings
from app.log import configure_logging
from app.web.api.router import api_router
from app.web.lifetime import register_shutdown_event, register_startup_event


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    configure_logging()
    app = FastAPI(
        title="bemore",
        version=appx.version,
        docs_url=f"{settings.API_STR}/docs",
        redoc_url=f"{settings.API_STR}/redoc",
        openapi_url=f"{settings.API_STR}/openapi.json",
        default_response_class=UJSONResponse,
    )

    # Adds startup and shutdown events.
    register_startup_event(app)
    register_shutdown_event(app)

    # Main router for the API.
    app.include_router(router=api_router, prefix=f"{settings.API_STR}")

    return app