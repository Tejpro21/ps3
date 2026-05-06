from __future__ import annotations

from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


def handle_missing_values(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Missing value handling without forward-looking bias:
    - forward-fill within the ticker timeline
    - if still missing at start, backfill once (initialization only)
    """
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")
        out[c] = out[c].replace([np.inf, -np.inf], np.nan)
        out[c] = out[c].ffill().bfill(limit=1)
    return out


def smooth_outliers(df: pd.DataFrame, cols: List[str], z: float = 8.0) -> pd.DataFrame:
    """
    Robust-ish outlier smoothing using rolling median and MAD-like scale.
    Designed to avoid distorting trends while mitigating extreme spikes.
    """
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        s = pd.to_numeric(out[c], errors="coerce")
        med = s.rolling(51, min_periods=10).median()
        mad = (s - med).abs().rolling(51, min_periods=10).median()
        scale = (mad * 1.4826).replace(0, np.nan)
        zscore = (s - med) / scale
        clipped = s.where(zscore.abs() <= z, med + np.sign(zscore) * z * scale)
        out[c] = clipped
    return out

