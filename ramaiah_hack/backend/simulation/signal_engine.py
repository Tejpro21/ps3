from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from models.domain import Regime, Signal


@dataclass
class SignalResult:
    signal: Signal
    confidence: float
    rationale: str


def detect_regime(
    close: float | None,
    ema200: float | None,
    atr14: float | None,
    sentiment: float | None,
) -> Regime:
    if close is None or ema200 is None or not np.isfinite(close) or not np.isfinite(ema200):
        return "sideways"

    trend = (close - ema200) / ema200 if ema200 else 0.0
    vol = float(atr14 / close) if (atr14 is not None and np.isfinite(atr14) and close) else 0.0
    sent = float(sentiment) if sentiment is not None and np.isfinite(sentiment) else 0.0

    if vol > 0.03:
        return "high_volatility"
    if trend > 0.01 and sent >= -0.2:
        return "bullish"
    if trend < -0.01 and sent <= 0.2:
        return "bearish"
    return "sideways"


def compute_signal(
    rsi14: float | None,
    rsi_sma9: float | None,
    prev_rsi14: float | None,
    prev_rsi_sma9: float | None,
    close: float | None,
    ema200: float | None,
    ssma9: float | None,
    atr14: float | None,
) -> SignalResult:
    def ok(x):
        return x is not None and np.isfinite(x)

    if not (ok(rsi14) and ok(rsi_sma9) and ok(close) and ok(ssma9)):
        return SignalResult(signal="HOLD", confidence=0.15, rationale="Insufficient indicator history.")

    crossed_up = ok(prev_rsi14) and ok(prev_rsi_sma9) and prev_rsi14 <= prev_rsi_sma9 and rsi14 > rsi_sma9
    crossed_down = ok(prev_rsi14) and ok(prev_rsi_sma9) and prev_rsi14 >= prev_rsi_sma9 and rsi14 < rsi_sma9

    exits_oversold = rsi14 > 30.0 and (prev_rsi14 is not None and prev_rsi14 <= 30.0)
    price_above_ema = ok(ema200) and close > ema200
    ssma_bull = close > ssma9

    atr_spike = ok(atr14) and atr14 > 1.5 * float(atr14)  # placeholder (stabilized below)
    # Make atr_spike meaningful with relative volatility check when possible.
    if ok(atr14) and close and close > 0:
        atr_spike = (atr14 / close) > 0.03

    # BUY (institutional-style but not overly sparse):
    # - primary trigger: RSI crosses above RSI-SMA
    # - confirmation: price above EMA200 and above SSMA9
    # - bonus: oversold exit increases confidence, but is not required to trade
    if crossed_up and price_above_ema and ssma_bull:
        bonus = 0.08 if exits_oversold else 0.0
        confidence = 0.62 + bonus + min(0.22, max(0.0, (rsi14 - 45.0) / 100.0))
        return SignalResult(
            signal="BUY",
            confidence=float(min(confidence, 0.9)),
            rationale=(
                "RSI crossed above RSI-SMA with trend confirmation (price>EMA200) and bullish SSMA9 alignment."
                + (" Oversold exit adds confidence." if exits_oversold else "")
            ),
        )

    # SELL
    rsi_weak = ok(prev_rsi14) and rsi14 < prev_rsi14
    price_below_ssma = close < ssma9
    if crossed_down and (rsi_weak or price_below_ssma or atr_spike):
        confidence = 0.62 + (0.1 if atr_spike else 0.0) + (0.05 if price_below_ssma else 0.0)
        return SignalResult(
            signal="SELL",
            confidence=float(min(confidence, 0.9)),
            rationale="RSI crossed below RSI-SMA with weakening momentum; exit triggered by SSMA9 weakness or volatility shock.",
        )

    return SignalResult(signal="HOLD", confidence=0.35, rationale="No actionable cross/confirmation; hold state.")

