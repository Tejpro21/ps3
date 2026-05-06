## Hedge Fund Risk Modeling System (Local) — Architecture

### High-level flow
- **Datasets**: loaded from `datasets/` (fallback: project root) on backend startup.
- **Normalization**: backend normalizes both the required schemas and provided hackathon schemas into canonical market/macro frames.
- **Feature layer**: backend computes ATR/RSI/EMA/SSMA once per asset.
- **Replay + simulation**:
  - Candle-by-candle stepping (play/pause/prev/next/speed)
  - Portfolio engine tracks cash, positions, PnL, exposure, allocation, equity curve
  - Risk engine sizes positions using ATR stops + 1:3 RR
  - Signal engine emits BUY/SELL/HOLD and explainability logs
  - Slippage model applied on execution (volatility-aware bps)
  - Periodic rebalance trims concentration drift
- **API**: FastAPI serves dashboard snapshots + SSE stream (snapshots), plus upload/reload.
- **Frontend**: React terminal UI only **renders backend outputs** (no indicators/metrics computed client-side).

### Backend modules
- `services/data_registry.py`: dataset discovery + per-ticker frames
- `utils/csv_normalize.py`: schema normalization (required + hackathon formats)
- `utils/preprocessing.py`: missing value handling + outlier smoothing
- `metrics/indicators.py`: ATR(14), RSI(14), RSI-SMA(9), EMA200, SSMA9
- `simulation/signal_engine.py`: rule-based signals + regime detection
- `simulation/risk_engine.py`: ATR sizing + RR + volatility-aware sizing
- `simulation/portfolio.py`: state, trades, slippage execution, equity curve
- `simulation/replay_manager.py`: per-ticker replay cursor + multi-asset sync at timestamp

### Frontend modules
- `src/pages/DashboardPage.tsx`: orchestrates snapshot polling + SSE sync + layout
- `src/charts/*`: replay chart + multi-asset performance chart
- `src/services/api.ts`: single source of truth for backend communication (supports `VITE_API_BASE`)

