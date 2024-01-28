from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import UJSONResponse

import app as appx  # just to get version
from app.core.config import settings
from app.db.init_db import init
from app.log import configure_logging
from app.web.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the lifespan of the application.

    :param app: current FastAPI application.
    """
    app.middleware_stack = None
    app.middleware_stack = app.build_middleware_stack()
    init()
    yield
    pass


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
        lifespan=lifespan,
    )

    # Main router for the API.
    app.include_router(router=api_router, prefix=f"{settings.API_STR}")

    return app
