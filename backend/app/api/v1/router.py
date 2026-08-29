from fastapi import APIRouter
from app.api.v1.endpoints import market, ws, health, analysis, backtesting, forensics, strategy_research, shadow, trade_decision, profiles, scalp, scalp_v2

api_router = APIRouter()
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Quantitative Analysis"])
api_router.include_router(trade_decision.router, prefix="/trade-decision", tags=["Trade Decision & Risk Planning"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Trading Profiles & Multi-Horizon"])
api_router.include_router(scalp.router, prefix="/scalp", tags=["SCALP Strategy V1"])
api_router.include_router(scalp_v2.router, prefix="/scalp-v2", tags=["SCALP Strategy V2"])
api_router.include_router(scalp_v2.compare_router, prefix="/scalp", tags=["SCALP Comparison"])
api_router.include_router(forensics.router, prefix="/analysis/forensics", tags=["Signal Forensics & Attribution"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["Backtesting & Validation"])
api_router.include_router(strategy_research.router, prefix="/strategy-research", tags=["Strategy Research & Redesign"])
api_router.include_router(shadow.router, prefix="/shadow", tags=["Shadow Validation"])
api_router.include_router(health.router, tags=["System Health"])
api_router.include_router(ws.router, prefix="/ws", tags=["WebSockets"])

