# Macro Quant War Room

## Overview
A local macro quantitative system built to ingest financial data, detect structural regime states, backtest allocation strategies, optimize risk, and visualize results in both a Streamlit dashboard and a WebAssembly-powered browser UI.

## Architecture

1. **Data ingestion**
   - `pipeline_data.py` downloads raw macro, equity, and alternative data feeds.
   - Outputs feed into `processed_regime_matrix.csv` for downstream analytics.

2. **Regime detection**
   - `engine_regime.py` computes a structural regime score and sector Z-scores.
   - The regime signal drives tactical allocation and risk tilts.

## Math & regime detection

This system uses rolling statistics and standardized factor signals to infer structural market states.
- `engine_regime.py` applies rolling z-scores and volatility normalization over a multi-year window to create stable macro factor signals.
- The model is grounded in time-series statistics such as rolling means, rolling standard deviations, correlation structure, and volatility clustering.
- By standardizing inflation, liquidity, and rate data, the engine creates an interpretable regime state score rather than relying on one-off cross-sectional models.

## Macro factor intuition

The strategy reflects classic macro sector rotation principles:
- **Inflation** tends to favor commodity and materials exposures (e.g. `XLB`, `XLE`) while weighing on rate-sensitive defensive sectors.
- **Growth** and liquidity expansion usually benefit cyclicals and technology (`XLK`, `XLY`).
- **Rising rates** and tightening liquidity favor defensive and income-oriented assets, which is reflected in the model through negative regime state contributions from Fed rate strength.
- The sector scoring also embeds inter-market ratios like `XLI/XLU` and `XLK/XLP` to capture real economy versus defensive regime tilts.

## Methodology

### Regime detection
- Uses standardization and rolling statistics rather than black-box predictions.
- Each macro input is converted to a rolling z-score using a 60-month lookback window.
- This is equivalent to normalizing each series by its local mean and volatility, which helps detect volatility clustering and persistent regime shifts.
- The composite regime state score is a weighted factor model:
  - `40% M2 liquidity` captures broad monetary expansion/contraction.
  - `30% yield curve` captures growth expectations and recession risk.
  - `-30% Fed rates` captures monetary tightening, where higher rates reduce the state score.
- The engine therefore behaves like a simple factor model, blending macro regime signals with a risk-sensitive tilt.

### Sector rotation
- `engine_regime.py` also computes z-scores for sector ETFs and inter-market ratios, making each sector signal comparable on the same statistical scale.
- Relative strength is implied by higher z-scores, while mean reversion is controlled by clipping extreme values.
- Forward 3-month and 6-month returns are generated for review, supporting a regime-based transition view rather than a pure momentum or carry model.

### Backtest assumptions
- The backtest is monthly and uses end-of-month closing prices from Yahoo Finance.
- Portfolio decisions are based on a one-period lagged signal to reduce lookahead bias.
- Execution costs are treated as modeled slippage and order slips in `macro_rebalancer.py`, not as a full execution engine.
- The strategy is benchmarked to SPY and QQQ to show relative performance and risk-adjusted alpha.

## Data sources
- Macro data: FRED API via the St. Louis Fed (`M2SL`, `T10Y2Y`, `FEDFUNDS`, `BAA`) using `pipeline_data.py`.
- Equity / ETF prices: Yahoo Finance via `yfinance` for `SPY`, `QQQ`, `IBB`, and sector ETFs.
- Inter-market ratios: constructed internally from ETF pairs such as `XLK/XLP`, `XLI/XLU`, and `XLB/XLP`.
- Optional alt-data placeholders are present for freight and commodity ratios, but they are not required for core operation.

## System diagram

```text
Raw data collection
  ├─ FRED API (macro indicators)
  └─ Yahoo Finance (ETF prices)
          │
          ▼
   raw_macro_panel.csv
          │
          ▼
   engine_regime.py -> processed_regime_matrix.csv
          │
          ├─ engine_backtest.py -> backtest_performance_results.csv + backtest_summary_metrics.csv
          ├─ portfolio_manager.py -> portfolio_risk_metrics.csv
          ├─ macro_rebalancer.py -> execution_order_slip.csv
          └─ app_frontend.py / web UI
```

## Sample outputs
- `backtest_summary_metrics.csv` contains a single-row summary of total return, CAGR, Sharpe, max drawdown, and alpha versus SPY/QQQ.
- `backtest_performance_results.csv` contains monthly cumulative equity curves and drawdowns for the strategy and benchmarks.
- The Streamlit dashboard displays the computed `Regime_State_Score`, the detected structural regime, and cash buffer recommendations.

> Example summary snippet:
>
> `strategy_total_return_pct`, `strategy_cagr_pct`, `strategy_sharpe_ratio`, `strategy_max_drawdown_pct`, `alpha_vs_spy_pct`, `alpha_vs_qqq_pct`

## Limitations & assumptions
- Does not support intraday or tick-level execution; all signals are monthly.
- Does not execute live orders; `macro_rebalancer.py` generates execution slips only.
- Transaction-cost modeling is approximate and not a full market impact engine.
- No multi-user web deployment is included; Streamlit is single-user by default.
- The current system does not yet include a full factor model for value, momentum, or quality.

## Future roadmap
- Add formal factor models for value, momentum, and quality in addition to macro regime signals.
- Integrate live data feeds for real-time regime monitoring.
- Deploy the dashboard to cloud hosting for secure multi-user access.
- Expand the WASM visualization with animation, interactive filtering, and a richer sector heatmap.
- Add a dedicated testing suite with unit tests for pipeline ingestion, regime normalization, and backtest integrity.

## Testing framework
- A lightweight `pytest` setup is a strong next step.
- Suggested tests include:
  - validating FRED/Yahoo ingestion output shapes and required columns,
  - verifying rolling z-score normalization in `engine_regime.py`,
  - confirming backtest metrics are finite and monotonic where appropriate.
- Even a small `tests/test_engine_regime.py` file would demonstrate engineering discipline.

3. **Backtest & validation**
   - `engine_backtest.py` compares the dynamic strategy against SPY and QQQ baselines.
   - It calculates total return, CAGR, Sharpe ratio, and maximum drawdown.
   - Outputs are persisted to `backtest_performance_results.csv` and `backtest_summary_metrics.csv`.

4. **Risk optimization**
   - `portfolio_manager.py` generates target weights, risk metrics, and cash sizing.
   - Outputs are recorded in `portfolio_risk_metrics.csv`.

5. **Rebalancer**
   - `macro_rebalancer.py` creates orders and rebalancing recommendations based on regime state and risk signals.

6. **Visualization**
   - `app_frontend.py` provides the Streamlit war room dashboard with charts, metrics, and a DCF toolkit.
   - `web/index.html`, `web/index.js`, and `web/style.css` provide a static browser UI.
   - `cpp/wasm/sector_heatmap.cpp` compiles to WASM and exports a live heatmap engine.

## Current status

- Streamlit dashboard is functional with regime metrics, time-series charts, sector rotation visualization, valuation tools, and a new factor overlay panel.
- The pipeline now includes broader multi-asset coverage for bonds, commodities, FX, and alternative macro signals.
- WASM module is compiled and copied into `web/`, with the browser loader now wired for runtime module detection.
- Backtest engine now produces comparative validation metrics versus SPY and QQQ.
- Documentation and deployment guidance have been added.

## Dependencies

Install the Python runtime dependencies with:
```bash
pip install -r requirements.txt
```

## How to run

### Streamlit dashboard
```bash
streamlit run app_frontend.py
```

### Web frontend
Open `web/index.html` in a browser, or serve the folder with a local static server:
```bash
cd web
python -m http.server 8080
```

## Validation

The backtest engine now reports:
- total return
- compound annual growth rate (CAGR)
- annualized return
- annualized volatility
- Sharpe ratio
- maximum drawdown
- alpha versus SPY and QQQ

This gives a benchmarkable output for financial audiences and hiring managers.

## Assumptions & testing transparency

The backtest reflects the following baseline assumptions:
- **Rebalance frequency:** monthly, based on monthly state updates and asset price data.
- **Transaction costs:** modeled with slippage, fixed fees, and low commission assumptions in `macro_rebalancer.py`.
- **Data sources:** FRED for macro series, Yahoo Finance for asset prices, and internally generated inter-market ratios.
- **Lookahead control:** regime signals are shifted by one period before trade decisions to maintain a forward-looking simulation.
- **Risk controls:** position weights are capped and normalized to avoid over-concentration in any single sector.

These assumptions are explicitly documented so performance results can be interpreted realistically.

A Dockerfile has been added for containerized Streamlit execution:

```bash
docker build -t macro-war-room .
docker run --rm -p 8501:8501 macro-war-room
```

The static web frontend can be hosted separately on any static site service, while the Streamlit war room can run behind a reverse proxy or inside a container.

## Notes

- `web/index.js` now loads the compiled WASM module if available and falls back cleanly if it is not.
- `engine_backtest.py` now saves both the full performance series and a summary metrics file.
- `README.md` documents the system flow, validation story, and deployment path more clearly.
