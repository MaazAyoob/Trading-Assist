import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Crypto AI Trading Intelligence"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://trading-assist-website.vercel.app",
        "https://trading-assist.vercel.app",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if not v_str:
                return []
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        elif isinstance(v, (list, tuple, set)):
            return [str(i).strip() for i in v if str(i).strip()]
        raise ValueError(f"Invalid BACKEND_CORS_ORIGINS value: {v}")

    # Database: Default to async SQLite for instant zero-config startup, supports PostgreSQL seamlessly
    DATABASE_URL: str = "sqlite+aiosqlite:///./crypto_trading.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Exchange Market Data Config
    DEFAULT_SYMBOL: str = "BTCUSDT"
    SUPPORTED_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    SUPPORTED_TIMEFRAMES: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]
    BINANCE_REST_BASE_URL: str = "https://data-api.binance.vision"
    BINANCE_WS_BASE_URL: str = "wss://data-stream.binance.vision"

    # API Keys (optional for public data)
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    AI_API_KEY: str = ""

    # Feature Flags
    ENABLE_PAPER_TRADING: bool = False
    ENABLE_LIVE_TRADING: bool = False  # MUST BE FALSE IN INITIAL BUILDS


settings = Settings()
