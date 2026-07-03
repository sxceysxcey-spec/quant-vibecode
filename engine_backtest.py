"""Backtesting and validation engine for the Macro Quant War Room.

This module computes performance benchmarks, risk-adjusted statistics, and
comparative metrics versus SPY and QQQ baselines.
"""

import pandas as pd
import numpy as np

# =====================================================================
# FILE 4: PORTFOLIO BACKTESTING ENGINE
# Role: Simulates dynamic capital switching based on the state scores.
# =====================================================================


def calculate_annual_metrics(cum_series, periods_per_year=12):
    """Derive annualized performance metrics from a cumulative equity curve."""
    cumulative = cum_series.dropna()
    if cumulative.empty:
        return {
            'total_return_pct': np.nan,
            'cagr_pct': np.nan,
            'annualized_return_pct': np.nan,
            'annualized_vol_pct': np.nan,
            'sharpe_ratio': np.nan,
            'max_drawdown_pct': np.nan
        }

    returns = cumulative.pct_change().dropna()
    total_return = (cumulative.iloc[-1] / cumulative.iloc[0] - 1) * 100
    years = max(len(cumulative) / periods_per_year, 1)
    cagr = ((cumulative.iloc[-1] / cumulative.iloc[0]) ** (1 / years) - 1) * 100
    annualized_return = returns.mean() * periods_per_year * 100
    annualized_vol = returns.std() * np.sqrt(periods_per_year) * 100
    sharpe = annualized_return / annualized_vol if annualized_vol != 0 else np.nan
    drawdown = cumulative / cumulative.cummax() - 1
    max_drawdown = drawdown.min() * 100

    return {
        'total_return_pct': total_return,
        'cagr_pct': cagr,
        'annualized_return_pct': annualized_return,
        'annualized_vol_pct': annualized_vol,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_drawdown
    }


def execute_portfolio_backtest():
    """Run the portfolio backtest and produce validation metrics.

    This function compares the dynamic regime strategy to SPY and QQQ,
    and saves both detailed performance series and summary metrics files.
    """
    print("[*] Loading processed regime data for performance audit...")
    try:
        df = pd.read_csv("c:/Users/ceyxc/New folder/processed_regime_matrix.csv", index_col=0, parse_dates=True)
    except Exception as e:
        print(f"[ERROR] Could not read matrix file: {e}")
        return

    required_columns = ["SPY", "QQQ", "IBB", "Regime_State_Score"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"[ERROR] Missing required columns: {missing}")
        return

    df["SPY_Returns"] = df["SPY"].pct_change()
    df["QQQ_Returns"] = df["QQQ"].pct_change()
    df["IBB_Returns"] = df["IBB"].pct_change()

    df["Signal"] = df["Regime_State_Score"].shift(1)

    strategy_returns = []
    for _, row in df.iterrows():
        sig = row["Signal"]
        if pd.isna(sig):
            strategy_returns.append(0.0)
        elif sig > 0.3:
            strategy_returns.append(row["QQQ_Returns"])
        elif sig < -0.3:
            strategy_returns.append(row["IBB_Returns"])
        else:
            strategy_returns.append(row["SPY_Returns"])

    df["Strategy_Returns"] = strategy_returns
    df["SPY_Cum"] = (1 + df["SPY_Returns"].fillna(0)).cumprod()
    df["QQQ_Cum"] = (1 + df["QQQ_Returns"].fillna(0)).cumprod()
    df["Strategy_Cum"] = (1 + df["Strategy_Returns"].fillna(0)).cumprod()

    df["SPY_Drawdown"] = df["SPY_Cum"] / df["SPY_Cum"].cummax() - 1
    df["QQQ_Drawdown"] = df["QQQ_Cum"] / df["QQQ_Cum"].cummax() - 1
    df["Strategy_Drawdown"] = df["Strategy_Cum"] / df["Strategy_Cum"].cummax() - 1

    spy_metrics = calculate_annual_metrics(df["SPY_Cum"])
    qqq_metrics = calculate_annual_metrics(df["QQQ_Cum"])
    strat_metrics = calculate_annual_metrics(df["Strategy_Cum"])

    summary = {
        'strategy_total_return_pct': strat_metrics['total_return_pct'],
        'strategy_cagr_pct': strat_metrics['cagr_pct'],
        'strategy_sharpe_ratio': strat_metrics['sharpe_ratio'],
        'strategy_max_drawdown_pct': strat_metrics['max_drawdown_pct'],
        'spy_total_return_pct': spy_metrics['total_return_pct'],
        'spy_cagr_pct': spy_metrics['cagr_pct'],
        'spy_sharpe_ratio': spy_metrics['sharpe_ratio'],
        'spy_max_drawdown_pct': spy_metrics['max_drawdown_pct'],
        'qqq_total_return_pct': qqq_metrics['total_return_pct'],
        'qqq_cagr_pct': qqq_metrics['cagr_pct'],
        'qqq_sharpe_ratio': qqq_metrics['sharpe_ratio'],
        'qqq_max_drawdown_pct': qqq_metrics['max_drawdown_pct'],
        'alpha_vs_spy_pct': strat_metrics['total_return_pct'] - spy_metrics['total_return_pct'],
        'alpha_vs_qqq_pct': strat_metrics['total_return_pct'] - qqq_metrics['total_return_pct']
    }

    print("\n" + "=" * 72)
    print("         QUANT WAR ROOM STRATEGY AUDIT PERFORMANCE         ")
    print("=" * 72)
    print(f"Strategy total return: {summary['strategy_total_return_pct']:.2f}%")
    print(f"Strategy CAGR: {summary['strategy_cagr_pct']:.2f}%")
    print(f"Strategy Sharpe ratio: {summary['strategy_sharpe_ratio']:.2f}")
    print(f"Strategy max drawdown: {summary['strategy_max_drawdown_pct']:.2f}%")
    print("---")
    print(f"SPY total return: {summary['spy_total_return_pct']:.2f}%")
    print(f"SPY CAGR: {summary['spy_cagr_pct']:.2f}%")
    print(f"SPY Sharpe ratio: {summary['spy_sharpe_ratio']:.2f}")
    print(f"SPY max drawdown: {summary['spy_max_drawdown_pct']:.2f}%")
    print("---")
    print(f"QQQ total return: {summary['qqq_total_return_pct']:.2f}%")
    print(f"QQQ CAGR: {summary['qqq_cagr_pct']:.2f}%")
    print(f"QQQ Sharpe ratio: {summary['qqq_sharpe_ratio']:.2f}")
    print(f"QQQ max drawdown: {summary['qqq_max_drawdown_pct']:.2f}%")
    print("---")
    print(f"Alpha vs SPY: {summary['alpha_vs_spy_pct']:+.2f}%")
    print(f"Alpha vs QQQ: {summary['alpha_vs_qqq_pct']:+.2f}%")
    print("=" * 72)

    df.to_csv("c:/Users/ceyxc/New folder/backtest_performance_results.csv")
    pd.DataFrame([summary]).to_csv("c:/Users/ceyxc/New folder/backtest_summary_metrics.csv", index=False)
    print("[SUCCESS] Results written to 'backtest_performance_results.csv' and 'backtest_summary_metrics.csv'")


if __name__ == "__main__":
    execute_portfolio_backtest()
