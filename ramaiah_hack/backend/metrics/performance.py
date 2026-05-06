from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


def _safe_std(x: np.ndarray) -> float:
    s = float(np.nanstd(x, ddof=1)) if len(x) > 1 else float("nan")
    return s if np.isfinite(s) and s > 0 else float("nan")


def sharpe_ratio(returns: np.ndarray, risk_free_daily: float = 0.0) -> float:
    r = returns - risk_free_daily
    mu = float(np.nanmean(r))
    sigma = _safe_std(r)
    if not np.isfinite(mu) or not np.isfinite(sigma):
        return float("nan")
    return (mu / sigma) * np.sqrt(252.0)


def max_drawdown(equity: np.ndarray) -> float:
    if len(equity) == 0:
        return float("nan")
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / np.where(peak == 0, np.nan, peak)
    return float(np.nanmin(dd))


def annualized_volatility(returns: np.ndarray) -> float:
    sigma = _safe_std(returns)
    if not np.isfinite(sigma):
        return float("nan")
    return sigma * np.sqrt(252.0)


def var_historical(returns: np.ndarray, level: float = 0.95) -> float:
    if len(returns) < 20:
        return float("nan")
    q = np.nanquantile(returns, 1.0 - level)
    return float(-q)


def alpha_beta(portfolio_returns: np.ndarray, benchmark_returns: np.ndarray) -> Tuple[float, float]:
    n = min(len(portfolio_returns), len(benchmark_returns))
    if n < 50:
        return float("nan"), float("nan")
    x = benchmark_returns[:n]
    y = portfolio_returns[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask]
    y = y[mask]
    if len(x) < 50:
        return float("nan"), float("nan")
    beta = float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)) if np.var(x, ddof=1) > 0 else float("nan")
    alpha = float(np.nanmean(y) - beta * np.nanmean(x))
    return alpha * 252.0, beta


@dataclass
class MetricsSnapshot:
    sharpe: float
    max_drawdown: float
    volatility: float
    var_95: float
    alpha: float
    beta: float

    def to_dict(self) -> Dict[str, float | None]:
        def clean(x: float) -> float | None:
            return float(x) if np.isfinite(x) else None

        return {
            "sharpe": clean(self.sharpe),
            "max_drawdown": clean(self.max_drawdown),
            "volatility": clean(self.volatility),
            "var_95": clean(self.var_95),
            "alpha": clean(self.alpha),
            "beta": clean(self.beta),
        }


def compute_metrics(equity_curve: pd.Series, benchmark_curve: Optional[pd.Series] = None) -> MetricsSnapshot:
    eq = equity_curve.dropna()
    rets = eq.pct_change().dropna().to_numpy(dtype=float)
    sharpe = sharpe_ratio(rets)
    mdd = max_drawdown(eq.to_numpy(dtype=float))
    vol = annualized_volatility(rets)
    var95 = var_historical(rets, 0.95)

    alpha = float("nan")
    beta = float("nan")
    if benchmark_curve is not None:
        b = benchmark_curve.dropna()
        # align
        joined = pd.concat([eq.pct_change(), b.pct_change()], axis=1, join="inner").dropna()
        if len(joined) >= 50:
            alpha, beta = alpha_beta(joined.iloc[:, 0].to_numpy(float), joined.iloc[:, 1].to_numpy(float))

    return MetricsSnapshot(sharpe=sharpe, max_drawdown=mdd, volatility=vol, var_95=var95, alpha=alpha, beta=beta)

