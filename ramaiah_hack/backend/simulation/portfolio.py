from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from models.domain import Position, Trade


@dataclass
class Portfolio:
    initial_cash: float = 1_000_000.0
    cash: float = 1_000_000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    realized_pnl: float = 0.0
    trade_history: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)

    def reset(self) -> None:
        self.cash = float(self.initial_cash)
        self.positions.clear()
        self.realized_pnl = 0.0
        self.trade_history.clear()
        self.equity_curve.clear()
        self.timestamps.clear()

    def mark_to_market(self, ts: str, prices: Dict[str, float]) -> float:
        equity = self.cash
        for t, pos in self.positions.items():
            px = prices.get(t)
            if px is None or not np.isfinite(px):
                continue
            equity += pos.qty * px
        self.timestamps.append(ts)
        self.equity_curve.append(float(equity))
        return float(equity)

    def unrealized_pnl(self, prices: Dict[str, float]) -> float:
        pnl = 0.0
        for t, pos in self.positions.items():
            px = prices.get(t)
            if px is None or not np.isfinite(px):
                continue
            pnl += pos.qty * (px - pos.avg_price)
        return float(pnl)

    def exposure(self, prices: Dict[str, float]) -> float:
        exp = 0.0
        for t, pos in self.positions.items():
            px = prices.get(t)
            if px is None or not np.isfinite(px):
                continue
            exp += abs(pos.qty * px)
        return float(exp)

    def allocation(self, prices: Dict[str, float]) -> Dict[str, float]:
        equity = self.cash + sum(pos.qty * prices.get(t, 0.0) for t, pos in self.positions.items())
        if equity <= 0:
            return {t: 0.0 for t in self.positions}
        alloc = {}
        for t, pos in self.positions.items():
            px = prices.get(t, 0.0)
            alloc[t] = float((pos.qty * px) / equity)
        return alloc

    def buy(
        self,
        ts: str,
        ticker: str,
        qty: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        fee_bps: float = 1.0,
        slippage_bps: float = 0.0,
    ) -> Trade | None:
        if qty <= 0 or price <= 0:
            return None
        exec_price = float(price) * (1.0 + float(slippage_bps) / 10_000.0)
        notional = qty * exec_price
        fees = notional * (fee_bps / 10_000.0)
        total_cost = notional + fees
        if total_cost > self.cash:
            # insufficient capital safeguard
            return None
        self.cash -= total_cost

        if ticker in self.positions:
            pos = self.positions[ticker]
            new_qty = pos.qty + qty
            new_avg = (pos.avg_price * pos.qty + exec_price * qty) / new_qty
            pos.qty = float(new_qty)
            pos.avg_price = float(new_avg)
            pos.stop_loss = float(min(pos.stop_loss, stop_loss))
            pos.take_profit = float(max(pos.take_profit, take_profit))
        else:
            self.positions[ticker] = Position(
                ticker=ticker,
                qty=float(qty),
                avg_price=float(exec_price),
                stop_loss=float(stop_loss),
                take_profit=float(take_profit),
            )

        trade = Trade(
            timestamp=ts,
            ticker=ticker,
            side="BUY",
            qty=float(qty),
            price=float(exec_price),
            stop_loss=float(stop_loss),
            take_profit=float(take_profit),
            fees=float(fees),
        )
        self.trade_history.append(trade)
        return trade

    def sell(self, ts: str, ticker: str, price: float, fee_bps: float = 1.0, slippage_bps: float = 0.0) -> Trade | None:
        pos = self.positions.get(ticker)
        if pos is None or pos.qty <= 0 or price <= 0:
            return None
        qty = pos.qty
        return self.sell_qty(ts=ts, ticker=ticker, qty=qty, price=price, fee_bps=fee_bps, slippage_bps=slippage_bps)

    def sell_qty(self, ts: str, ticker: str, qty: float, price: float, fee_bps: float = 1.0, slippage_bps: float = 0.0) -> Trade | None:
        pos = self.positions.get(ticker)
        if pos is None or qty <= 0 or pos.qty <= 0 or price <= 0:
            return None
        qty = float(min(qty, pos.qty))
        exec_price = float(price) * (1.0 - float(slippage_bps) / 10_000.0)
        notional = qty * exec_price
        fees = notional * (fee_bps / 10_000.0)
        self.cash += notional - fees
        pnl = qty * (exec_price - pos.avg_price) - fees
        self.realized_pnl += float(pnl)

        trade = Trade(
            timestamp=ts,
            ticker=ticker,
            side="SELL",
            qty=float(qty),
            price=float(exec_price),
            stop_loss=float(pos.stop_loss),
            take_profit=float(pos.take_profit),
            pnl=float(pnl),
            fees=float(fees),
        )
        self.trade_history.append(trade)
        pos.qty = float(pos.qty - qty)
        if pos.qty <= 1e-9:
            del self.positions[ticker]
        return trade

    def check_stops(self, ts: str, prices: Dict[str, float]) -> List[Trade]:
        closed: List[Trade] = []
        for t in list(self.positions.keys()):
            pos = self.positions[t]
            px = prices.get(t)
            if px is None or not np.isfinite(px):
                continue
            if px <= pos.stop_loss or px >= pos.take_profit:
                tr = self.sell(ts=ts, ticker=t, price=float(px))
                if tr:
                    closed.append(tr)
        return closed

