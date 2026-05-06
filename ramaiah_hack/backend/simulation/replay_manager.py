from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional

import numpy as np
import pandas as pd

from metrics.indicators import add_indicators
from metrics.performance import compute_metrics
from models.domain import ExplainabilityLog, Regime
from services.data_registry import DataRegistry
from simulation.portfolio import Portfolio
from simulation.risk_engine import atr_position_sizing
from simulation.signal_engine import SignalResult, compute_signal, detect_regime


def _ts_str(ts: pd.Timestamp) -> str:
    if isinstance(ts, pd.Timestamp):
        return ts.isoformat()
    return str(ts)


@dataclass
class ReplayStatus:
    playing: bool
    speed: float
    step: int
    total_steps: int
    active_ticker: str


@dataclass
class ReplayManager:
    # Runtime state
    playing: bool = False
    speed: float = 1.0  # 1x baseline
    active_ticker: str = ""

    # Data
    frames: Dict[str, pd.DataFrame] = field(default_factory=dict)  # ticker -> df with indicators
    macro: Optional[pd.DataFrame] = None
    timelines: Dict[str, List[pd.Timestamp]] = field(default_factory=dict)  # ticker -> sorted timestamps
    ticker_steps: Dict[str, int] = field(default_factory=dict)  # ticker -> cursor
    step: int = 0  # active ticker cursor (mirrors ticker_steps[active_ticker])

    # Outputs
    portfolio: Portfolio = field(default_factory=Portfolio)
    explain_logs: List[ExplainabilityLog] = field(default_factory=list)
    latest_signal: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # ticker -> dict

    # Threaded replay loop (keeps this stable across sync endpoints)
    _thread: Optional[threading.Thread] = None
    _stop: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def bootstrap_from_registry(self, registry: DataRegistry) -> None:
        self.frames = {t: add_indicators(df) for t, df in registry.market_frames.items()}
        self.macro = registry.macro_frame

        self.timelines = {t: list(pd.to_datetime(df.index).sort_values()) for t, df in self.frames.items()}
        self.ticker_steps = {t: 0 for t in self.frames}
        self.step = 0
        self.playing = False
        self.speed = 1.0
        self.portfolio.reset()
        self.explain_logs.clear()
        self.latest_signal.clear()

        if not self.active_ticker:
            assets = sorted(self.frames.keys())
            self.active_ticker = assets[0] if assets else ""
        if self.active_ticker in self.ticker_steps:
            self.step = int(self.ticker_steps[self.active_ticker])

    def status(self) -> Dict[str, Any]:
        total = len(self.timelines.get(self.active_ticker, []))
        return ReplayStatus(
            playing=self.playing,
            speed=self.speed,
            step=self.step,
            total_steps=total,
            active_ticker=self.active_ticker,
        ).__dict__

    def control(self, action: str, ticker: Optional[str], speed: Optional[float]) -> None:
        with self._lock:
            if ticker and ticker in self.frames:
                self.active_ticker = ticker
                self.step = int(self.ticker_steps.get(self.active_ticker, 0))
            if speed is not None and np.isfinite(speed) and speed > 0:
                self.speed = float(speed)

            if action == "play":
                self.playing = True
                self._ensure_thread()
            elif action == "pause":
                self.playing = False
            elif action == "step_next":
                self.playing = False
                self._step_sync(+1)
            elif action == "step_prev":
                self.playing = False
                self._step_sync(-1)
            elif action == "set_speed":
                pass
            elif action == "set_active":
                pass

    def _ensure_thread(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._thread_loop, name="replay-loop", daemon=True)
        self._thread.start()

    def _thread_loop(self) -> None:
        while not self._stop.is_set():
            if not self.playing:
                time.sleep(0.05)
                continue
            with self._lock:
                self._step_sync(+1)
            time.sleep(max(0.08, 0.45 / max(self.speed, 0.1)))

    def _step_sync(self, delta: int) -> None:
        tl = self.timelines.get(self.active_ticker, [])
        if len(tl) == 0:
            return
        self.step = int(np.clip(self.step + delta, 0, len(tl) - 1))
        self.ticker_steps[self.active_ticker] = int(self.step)
        ts = pd.Timestamp(tl[self.step])
        prices = self._prices_at(ts)
        self.portfolio.check_stops(_ts_str(ts), prices)

        for ticker, df in self.frames.items():
            # Use last known candle at-or-before ts for multi-asset sync
            idx = int(df.index.searchsorted(ts, side="right") - 1)
            if idx < 0:
                continue
            row = df.iloc[idx]
            prev = df.iloc[idx - 1] if idx - 1 >= 0 else None
            sentiment = self._sentiment_at(ts)
            regime = detect_regime(
                close=float(row["close"]) if np.isfinite(row["close"]) else None,
                ema200=float(row["ema200"]) if np.isfinite(row["ema200"]) else None,
                atr14=float(row["atr14"]) if np.isfinite(row["atr14"]) else None,
                sentiment=sentiment,
            )
            sig = compute_signal(
                rsi14=_f(row.get("rsi14")),
                rsi_sma9=_f(row.get("rsi_sma9")),
                prev_rsi14=_f(prev.get("rsi14")) if prev is not None else None,
                prev_rsi_sma9=_f(prev.get("rsi_sma9")) if prev is not None else None,
                close=_f(row.get("close")),
                ema200=_f(row.get("ema200")),
                ssma9=_f(row.get("ssma9")),
                atr14=_f(row.get("atr14")),
            )
            self.latest_signal[ticker] = {
                "ticker": ticker,
                "timestamp": _ts_str(ts),
                "signal": sig.signal,
                "confidence": sig.confidence,
                "atr14": _f(row.get("atr14")),
                "sentiment": sentiment,
                "regime": regime,
            }
            self._log_explainability(ts, ticker, row, sig, regime, sentiment)
            self._execute_if_needed(ts, ticker, row, sig)

        # Periodic (monthly-ish) rebalance to avoid concentration drift
        if self.step > 0 and (self.step % 21 == 0):
            self._rebalance(ts, prices)

        self.portfolio.mark_to_market(_ts_str(ts), prices)

    def _execute_if_needed(self, ts: pd.Timestamp, ticker: str, row: pd.Series, sig: SignalResult) -> None:
        price = _f(row.get("close"))
        atr14 = _f(row.get("atr14"))
        if price is None:
            return

        # Slippage model (bps): higher ATR% => more slippage
        atr_pct = (atr14 / price) if (atr14 is not None and price and price > 0) else 0.0
        slippage_bps = float(np.clip(2.0 + 1500.0 * atr_pct, 2.0, 35.0))

        has_pos = ticker in self.portfolio.positions
        if sig.signal == "BUY" and not has_pos:
            rd = atr_position_sizing(cash=self.portfolio.cash, price=price, atr14=atr14)
            if rd is None:
                # Execution guard visibility (helps debug "signals but no trades")
                self.explain_logs.append(
                    ExplainabilityLog(
                        timestamp=_ts_str(ts),
                        ticker=ticker,
                        signal="HOLD",
                        confidence=0.05,
                        rationale="BUY signal rejected by risk sizing (ATR unavailable/invalid or size too small).",
                        rsi14=_f(row.get("rsi14")),
                        rsi_sma9=_f(row.get("rsi_sma9")),
                        atr14=_f(row.get("atr14")),
                        ema200=_f(row.get("ema200")),
                        ssma9=_f(row.get("ssma9")),
                        regime=self.latest_signal.get(ticker, {}).get("regime", "sideways"),
                        sentiment=self.latest_signal.get(ticker, {}).get("sentiment"),
                    )
                )
                return
            trade = self.portfolio.buy(
                ts=_ts_str(ts),
                ticker=ticker,
                qty=rd.qty,
                price=price,
                stop_loss=rd.stop_loss,
                take_profit=rd.take_profit,
                slippage_bps=slippage_bps,
            )
            if trade:
                # trade is already captured in portfolio trade history; SSE uses snapshots
                return

        elif sig.signal == "SELL" and has_pos:
            trade = self.portfolio.sell(ts=_ts_str(ts), ticker=ticker, price=price, slippage_bps=slippage_bps)
            if trade:
                return

    def _rebalance(self, ts: pd.Timestamp, prices: Dict[str, float]) -> None:
        """
        Lightweight rebalancing:
        - target equal weight across open positions
        - if any position exceeds target by > 15%, trim it toward target
        """
        if len(self.portfolio.positions) < 2:
            return
        alloc = self.portfolio.allocation(prices)
        if not alloc:
            return
        target = 1.0 / max(1, len(alloc))
        for t, w in alloc.items():
            if w is None or not np.isfinite(w):
                continue
            if w > target + 0.15:
                px = prices.get(t)
                pos = self.portfolio.positions.get(t)
                if px is None or pos is None or px <= 0:
                    continue
                # trim a fraction of the position
                trim_frac = min(0.5, (w - target) / max(w, 1e-9))
                qty_to_sell = float(pos.qty * trim_frac)
                if qty_to_sell * px < 10.0:
                    continue
                self.portfolio.sell_qty(ts=_ts_str(ts), ticker=t, qty=qty_to_sell, price=float(px), slippage_bps=3.0)

    def _log_explainability(
        self,
        ts: pd.Timestamp,
        ticker: str,
        row: pd.Series,
        sig: SignalResult,
        regime: Regime,
        sentiment: float | None,
    ) -> None:
        log = ExplainabilityLog(
            timestamp=_ts_str(ts),
            ticker=ticker,
            signal=sig.signal,
            confidence=float(sig.confidence),
            rationale=sig.rationale,
            rsi14=_f(row.get("rsi14")),
            rsi_sma9=_f(row.get("rsi_sma9")),
            atr14=_f(row.get("atr14")),
            ema200=_f(row.get("ema200")),
            ssma9=_f(row.get("ssma9")),
            regime=regime,
            sentiment=sentiment,
        )
        self.explain_logs.append(log)
        # keep bounded
        if len(self.explain_logs) > 5000:
            self.explain_logs = self.explain_logs[-3000:]

    def _prices_at(self, ts: pd.Timestamp) -> Dict[str, float]:
        prices: Dict[str, float] = {}
        for t, df in self.frames.items():
            idx = int(df.index.searchsorted(ts, side="right") - 1)
            if idx >= 0:
                px = _f(df.iloc[idx].get("close"))
                if px is not None:
                    prices[t] = px
        return prices

    def _sentiment_at(self, ts: pd.Timestamp) -> float | None:
        if self.macro is None or len(self.macro) == 0:
            return None
        idx = self.macro.index.searchsorted(ts, side="right") - 1
        if idx < 0:
            return None
        s = self.macro.iloc[idx].get("market_sentiment")
        return float(s) if s is not None and np.isfinite(s) else None

    async def sse_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            # periodic snapshots are robust and keep the UI synced even under missed events
            with self._lock:
                snap = self.dashboard_snapshot()
            yield {"type": "snapshot", "data": snap}
            await asyncio.sleep(0.6)

    def trade_logs(self) -> List[Dict[str, Any]]:
        return [t.__dict__ for t in self.portfolio.trade_history[-2000:]]

    def portfolio_state(self) -> Dict[str, Any]:
        tl = self.timelines.get(self.active_ticker, [])
        if len(tl) == 0:
            return {"cash": self.portfolio.cash, "positions": {}, "realized_pnl": self.portfolio.realized_pnl}
        ts = pd.Timestamp(tl[self.step])
        prices = self._prices_at(ts)
        return {
            "cash": self.portfolio.cash,
            "positions": {k: v.__dict__ for k, v in self.portfolio.positions.items()},
            "realized_pnl": self.portfolio.realized_pnl,
            "unrealized_pnl": self.portfolio.unrealized_pnl(prices),
            "exposure": self.portfolio.exposure(prices),
            "allocation": self.portfolio.allocation(prices),
            "equity": (self.portfolio.equity_curve[-1] if self.portfolio.equity_curve else self.portfolio.cash),
        }

    def performance_metrics(self) -> Dict[str, Any]:
        if not self.portfolio.equity_curve:
            return {}
        eq = pd.Series(self.portfolio.equity_curve, index=pd.to_datetime(self.portfolio.timestamps))
        # benchmark: active ticker close series (aligned)
        bench = None
        if self.active_ticker in self.frames:
            df = self.frames[self.active_ticker]
            bench = df["close"].reindex(eq.index, method="ffill")
        return compute_metrics(eq, bench).to_dict()

    def dashboard_snapshot(self) -> Dict[str, Any]:
        assets = sorted(self.frames.keys())
        active = self.active_ticker if self.active_ticker in self.frames else (assets[0] if assets else "")

        candle_series: List[Dict[str, Any]] = []
        if active:
            df = self.frames[active]
            # take window up to current step timestamp
            tl = self.timelines.get(active, [])
            ts = pd.Timestamp(tl[self.step]) if tl else None
            if ts is not None:
                upto = df.loc[:ts].tail(300)
            else:
                upto = df.tail(300)
            candle_series = [
                {
                    "timestamp": _ts_str(idx),
                    "open": _f(row.get("open")),
                    "high": _f(row.get("high")),
                    "low": _f(row.get("low")),
                    "close": _f(row.get("close")),
                    "volume": _f(row.get("volume")),
                    "atr14": _f(row.get("atr14")),
                    "rsi14": _f(row.get("rsi14")),
                    "rsi_sma9": _f(row.get("rsi_sma9")),
                    "ema200": _f(row.get("ema200")),
                    "ssma9": _f(row.get("ssma9")),
                    "sentiment": self._sentiment_at(pd.Timestamp(idx)),
                }
                for idx, row in upto.iterrows()
            ]

        latest_signals = list(self.latest_signal.values())
        latest_signals.sort(key=lambda x: x.get("ticker", ""))

        # active regime
        active_regime = None
        if active and candle_series:
            last = candle_series[-1]
            active_regime = detect_regime(last.get("close"), last.get("ema200"), last.get("atr14"), last.get("sentiment"))

        # Equity curve (for multi-asset performance panel)
        equity_curve = []
        if self.portfolio.timestamps and self.portfolio.equity_curve:
            equity_curve = [
                {"timestamp": self.portfolio.timestamps[i], "equity": float(self.portfolio.equity_curve[i])}
                for i in range(max(0, len(self.portfolio.equity_curve) - 300), len(self.portfolio.equity_curve))
            ]

        # Normalized asset performance (last 300 points up to current ts)
        asset_perf: List[Dict[str, Any]] = []
        if active:
            tl = self.timelines.get(active, [])
            ts_now = pd.Timestamp(tl[self.step]) if tl else None
            if ts_now is not None:
                for t in assets:
                    df = self.frames[t]
                    seg = df.loc[:ts_now].tail(300)
                    if len(seg) < 2:
                        continue
                    base = float(seg["close"].iloc[0]) if np.isfinite(seg["close"].iloc[0]) and seg["close"].iloc[0] != 0 else None
                    if base is None:
                        continue
                    asset_perf.append(
                        {
                            "ticker": t,
                            "series": [
                                {"timestamp": _ts_str(idx), "value": float(row["close"]) / base}
                                for idx, row in seg[["close"]].iterrows()
                                if np.isfinite(row["close"])
                            ],
                        }
                    )

        return {
            "status": self.status(),
            "assets": assets,
            "active_ticker": active,
            "timeline": {
                "step": self.step,
                "total": len(self.timelines.get(active, [])),
                "timestamp": _ts_str(self.timelines.get(active, [])[self.step]) if self.timelines.get(active, []) else None,
            },
            "candles": candle_series,
            "latest_signals": latest_signals,
            "explainability": [e.__dict__ for e in self.explain_logs[-150:]],
            "portfolio": self.portfolio_state(),
            "metrics": self.performance_metrics(),
            "equity_curve": equity_curve,
            "asset_performance": asset_perf,
        }


def _f(x) -> float | None:
    try:
        if x is None:
            return None
        v = float(x)
        return v if np.isfinite(v) else None
    except Exception:
        return None

