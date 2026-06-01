"""FastAPI entry point for the trading bot backend."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.bot.client import BinanceFuturesClient
from backend.bot.config import Settings, get_settings
from backend.bot.exceptions import BinanceAPIError, BinanceNetworkError, ConfigurationError
from backend.bot.logging_config import configure_logging
from backend.bot.models import ErrorResponse, OrderRequest, OrderResponse
from backend.bot.orders import TradingBot


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_file)
    yield


app = FastAPI(
    title="Binance Futures Testnet Trading Bot",
    description="FastAPI wrapper around a reusable Binance Futures Testnet order client.",
    version="1.0.0",
    lifespan=lifespan,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_bot(settings: Settings = Depends(get_settings)) -> TradingBot:
    return TradingBot(BinanceFuturesClient(settings))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "trading-bot-api"}


@app.get("/api/binance/ping")
async def ping_binance(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    client = BinanceFuturesClient(settings)
    try:
        return await client.ping()
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail={"detail": str(exc), "error_type": exc.__class__.__name__}) from exc


@app.post("/api/orders", response_model=OrderResponse)
async def place_order(order: OrderRequest, bot: TradingBot = Depends(get_bot)) -> OrderResponse:
    try:
        return await bot.place_order(order)
    except ConfigurationError as exc:
        raise HTTPException(status_code=400, detail={"detail": str(exc), "error_type": exc.__class__.__name__}) from exc
    except BinanceAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code or 502,
            detail={"detail": str(exc), "error_type": exc.__class__.__name__, "payload": exc.payload},
        ) from exc
    except BinanceNetworkError as exc:
        raise HTTPException(status_code=502, detail={"detail": str(exc), "error_type": exc.__class__.__name__}) from exc
