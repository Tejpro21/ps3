export type Signal = "BUY" | "SELL" | "HOLD";
export type Regime = "bullish" | "bearish" | "sideways" | "high_volatility";

export type SystemStatus = {
  ok: boolean;
  assets_loaded: number;
  macro_loaded: boolean;
  simulation: {
    playing: boolean;
    speed: number;
    step: number;
    total_steps: number;
    active_ticker: string;
  };
};

export type Candle = {
  timestamp: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  atr14: number | null;
  rsi14: number | null;
  rsi_sma9: number | null;
  ema200: number | null;
  ssma9: number | null;
  sentiment?: number | null;
};

export type LatestSignalRow = {
  ticker: string;
  timestamp: string;
  signal: Signal;
  confidence: number;
  atr14: number | null;
  sentiment: number | null;
  regime: Regime;
};

export type ExplainabilityRow = {
  timestamp: string;
  ticker: string;
  signal: Signal;
  confidence: number;
  rationale: string;
  rsi14: number | null;
  rsi_sma9: number | null;
  atr14: number | null;
  ema200: number | null;
  ssma9: number | null;
  regime: Regime;
  sentiment: number | null;
};

export type DashboardData = {
  status: SystemStatus["simulation"];
  assets: string[];
  active_ticker: string;
  timeline: { step: number; total: number; timestamp: string | null };
  candles: Candle[];
  latest_signals: LatestSignalRow[];
  explainability: ExplainabilityRow[];
  portfolio: {
    cash: number;
    realized_pnl: number;
    unrealized_pnl?: number;
    exposure?: number;
    equity?: number;
    positions: Record<
      string,
      { ticker: string; qty: number; avg_price: number; stop_loss: number; take_profit: number }
    >;
    allocation?: Record<string, number>;
  };
  metrics: {
    sharpe?: number;
    max_drawdown?: number;
    volatility?: number;
    var_95?: number;
    alpha?: number;
    beta?: number;
  };
  equity_curve?: { timestamp: string; equity: number }[];
  asset_performance?: { ticker: string; series: { timestamp: string; value: number }[] }[];
};

export type SSEEvent =
  | { type: "snapshot"; data: DashboardData }
  | { type: "step"; timestamp: string; step: number; portfolio_value: number; active_ticker: string }
  | { type: "trade"; trade: any };

