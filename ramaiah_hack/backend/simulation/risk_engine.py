from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RiskDecision:
    qty: float
    stop_loss: float
    take_profit: float
    risk_per_trade: float


def atr_position_sizing(
    cash: float,
    price: float,
    atr14: float | None,
    risk_fraction: float = 0.01,
    atr_stop_mult: float = 2.0,
    rr: float = 3.0,
    max_notional_fraction: float = 0.25,
) -> RiskDecision | None:
    """
    ATR-based sizing:
    - stop distance = atr_stop_mult * ATR
    - qty = (cash * risk_fraction) / stop_distance
    - clamp notional to max_notional_fraction of cash
    """
    if cash <= 0 or price <= 0 or atr14 is None or not np.isfinite(atr14) or atr14 <= 0:
        return None

    stop_distance = atr_stop_mult * atr14
    risk_budget = cash * risk_fraction
    qty = risk_budget / stop_distance

    # Volatility-aware adjustment: reduce size when ATR% is high
    atr_pct = atr14 / price
    if np.isfinite(atr_pct) and atr_pct > 0.0:
        qty *= float(1.0 / (1.0 + 10.0 * atr_pct))

    notional = qty * price
    max_notional = cash * max_notional_fraction
    if notional > max_notional and max_notional > 0:
        qty = max_notional / price

    if qty * price < 1.0:
        return None

    stop_loss = price - stop_distance
    take_profit = price + rr * stop_distance

    return RiskDecision(qty=float(qty), stop_loss=float(stop_loss), take_profit=float(take_profit), risk_per_trade=float(risk_budget))

