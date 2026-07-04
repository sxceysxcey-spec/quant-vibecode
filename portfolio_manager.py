"""Risk management engine for the Macro Quant War Room.

This module computes drawdowns and dynamic allocation weights from the
backtest results and regime state signals.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent

# =====================================================================
# FILE 5: DYNAMIC RISK MANAGEMENT ENGINE
# Role: Computes risk metrics and dynamic weighting curves.
# =====================================================================

def calculate_risk_metrics():
    """Calculate risk statistics and dynamic exposure weights.

    The output is intended to feed the dashboard and automated rebalance logic.
    """
    print("[*] Running portfolio optimization layer...")
    try:
        df = pd.read_csv(ROOT / "backtest_performance_results.csv", index_col=0, parse_dates=True)
    except Exception as e:
        print(f"[ERROR] Portfolio manager cannot find backtest sheets: {e}")
        return

    # 1. Calculate Maximum Drawdown Metrics
    for prefix in ["SPY", "Strategy"]:
        cum_col = f"{prefix}_Cum"
        peak_col = f"{prefix}_Peak"
        dd_col = f"{prefix}_DD"
        
        df[peak_col] = df[cum_col].cummax()
        df[dd_col] = (df[cum_col] - df[peak_col]) / df[peak_col] * 100

    # 2. Compute Dynamic Scaling Allocation Weights Based on Active Scores
    # Smooth transition sizing instead of all-or-nothing switching
    df["QQQ_Weight"] = np.where(df["Regime_State_Score"] > 0, (df["Regime_State_Score"] / 2).clip(0, 1), 0)
    df["IBB_Weight"] = np.where(df["Regime_State_Score"] < 0, (abs(df["Regime_State_Score"]) / 2).clip(0, 1), 0)
    df["Cash_Weight"] = 1.0 - (df["QQQ_Weight"] + df["IBB_Weight"])

    df.to_csv(ROOT / "portfolio_risk_metrics.csv")
    print("[SUCCESS] Risk evaluation metrics written to 'portfolio_risk_metrics.csv'")

if __name__ == "__main__":
    calculate_risk_metrics()
