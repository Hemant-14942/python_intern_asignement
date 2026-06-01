"""Domain exceptions raised by the trading bot."""


class TradingBotError(Exception):
    """Base exception for expected trading bot failures."""


class ConfigurationError(TradingBotError):
    """Raised when credentials or settings are missing for a live request."""


class BinanceAPIError(TradingBotError):
    """Raised when Binance returns an error response."""

    def __init__(self, message: str, status_code: int | None = None, payload: dict | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class BinanceNetworkError(TradingBotError):
    """Raised when a request to Binance cannot be completed."""
