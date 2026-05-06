from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ssma(series: pd.Series, window: int) -> pd.Series:
    """
    Smoothed SMA (recursive), lightweight and stable for replay.
    """
    values = series.to_numpy(dtype=float)
    out = np.full_like(values, np.nan, dtype=float)
    if len(values) < window:
        return pd.Series(out, index=series.index)
    seed = np.nanmean(values[:window])
    out[window - 1] = seed
    alpha = 1.0 / window
    for i in range(window, len(values)):
        prev = out[i - 1]
        x = values[i]
        if np.isnan(prev):
            out[i] = x
        else:
            out[i] = prev + alpha * (x - prev)
    return pd.Series(out, index=series.index)


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    tr = true_range(df["high"], df["low"], df["close"])
    return tr.rolling(window=window, min_periods=window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0.0)
    down = (-delta).clip(lower=0.0)
    roll_up = up.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    roll_down = down.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = roll_up / roll_down.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr14"] = atr(out, 14)
    out["rsi14"] = rsi(out["close"], 14)
    out["rsi_sma9"] = sma(out["rsi14"], 9)
    out["ema200"] = ema(out["close"], 200)
    out["ssma9"] = ssma(out["close"], 9)
    return out

