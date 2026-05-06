from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


Signal = Literal["BUY", "SELL", "HOLD"]
Regime = Literal["bullish", "bearish", "sideways", "high_volatility"]


@dataclass
class ExplainabilityLog:
    timestamp: str
    ticker: str
    signal: Signal
    confidence: float
    rationale: str
    rsi14: float | None
    rsi_sma9: float | None
    atr14: float | None
    ema200: float | None
    ssma9: float | None
    regime: Regime
    sentiment: float | None


@dataclass
class Trade:
    timestamp: str
    ticker: str
    side: Literal["BUY", "SELL"]
    qty: float
    price: float
    stop_loss: float
    take_profit: float
    pnl: float = 0.0
    fees: float = 0.0


@dataclass
class Position:
    ticker: str
    qty: float
    avg_price: float
    stop_loss: float
    take_profit: float

