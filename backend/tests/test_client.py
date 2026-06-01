import pytest

from backend.bot.client import BinanceFuturesClient
from backend.bot.config import Settings


class FakePythonBinanceClient:
    instances: list["FakePythonBinanceClient"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.order_params: dict | None = None
        self.FUTURES_TESTNET_URL = ""
        self.instances.append(self)

    def futures_create_order(self, **params):
        self.order_params = params
        return {
            "orderId": 123456,
            "symbol": params["symbol"],
            "status": "NEW",
            "executedQty": "0",
            "avgPrice": "0",
            "type": params["type"],
            "side": params["side"],
        }


@pytest.mark.asyncio
async def test_live_order_uses_python_binance_futures_client() -> None:
    FakePythonBinanceClient.instances.clear()
    settings = Settings(BINANCE_API_KEY="key", BINANCE_API_SECRET="secret")
    client = BinanceFuturesClient(settings, client_factory=FakePythonBinanceClient)

    response = await client.create_order(
        {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.001",
            "newOrderRespType": "RESULT",
        },
        dry_run=False,
    )

    fake_client = FakePythonBinanceClient.instances[0]
    assert fake_client.kwargs["testnet"] is True
    assert fake_client.kwargs["ping"] is False
    assert fake_client.FUTURES_TESTNET_URL == "https://testnet.binancefuture.com/fapi"
    assert fake_client.order_params == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.001",
        "newOrderRespType": "RESULT",
    }
    assert response["orderId"] == 123456
