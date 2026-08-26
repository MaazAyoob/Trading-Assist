from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.router import api_router
from app.api.v1.endpoints.ws import router as ws_router
from app.data.ws_manager import ws_manager
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup structured logging
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} backend...")

    # Initialize database
    await init_db()

    # Start Binance WebSocket stream manager for default BTC/USDT 1m, 15m & 1h
    await ws_manager.start(settings.DEFAULT_SYMBOL, "1m")
    await ws_manager.start(settings.DEFAULT_SYMBOL, "15m")
    await ws_manager.start(settings.DEFAULT_SYMBOL, "1h")

    yield

    # Clean shutdown
    logger.info("Stopping background tasks and WebSocket managers...")
    await ws_manager.stop()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Deterministic Multi-Factor Crypto Market Analysis & Trading Intelligence Engine",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

import re

VERCEL_ORIGIN_REGEX = r"^https:\/\/([a-zA-Z0-9_-]+\.)*vercel\.app$"
_compiled_vercel_regex = re.compile(VERCEL_ORIGIN_REGEX)


def is_cors_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return False
    origins_list = (
        settings.BACKEND_CORS_ORIGINS
        if isinstance(settings.BACKEND_CORS_ORIGINS, list)
        else [settings.BACKEND_CORS_ORIGINS]
    )
    if "*" in origins_list:
        return True
    if origin in origins_list:
        return True
    if _compiled_vercel_regex.fullmatch(origin):
        return True
    return False


def get_cors_headers_for_request(request: Request) -> dict[str, str]:
    origin = request.headers.get("origin")
    if origin and is_cors_allowed_origin(origin):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Vary": "Origin",
        }
    return {}


# CORS fallback middleware to guarantee headers on all HTTP responses and uncaught errors
@app.middleware("http")
async def cors_fallback_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
        cors_headers = get_cors_headers_for_request(request)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check server logs for details."},
            headers=cors_headers,
        )

    if origin and is_cors_allowed_origin(origin):
        if "access-control-allow-origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
    return response


# Standard Starlette CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.BACKEND_CORS_ORIGINS)
    if isinstance(settings.BACKEND_CORS_ORIGINS, list)
    else [settings.BACKEND_CORS_ORIGINS],
    allow_origin_regex=VERCEL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Top level WebSocket route `/ws/market/{symbol}/{timeframe}`
app.include_router(ws_router, prefix="/ws")

# API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "default_pair": settings.DEFAULT_SYMBOL,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    cors_headers = get_cors_headers_for_request(request)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
        headers=cors_headers,
    )
