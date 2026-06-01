"use client";

import { FormEvent, useMemo, useState } from "react";
import type { OrderFormState, OrderResponse, OrderType } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const initialForm: OrderFormState = {
  symbol: "BTCUSDT",
  side: "BUY",
  type: "MARKET",
  quantity: "0.001",
  price: "",
  stopPrice: "",
  dryRun: true,
};

export default function Home() {
  const [form, setForm] = useState<OrderFormState>(initialForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [response, setResponse] = useState<OrderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const requiresPrice = form.type === "LIMIT" || form.type === "STOP_LIMIT";
  const requiresStop = form.type === "STOP_LIMIT";

  const flowSteps = useMemo(
    () => [
      { label: "Validate", active: true },
      { label: "Sign", active: !form.dryRun },
      { label: form.dryRun ? "Simulate" : "Send", active: true },
      { label: "Log", active: true },
    ],
    [form.dryRun],
  );

  async function submitOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setResponse(null);

    const payload = {
      symbol: form.symbol,
      side: form.side,
      type: form.type,
      quantity: form.quantity,
      price: requiresPrice ? form.price : undefined,
      stop_price: requiresStop ? form.stopPrice : undefined,
      dry_run: form.dryRun,
    };

    try {
      const result = await fetch(`${API_URL}/api/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await result.json();
      if (!result.ok) {
        throw new Error(extractError(data));
      }
      setResponse(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong while placing the order.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function update<K extends keyof OrderFormState>(key: K, value: OrderFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  return (
    <main className="shell">
      <div className="aurora auroraOne" />
      <div className="aurora auroraTwo" />

      <section className="hero">
        <div className="eyebrow">Binance Futures Testnet</div>
        <h1>Place safer testnet trades with a production-style bot flow.</h1>
        <p>
          A FastAPI backend validates each order, signs live testnet requests, records structured logs, and powers this
          responsive Next.js trading desk.
        </p>
        <div className="heroStats" aria-label="Feature highlights">
          <span>Market</span>
          <span>Limit</span>
          <span>Stop-Limit Bonus</span>
          <span>Dry-run Mode</span>
        </div>
      </section>

      <section className="terminalCard" aria-label="Order flow">
        <div className="terminalHeader">
          <div>
            <span className="dot red" />
            <span className="dot yellow" />
            <span className="dot green" />
          </div>
          <span>order-pipeline.json</span>
        </div>
        <div className="flow">
          {flowSteps.map((step, index) => (
            <div className={`flowStep ${step.active ? "active" : ""}`} key={step.label}>
              <span>{index + 1}</span>
              {step.label}
            </div>
          ))}
        </div>
      </section>

      <section className="grid">
        <form className="card orderCard" onSubmit={submitOrder}>
          <div className="cardTitle">
            <span>New order</span>
            <strong>{form.dryRun ? "Dry-run" : "Live testnet"}</strong>
          </div>

          <label>
            Symbol
            <input value={form.symbol} onChange={(event) => update("symbol", event.target.value.toUpperCase())} />
          </label>

          <div className="segmented" aria-label="Order side">
            {(["BUY", "SELL"] as const).map((side) => (
              <button
                className={form.side === side ? `selected ${side.toLowerCase()}` : ""}
                key={side}
                onClick={() => update("side", side)}
                type="button"
              >
                {side}
              </button>
            ))}
          </div>

          <label>
            Order type
            <select value={form.type} onChange={(event) => update("type", event.target.value as OrderType)}>
              <option value="MARKET">Market</option>
              <option value="LIMIT">Limit</option>
              <option value="STOP_LIMIT">Stop-Limit</option>
            </select>
          </label>

          <label>
            Quantity
            <input min="0" step="any" value={form.quantity} onChange={(event) => update("quantity", event.target.value)} />
          </label>

          {requiresPrice && (
            <label className="animatedField">
              Limit price
              <input min="0" step="any" value={form.price} onChange={(event) => update("price", event.target.value)} />
            </label>
          )}

          {requiresStop && (
            <label className="animatedField">
              Stop price
              <input min="0" step="any" value={form.stopPrice} onChange={(event) => update("stopPrice", event.target.value)} />
            </label>
          )}

          <label className="switchRow">
            <input checked={form.dryRun} onChange={(event) => update("dryRun", event.target.checked)} type="checkbox" />
            <span>
              Dry-run first
              <small>Validates, logs, and simulates without credentials.</small>
            </span>
          </label>

          <button className="submitButton" disabled={isSubmitting} type="submit">
            {isSubmitting ? "Routing order..." : "Place order"}
          </button>
        </form>

        <aside className="card resultCard">
          <div className="cardTitle">
            <span>Execution report</span>
            <strong>{response?.status ?? "Waiting"}</strong>
          </div>

          {error && <div className="alert error">{error}</div>}

          {!error && !response && (
            <div className="emptyState">
              <div className="pulseRing" />
              <p>Submit an order to see the normalized response, order ID, status, executed quantity, and average price.</p>
            </div>
          )}

          {response && (
            <div className="report">
              <Metric label="Order ID" value={String(response.order_id)} />
              <Metric label="Symbol" value={response.symbol} />
              <Metric label="Side" value={response.side} tone={response.side === "BUY" ? "positive" : "negative"} />
              <Metric label="Executed Qty" value={response.executed_qty} />
              <Metric label="Average Price" value={response.avg_price ?? "Not filled yet"} />
              <Metric label="Mode" value={response.dry_run ? "Dry-run" : "Live testnet"} />
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "positive" | "negative" }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={tone ?? ""}>{value}</strong>
    </div>
  );
}

function extractError(data: unknown) {
  if (typeof data === "object" && data !== null && "detail" in data) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (typeof detail === "object" && detail !== null && "detail" in detail) {
      return String((detail as { detail?: unknown }).detail);
    }
  }
  return "The backend rejected the order.";
}
