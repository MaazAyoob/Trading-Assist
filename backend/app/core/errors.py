from fastapi import HTTPException, status


class MarketDataException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(status_code=status_code, detail=detail)


class SymbolNotFoundException(HTTPException):
    def __init__(self, symbol: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{symbol}' is not supported or not found."
        )


class TimeframeNotSupportedException(HTTPException):
    def __init__(self, timeframe: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timeframe '{timeframe}' is not supported. Valid: 1m, 5m, 15m, 1h, 4h, 1d"
        )


class InsufficientDataException(HTTPException):
    def __init__(self, reason: str = "Insufficient historical market data available."):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=reason
        )
