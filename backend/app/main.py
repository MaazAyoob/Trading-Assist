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

    # Start Binance WebSocket stream manager for default BTC/USDT 15m & 1h
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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
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
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs for details."},
    )
