"""Pydantic models shared by the CLI and API layers."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class OrderRequest(BaseModel):
    """Validated user intent before mapping to Binance Futures parameters."""

    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=False)

    symbol: str = Field(..., examples=["BTCUSDT"])
    side: OrderSide
    order_type: OrderType = Field(..., alias="type")
    quantity: Decimal = Field(..., gt=0, examples=["0.001"])
    price: Decimal | None = Field(None, gt=0, examples=["68000"])
    stop_price: Decimal | None = Field(None, gt=0, examples=["67500"])
    dry_run: bool = Field(
        default=False,
        description="When true, validate and log the order without sending it to Binance.",
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        symbol = value.upper().replace("/", "").replace("-", "")
        if not symbol.endswith("USDT"):
            raise ValueError("Only Binance USDT-M Futures symbols are supported, e.g. BTCUSDT.")
        if not symbol.isalnum() or len(symbol) < 6:
            raise ValueError("Symbol must contain only letters/numbers, e.g. BTCUSDT.")
        return symbol

    @model_validator(mode="after")
    def validate_price_requirements(self) -> "OrderRequest":
        if self.order_type == OrderType.MARKET and self.price is not None:
            raise ValueError("Price is not accepted for MARKET orders.")
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Price is required for LIMIT orders.")
        if self.order_type == OrderType.STOP_LIMIT:
            if self.price is None:
                raise ValueError("Limit price is required for STOP_LIMIT orders.")
            if self.stop_price is None:
                raise ValueError("Stop price is required for STOP_LIMIT orders.")
        return self


class OrderResponse(BaseModel):
    """Normalized order response printed by the CLI and returned by the API."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    order_id: int | str
    status: str
    executed_qty: Decimal = Field(default=Decimal("0"))
    avg_price: Decimal | None = None
    dry_run: bool = False
    raw: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str
