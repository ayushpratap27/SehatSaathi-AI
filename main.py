"""
SehatSaathi-AI — FastAPI application entry point.

Run the development server with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging

# ---- Bootstrap logging before anything else emits messages --------------- #
settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
logger = logging.getLogger(__name__)


# ---- Application lifespan ------------------------------------------------ #

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manage startup and shutdown tasks.

    Startup:
        - Log application boot information.
        - (Future phases) initialise DB connections, AI model warm-up, etc.

    Shutdown:
        - (Future phases) flush caches, close DB pools, etc.
    """
    # --- startup ---
    logger.info("Starting SehatSaathi-AI v%s [%s]", settings.APP_VERSION, settings.ENV)
    logger.info("API docs available at http://%s:%s/docs", settings.HOST, settings.PORT)

    # Initialise database tables (dev / test — production uses Alembic)
    if settings.ENV != "production":
        from app.database.init_db import init_db  # noqa: PLC0415
        await init_db()

    yield

    # --- shutdown ---
    logger.info("SehatSaathi-AI shutting down.")


# ---- Application factory ------------------------------------------------- #

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    Kept as a factory function so tests can create isolated instances
    without triggering side effects at import time.

    Returns:
        Fully configured :class:`FastAPI` instance.
    """
    application = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- Middleware ------------------------------------------------------- #
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Global exception handlers --------------------------------------- #
    register_exception_handlers(application)

    # ---- API routers ----------------------------------------------------- #
    application.include_router(api_router, prefix="/api/v1")

    # ---- Root & health endpoints ----------------------------------------- #

    @application.get("/", tags=["Root"], summary="Application info")
    async def root() -> dict:
        """Return basic application information and navigation links."""
        return {
            "name": settings.APP_NAME,
            "description": settings.APP_DESCRIPTION,
            "version": settings.APP_VERSION,
            "environment": settings.ENV,
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1",
        }

    @application.get("/health", tags=["Health"], summary="Health check")
    async def health_check() -> dict:
        """
        Liveness probe endpoint.

        Returns HTTP 200 while the application is running normally.
        """
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENV,
        }

    return application


# ---- ASGI app instance --------------------------------------------------- #
app = create_application()
