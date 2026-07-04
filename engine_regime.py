"""Regime detection engine for the Macro Quant War Room.

This module standardizes macro inputs and computes a composite regime score
based on liquidity, yield curve, and interest rate dynamics.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).parent

# Map the FRED Series IDs to the column names used in pipeline_data.py
# pipeline_data.py uses keys: "M2", "Yield_Curve", "Fed_Rates"
COLUMN_MAPPING = {
    "M2": "M2",
    "Yield_Curve": "Yield_Curve",
    "Fed_Rates": "Fed_Rates"
}


def compute_regime_score(df):
    """Compute normalized regime state signals from macroeconomic inputs.

    The regime score is built from rolling z-score transformations of the core
    macro variables, with weights chosen to reflect liquidity, growth, and rate
    regime intuition.
    """
    # Safety check: Ensure expected columns exist
    missing_cols = [col for col in COLUMN_MAPPING.values() if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Critical Error: The following columns are missing from the CSV: {missing_cols}. "
                       f"Available columns: {df.columns.tolist()}")

    # 1. Normalize variables using Z-Scores
    for f_name, col_name in COLUMN_MAPPING.items():
        # Calculate rolling mean/std for a 5-year lookback (60 months) to smooth noise
        window = 60
        if len(df) > window:
            mean = df[col_name].rolling(window=window).mean().fillna(df[col_name].mean())
            std = df[col_name].rolling(window=window).std().fillna(df[col_name].std())
            # Avoid division by zero
            std = std.replace(0, 1e-9)
            df[f"{f_name}_Score"] = ((df[col_name] - mean) / std).clip(-2, 2)
        else:
            # Fallback if not enough data
            mean = df[col_name].mean()
            std = df[col_name].std()
            std = std.replace(0, 1e-9)
            df[f"{f_name}_Score"] = ((df[col_name] - mean) / std).clip(-2, 2)

    # 2. Formulate the Composite State Score
    # Weights: 40% Liquidity, 30% Yield Curve, -30% Fed Rates (High rates = bad for score)
    df["Regime_State_Score"] = (
        (df["M2_Score"] * 0.4) + 
        (df["Yield_Curve_Score"] * 0.3) - 
        (df["Fed_Rates_Score"] * 0.3)
    )
    
    return df


def compute_sector_zscores(df, window=60):
    """Compute rolling Z-scores for sector ETFs and inter-market ratios.

    Adds columns like `XLK_Z`, `XLF_Z`, and also Z-scores for ratio columns
    such as `RiskOn_XLK_XLP` -> `RiskOn_XLK_XLP_Z`.
    """
    # Define canonical sector ETFs we expect from pipeline_data
    sector_tickers = ["XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"]
    ratio_cols = [c for c in df.columns if any(k in c for k in ["RiskOn_","EconExp_","Inflation_"]) ]

    # Compute Z-scores for sectors
    for t in sector_tickers:
        if t in df.columns:
            if len(df) > window:
                mean = df[t].rolling(window=window).mean().fillna(df[t].mean())
                std = df[t].rolling(window=window).std().fillna(df[t].std()).replace(0, 1e-9)
                df[f"{t}_Z"] = ((df[t] - mean) / std).clip(-3, 3)
            else:
                mean = df[t].mean()
                std = df[t].std() if df[t].std() != 0 else 1e-9
                df[f"{t}_Z"] = ((df[t] - mean) / std).clip(-3, 3)

            # Forward returns for sectors (3m and 6m)
            df[f"{t}_Fwd_3M"] = df[t].pct_change(3).shift(-3) * 100
            df[f"{t}_Fwd_6M"] = df[t].pct_change(6).shift(-6) * 100

    # Compute Z-scores for inter-market ratios
    for r in ratio_cols:
        if len(df) > window:
            mean = df[r].rolling(window=window).mean().fillna(df[r].mean())
            std = df[r].rolling(window=window).std().fillna(df[r].std()).replace(0, 1e-9)
            df[f"{r}_Z"] = ((df[r] - mean) / std).clip(-3, 3)
        else:
            mean = df[r].mean()
            std = df[r].std() if df[r].std() != 0 else 1e-9
            df[f"{r}_Z"] = ((df[r] - mean) / std).clip(-3, 3)

    return df


def run_regime_calculations():
    """Execute the full regime detection pipeline and persist the state matrix."""
    print("[*] Engine initialized. Loading 'raw_macro_panel.csv'...")
    
    file_path = ROOT / "raw_macro_panel.csv"
    
    try:
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        print(f"[*] Loaded data successfully. Shape: {df.shape}")
        print(f"[*] Found columns: {df.columns.tolist()}")
    except FileNotFoundError:
        print(f"[ERROR] File not found at: {file_path}")
        print("Please run 'pipeline_data.py' first.")
        return None
    except Exception as e:
        print(f"[ERROR] Could not read file: {e}")
        return None

    # Run the calculation
    try:
        df = compute_regime_score(df)
    except KeyError as e:
        print(f"[CRITICAL] Data Structure Mismatch: {e}")
        print("Please check that 'pipeline_data.py' saved the file with columns: M2, Yield_Curve, Fed_Rates")
        return None

    # Extend with sector z-scores and forward returns
    try:
        df = compute_sector_zscores(df)
    except Exception as e:
        print(f"[WARN] Sector Z-score computation failed: {e}")

    # Calculate Forward Returns
    for h in [3, 6]:
        for asset in ["SPY", "QQQ", "IBB"]:
            if asset in df.columns:
                df[f"{asset}_Fwd_{h}M"] = df[asset].pct_change(h).shift(-h) * 100

    # Save the processed matrix
    output_file = ROOT / "processed_regime_matrix.csv"
    df.to_csv(output_file)
    print(f"[SUCCESS] State Detection Complete. Matrix saved to: '{output_file}'")
    return df


if __name__ == "__main__":
    run_regime_calculations()
