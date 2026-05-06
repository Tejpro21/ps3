from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from utils.preprocessing import handle_missing_values, smooth_outliers


REQUIRED_MARKET_COLS = {"timestamp", "ticker", "open", "high", "low", "close", "volume"}
REQUIRED_MACRO_COLS = {"timestamp", "interest_rate", "inflation", "gdp_growth", "market_sentiment"}


def _coerce_timestamp(series: pd.Series) -> pd.DatetimeIndex:
    ts = pd.to_datetime(series, errors="coerce", utc=False)
    if ts.isna().all():
        raise ValueError("Could not parse any timestamps")
    return pd.DatetimeIndex(ts)


def split_multi_asset_wide(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts the provided hackathon-style wide CSV:
      Date,Oil,Gold,Bonds,...
    Returns a long frame with columns: timestamp,ticker,close,volume?
    """
    df = raw.copy()
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("timestamp") or cols.get("date")
    if not date_col:
        raise ValueError("multi_asset_dataset.csv missing Date/timestamp column")
    ts = _coerce_timestamp(df[date_col])
    wide = df.drop(columns=[date_col])

    # Take only numeric columns that look like asset prices (skip *_Returns)
    asset_cols = [c for c in wide.columns if ("return" not in c.lower()) and pd.api.types.is_numeric_dtype(wide[c])]
    long = wide[asset_cols].copy()
    long.insert(0, "timestamp", ts)
    long = long.melt(id_vars=["timestamp"], var_name="ticker", value_name="close")
    long["volume"] = 0.0
    return long


def normalize_market_csv(raw: pd.DataFrame, source_name: str) -> Dict[str, pd.DataFrame]:
    """
    Returns a dict {ticker: df} where df index is timestamp and columns:
      open,high,low,close,volume (float)

    Supports:
    - required schema
    - hackathon schema: Date,Price,Volume,...
    - long-ish: timestamp,ticker,close,volume
    """
    df = raw.copy()
    lower = {c.lower(): c for c in df.columns}

    if REQUIRED_MARKET_COLS.issubset(set(lower.keys())):
        mapped = {k: lower[k] for k in REQUIRED_MARKET_COLS}
        out = df.rename(columns={mapped["timestamp"]: "timestamp", mapped["ticker"]: "ticker"})
        for k in ["open", "high", "low", "close", "volume"]:
            out[k] = pd.to_numeric(out[mapped[k]], errors="coerce")
        out["timestamp"] = _coerce_timestamp(out["timestamp"])
        out = out[["timestamp", "ticker", "open", "high", "low", "close", "volume"]]
    else:
        # Hackathon/adaptive normalization
        date_col = lower.get("timestamp") or lower.get("date")
        if not date_col:
            raise ValueError(f"{source_name}: Missing timestamp/date column")

        ts = _coerce_timestamp(df[date_col])
        out = pd.DataFrame({"timestamp": ts})

        if "ticker" in lower:
            out["ticker"] = df[lower["ticker"]].astype(str)
        else:
            # Use the file stem as ticker if not present
            stem = source_name.replace("_dataset.csv", "").upper()
            out["ticker"] = stem

        price_col = lower.get("close") or lower.get("price") or lower.get("adj_close") or lower.get("value")
        vol_col = lower.get("volume")
        if price_col is None:
            raise ValueError(f"{source_name}: Missing price/close column")
        close = pd.to_numeric(df[price_col], errors="coerce")
        volume = pd.to_numeric(df[vol_col], errors="coerce") if vol_col else 0.0

        # Synthetic OHLC from close when absent (reasonable for hackathon data)
        prev = close.shift(1)
        open_ = prev.fillna(close)
        spread = (close - open_).abs().fillna(0.0)
        # ensure some wick for visuals/ATR
        wick = (0.001 * close.abs()).fillna(0.0) + spread * 0.5
        high = np.maximum(open_, close) + wick
        low = np.minimum(open_, close) - wick

        out["open"] = open_
        out["high"] = high
        out["low"] = low
        out["close"] = close
        out["volume"] = volume

    out = out.dropna(subset=["timestamp", "ticker", "close"]).copy()
    out["ticker"] = out["ticker"].astype(str).str.upper()
    out = out.sort_values("timestamp")

    # Missing + outlier handling (per ticker) without forward-looking bias
    by_ticker: Dict[str, pd.DataFrame] = {}
    for ticker, g in out.groupby("ticker", sort=False):
        g = g.copy()
        g.set_index("timestamp", inplace=True)
        g = handle_missing_values(g, cols=["open", "high", "low", "close", "volume"])
        g = smooth_outliers(g, cols=["open", "high", "low", "close"], z=8.0)
        by_ticker[ticker] = g

    return by_ticker


def normalize_macro_csv(raw: pd.DataFrame, source_name: str) -> pd.DataFrame:
    df = raw.copy()
    lower = {c.lower(): c for c in df.columns}

    if REQUIRED_MACRO_COLS.issubset(set(lower.keys())):
        mapped = {k: lower[k] for k in REQUIRED_MACRO_COLS}
        out = df.rename(columns={mapped["timestamp"]: "timestamp"})
        out["timestamp"] = _coerce_timestamp(out["timestamp"])
        out = out.assign(
            interest_rate=pd.to_numeric(out[mapped["interest_rate"]], errors="coerce"),
            inflation=pd.to_numeric(out[mapped["inflation"]], errors="coerce"),
            gdp_growth=pd.to_numeric(out[mapped["gdp_growth"]], errors="coerce"),
            market_sentiment=pd.to_numeric(out[mapped["market_sentiment"]], errors="coerce"),
        )
        out = out[["timestamp", "interest_rate", "inflation", "gdp_growth", "market_sentiment"]]
    else:
        # Hackathon macro: Date,Inflation,Interest_Rate,USD_Index,Sentiment
        date_col = lower.get("timestamp") or lower.get("date")
        if not date_col:
            raise ValueError(f"{source_name}: Missing timestamp/date column")
        out = pd.DataFrame({"timestamp": _coerce_timestamp(df[date_col])})

        infl = lower.get("inflation")
        ir = lower.get("interest_rate") or lower.get("interest rate")
        gdp = lower.get("gdp_growth") or lower.get("gdp growth")
        sent = lower.get("market_sentiment") or lower.get("sentiment")

        out["interest_rate"] = pd.to_numeric(df[ir], errors="coerce") if ir else np.nan
        out["inflation"] = pd.to_numeric(df[infl], errors="coerce") if infl else np.nan
        out["gdp_growth"] = pd.to_numeric(df[gdp], errors="coerce") if gdp else 0.0
        out["market_sentiment"] = pd.to_numeric(df[sent], errors="coerce") if sent else 0.0

    out = out.dropna(subset=["timestamp"]).copy()
    out = out.sort_values("timestamp")
    out.set_index("timestamp", inplace=True)
    out = handle_missing_values(out, cols=["interest_rate", "inflation", "gdp_growth", "market_sentiment"])
    return out

