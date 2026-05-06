# Hedge Fund Risk Modeling & Semi-Automated Trading System

## Team Information
- **Team Name**: [Team Name]
- **Year**: [Year]
- **All-Female Team**: [Yes/No]

## Architecture Overview

#### Describe your approach here. Keep it short and clear.

Our system is a modular multi-asset trading intelligence platform that processes market, macroeconomic, and sentiment datasets through a unified ingestion and preprocessing pipeline before running a candle-by-candle simulation. The data is validated, cleaned, normalized, and aligned on a shared timeline to support stable multi-asset processing while handling missing values and outliers gracefully. The platform computes indicators such as ATR, RSI, RSI-SMA, EMA200, and SSMA9 for volatility tracking, momentum detection, trend analysis, and execution confirmation. The trading engine generates explainable BUY, SELL, and HOLD signals using momentum crossovers, volatility conditions, trend alignment, and sentiment influence, while the portfolio engine applies risk-aware position sizing, exposure limits, slippage, and transaction costs before execution. Throughout the simulation, the system continuously tracks portfolio value, Sharpe Ratio, drawdown, volatility, Alpha, Beta, and Value at Risk while storing replay-ready snapshots for every candle. The dashboard acts as an institutional-style analytics terminal where users can replay the market candle-by-candle, monitor portfolio exposure, inspect signal evolution, and understand every trading decision through live explainability logs and real-time performance metrics.

# Overall System Flow

1. **Data Ingestion Layer**
   Loads and validates market, macroeconomic, and sentiment datasets from CSV files.

2. **Preprocessing Layer**
   Cleans missing values, malformed records, and outliers while aligning all datasets into a shared timeline.

3. **Feature Engineering Layer**
   Computes ATR, RSI, RSI-SMA, EMA200, and SSMA9 indicators for all assets.

4. **Signal Generation Layer**
   Generates BUY, SELL, and HOLD signals using momentum, volatility, trend, and sentiment conditions.

5. **Risk Management Layer**
   Applies ATR-based sizing, stop-loss calculations, exposure limits, and portfolio constraints.

6. **Execution Simulation Layer**
   Simulates slippage, transaction costs, and realistic trade execution while updating portfolio state.

7. **Portfolio & Metrics Layer**
   Tracks portfolio value, PnL, Sharpe Ratio, drawdown, VaR, Alpha, Beta, and volatility throughout the simulation.

8. **Replay & Visualization Layer**
   Displays candle-by-candle replay, explainability logs, portfolio analytics, and live performance metrics through an institutional-style dashboard.

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
