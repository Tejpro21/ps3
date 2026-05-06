from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.csv_normalize import normalize_macro_csv, normalize_market_csv, split_multi_asset_wide


def _candidate_paths(root: str, filename: str) -> List[str]:
    return [
        os.path.join(root, "datasets", filename),
        os.path.join(root, filename),
    ]


@dataclass
class DataRegistry:
    root_dir: str = field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    market_frames: Dict[str, pd.DataFrame] = field(default_factory=dict)  # ticker -> df
    macro_frame: Optional[pd.DataFrame] = None
    sources: Dict[str, str] = field(default_factory=dict)  # ticker -> source file

    @property
    def asset_count(self) -> int:
        return len(self.market_frames)

    @property
    def macro_loaded(self) -> bool:
        return self.macro_frame is not None and len(self.macro_frame) > 0

    def available_assets(self) -> List[str]:
        return sorted(self.market_frames.keys())

    def get_asset_frame(self, ticker: str) -> pd.DataFrame:
        return self.market_frames[ticker]

    def load_all_datasets(self) -> None:
        self.market_frames.clear()
        self.macro_frame = None
        self.sources.clear()

        market_files = [
            "oil_dataset.csv",
            "equity_dataset.csv",
            "multi_asset_dataset.csv",
        ]
        macro_file = "macro_dataset.csv"

        for fn in market_files:
            path = self._resolve_path(fn)
            raw = pd.read_csv(path)
            if fn == "multi_asset_dataset.csv":
                long = split_multi_asset_wide(raw)
                norm = normalize_market_csv(long, source_name=fn)
            else:
                norm = normalize_market_csv(raw, source_name=fn)
            for ticker, df in norm.items():
                if ticker not in self.market_frames:
                    self.market_frames[ticker] = df
                    self.sources[ticker] = fn
                else:
                    # merge additional rows for same ticker (keep newest)
                    merged = pd.concat([self.market_frames[ticker], df], axis=0, ignore_index=False)
                    merged = merged[~merged.index.duplicated(keep="last")].sort_index()
                    self.market_frames[ticker] = merged

        macro_path = self._resolve_path(macro_file)
        macro_raw = pd.read_csv(macro_path)
        self.macro_frame = normalize_macro_csv(macro_raw, source_name=macro_file)

        # Align macro to market timeline by forward-fill on timestamp for quick lookup.
        if self.macro_frame is not None and len(self.macro_frame) > 0:
            self.macro_frame = self.macro_frame.sort_index()

        # Final cleanup: enforce monotonic index and dtype sanity
        for t, df in list(self.market_frames.items()):
            df = df.sort_index()
            df = df[~df.index.duplicated(keep="last")]
            df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].apply(
                pd.to_numeric, errors="coerce"
            )
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(subset=["close"], inplace=True)
            df["volume"] = df["volume"].fillna(0.0)
            self.market_frames[t] = df

    def _resolve_path(self, filename: str) -> str:
        for p in _candidate_paths(self.root_dir, filename):
            if os.path.exists(p):
                return p
        raise FileNotFoundError(
            f"Missing required dataset '{filename}'. Expected in 'datasets/' or project root. root_dir={self.root_dir}"
        )

