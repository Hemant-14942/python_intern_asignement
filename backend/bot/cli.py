"""Command-line interface for placing Binance Futures Testnet orders."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend.bot.client import BinanceFuturesClient
from backend.bot.config import get_settings
from backend.bot.exceptions import BinanceAPIError, BinanceNetworkError, ConfigurationError
from backend.bot.logging_config import configure_logging
from backend.bot.orders import TradingBot
from backend.bot.validators import build_order_request

app = typer.Typer(
    help="Place MARKET, LIMIT, and STOP_LIMIT orders on Binance Futures Testnet.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def place(
    symbol: Annotated[str, typer.Argument(help="USDT-M Futures symbol, e.g. BTCUSDT")],
    side: Annotated[str, typer.Argument(help="BUY or SELL")],
    order_type: Annotated[str, typer.Argument(help="MARKET, LIMIT, or STOP_LIMIT")],
    quantity: Annotated[str, typer.Argument(help="Order quantity, e.g. 0.001")],
    price: Annotated[str | None, typer.Option("--price", "-p", help="Limit price for LIMIT/STOP_LIMIT orders")] = None,
    stop_price: Annotated[str | None, typer.Option("--stop-price", "-s", help="Stop trigger for STOP_LIMIT orders")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and log without sending to Binance")] = False,
) -> None:
    """Validate input, print a clear summary, place the order, and print the response."""

    settings = get_settings()
    configure_logging(settings.log_file)

    try:
        order = build_order_request(symbol, side, order_type, quantity, price, stop_price, dry_run)
    except (ValidationError, ValueError) as exc:
        console.print(Panel(str(exc), title="Invalid order input", border_style="red"))
        raise typer.Exit(code=2) from exc

    _print_order_summary(order.model_dump(mode="json", by_alias=True))

    bot = TradingBot(BinanceFuturesClient(settings))
    try:
        response = asyncio.run(bot.place_order(order))
    except (ConfigurationError, BinanceAPIError, BinanceNetworkError) as exc:
        console.print(Panel(str(exc), title="Order failed", border_style="red"))
        raise typer.Exit(code=1) from exc

    _print_order_response(response.model_dump(mode="json"))
    console.print("[bold green]Success:[/] order flow completed.")


@app.command()
def wizard() -> None:
    """Prompt-driven order entry for a friendlier CLI experience."""

    console.print(Panel("Binance Futures Testnet order wizard", border_style="cyan"))
    symbol = typer.prompt("Symbol", default="BTCUSDT")
    side = typer.prompt("Side (BUY/SELL)", default="BUY")
    order_type = typer.prompt("Order type (MARKET/LIMIT/STOP_LIMIT)", default="MARKET")
    quantity = typer.prompt("Quantity", default="0.001")
    price = None
    stop_price = None
    if order_type.upper() in {"LIMIT", "STOP_LIMIT"}:
        price = typer.prompt("Limit price")
    if order_type.upper() == "STOP_LIMIT":
        stop_price = typer.prompt("Stop price")
    dry_run = typer.confirm("Run in dry-run mode?", default=True)
    place(symbol, side, order_type, quantity, price=price, stop_price=stop_price, dry_run=dry_run)


def _print_order_summary(payload: dict) -> None:
    table = Table(title="Order request summary", show_header=True, header_style="bold magenta")
    table.add_column("Field")
    table.add_column("Value")
    for key in ["symbol", "side", "type", "quantity", "price", "stop_price", "dry_run"]:
        value = payload.get(key)
        if value is not None:
            table.add_row(key, str(value))
    console.print(table)


def _print_order_response(payload: dict) -> None:
    table = Table(title="Order response details", show_header=True, header_style="bold green")
    table.add_column("Field")
    table.add_column("Value")
    for key in ["order_id", "status", "executed_qty", "avg_price", "dry_run"]:
        table.add_row(key, str(payload.get(key)))
    console.print(table)


if __name__ == "__main__":
    app()
