import httpx
import pytest

from backend.main import app


@pytest.mark.asyncio
async def test_api_places_dry_run_market_order() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/orders",
            json={
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "0.001",
                "dry_run": True,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DRY_RUN_ACCEPTED"
    assert str(payload["order_id"]).startswith("dry-run-")
