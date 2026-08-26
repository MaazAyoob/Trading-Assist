import time
from fastapi import APIRouter
from app.data.binance import BinanceMarketDataProvider

router = APIRouter()
START_TIME = time.time()


@router.get("/health", summary="Service health check")
async def health_check():
    provider = BinanceMarketDataProvider()
    binance_healthy = await provider.ping()
    await provider.close()

    return {
        "status": "online",
        "binance_connectivity": "connected" if binance_healthy else "disconnected",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "timestamp": int(time.time() * 1000),
    }
