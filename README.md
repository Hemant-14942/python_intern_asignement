# Binance Futures Testnet Trading Bot

Full-stack submission for the Python Developer Intern assignment. The project includes:

- a reusable Python trading bot package,
- a FastAPI backend,
- a Typer CLI,
- structured JSON logging,
- market, limit, and bonus stop-limit order support,
- sample market/limit logs,
- a modern animated Next.js UI.

All live order calls target the Binance USDT-M Futures Testnet base URL:

```text
https://testnet.binancefuture.com
```

## Project structure

```text
backend/
  bot/
    client.py          # Signed Binance Futures REST client
    orders.py          # Order placement logic
    validators.py      # Input validation helpers
    logging_config.py  # Structured log setup
    cli.py             # CLI entry point
  main.py              # FastAPI app
  tests/
frontend/
  src/app/             # Next.js App Router UI
logs/
  sample_market_order.log
  sample_limit_order.log
requirements.txt
.env.example
```

## Backend setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Configure credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your Binance Futures Testnet API key and secret:

```text
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
```

> Dry-run mode does not need credentials. Live testnet order placement requires both values.

## CLI usage

Market order dry-run:

```bash
python -m backend.bot.cli place BTCUSDT BUY MARKET 0.001 --dry-run
```

Limit order dry-run:

```bash
python -m backend.bot.cli place ETHUSDT SELL LIMIT 0.01 --price 3500 --dry-run
```

Bonus stop-limit order dry-run:

```bash
python -m backend.bot.cli place BTCUSDT SELL STOP_LIMIT 0.001 --price 67000 --stop-price 67500 --dry-run
```

Prompt-based CLI wizard:

```bash
python -m backend.bot.cli wizard
```

Remove `--dry-run` only when your `.env` contains valid Binance Futures Testnet credentials.

## FastAPI usage

Start the backend:

```bash
uvicorn backend.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Place a dry-run order:

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "MARKET",
    "quantity": "0.001",
    "dry_run": true
  }'
```

Interactive API docs are available at:

```text
http://localhost:8000/docs
```

## Next.js UI

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the UI:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

If the backend is not running at `http://localhost:8000`, set:

```bash
NEXT_PUBLIC_API_URL=http://your-backend-host:8000
```

## Logging

Runtime logs are written as JSON lines to:

```text
logs/trading_bot.log
```

Each order logs:

- sanitized request payload,
- Binance/dry-run response payload,
- configuration, API, and network errors.

Sample deliverable logs are included:

- `logs/sample_market_order.log`
- `logs/sample_limit_order.log`

The sample logs are dry-run examples because repository submissions should not include private credentials or real account data.

## Tests

Run backend tests:

```bash
pytest
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Assumptions

- The app supports Binance USDT-M Futures symbols ending in `USDT`.
- Price is required for `LIMIT`.
- Price and stop price are required for `STOP_LIMIT`.
- `STOP_LIMIT` maps to Binance Futures order type `STOP`.
- Dry-run mode is enabled in the UI by default for safe demos.
- Live testnet orders are sent only when credentials are configured and `dry_run` is false.

## Assignment coverage

- Market and limit orders: implemented.
- BUY and SELL sides: implemented.
- CLI input validation: implemented with Typer and Pydantic.
- Clear request/response output: implemented with Rich tables.
- Separate API/client and command layers: implemented.
- Request, response, and error logging: implemented as JSON lines.
- Exception handling for invalid input, API errors, and network failures: implemented.
- Bonus: stop-limit order type, enhanced CLI wizard, and lightweight modern UI.
