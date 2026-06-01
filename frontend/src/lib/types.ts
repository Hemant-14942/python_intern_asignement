export type OrderSide = "BUY" | "SELL";
export type OrderType = "MARKET" | "LIMIT" | "STOP_LIMIT";

export type OrderFormState = {
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: string;
  price: string;
  stopPrice: string;
  dryRun: boolean;
};

export type OrderResponse = {
  symbol: string;
  side: OrderSide;
  order_type: OrderType;
  order_id: string | number;
  status: string;
  executed_qty: string;
  avg_price: string | null;
  dry_run: boolean;
  raw: Record<string, unknown>;
};
