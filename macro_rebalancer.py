"""Rebalancer and execution slip generator for the Macro Quant War Room.

This module converts regime-driven sector signals into estimated order tickets
with transaction cost and slippage assumptions.
"""

import pandas as pd
import numpy as np
import os

# =====================================================================
# FILE 6: MACRO REBALANCER & AUTOMATED ORDER GENERATOR
# Role: Computes share execution values and generates trade tickets.
# =====================================================================

def generate_execution_order_slips(portfolio_value=100000.0, min_z_threshold=0.0, max_weight=0.2, method='positive', temperature=1.0):
    """Generate execution slips driven by sector Z-scores.

    Parameters:
    - portfolio_value: total portfolio USD
    - min_z_threshold: ignore sectors with Z below this (applied before softmax)
    - max_weight: maximum weight per sector (fraction)
    - method: 'positive' (positive-clamp) or 'softmax'
    - temperature: softmax temperature (higher -> flatter)
    """
    print("[*] Generating systematic trade allocation slips...")
    
    risk_file = r"c:\Users\ceyxc\New folder\portfolio_risk_metrics.csv"
    output_slip = r"c:\Users\ceyxc\New folder\execution_order_slip.csv"
    
    if not os.path.exists(risk_file):
        raise FileNotFoundError("Missing portfolio matrix source files. Cannot rebalance portfolio assets.")

    # Prefer the processed regime matrix (contains sector Z-scores)
    regime_file = r"c:\Users\ceyxc\New folder\processed_regime_matrix.csv"
    if not os.path.exists(regime_file):
        raise FileNotFoundError("Missing processed regime matrix. Run the regime engine first.")

    df = pd.read_csv(risk_file, index_col=0, parse_dates=True)
    latest_state = df.iloc[-1]

    reg = pd.read_csv(regime_file, index_col=0, parse_dates=True)
    # Sector tickers used in the frontend and pipeline
    sectors = ["XLK","XLY","XLP","XLE","XLF","XLI","XLV","XLB","XLU","XLC","XLRE"]

    # Build Z-score column names
    zcols = [f"{s}_Z" for s in sectors]

    if not all(c in reg.columns for c in zcols):
        # fallback: use two primary assets
        assets = ["QQQ","IBB"]
        order_records = []
        for asset in assets:
            target_weight = latest_state.get(f"{asset}_Weight", 0.5)
            target_allocation_value = portfolio_value * target_weight
            current_unit_price = latest_state.get(asset, 1.0)
            target_shares = int(np.floor(target_allocation_value / current_unit_price))
            order_records.append({
                "Ticker": asset,
                "Action": "BUY_MARKET" if target_shares > 0 else "HOLD",
                "Target_Weight": f"{target_weight * 100:.2f}%",
                "Order_Volume_Shares": target_shares,
                "Estimated_Execution_Price": f"${current_unit_price:.2f}"
            })
        order_slip_df = pd.DataFrame(order_records)
        order_slip_df.to_csv(output_slip, index=False)
        print(f"[SUCCESS] Fallback Execution Slip generated at: '{output_slip}'")
        return order_slip_df

    latest_z = reg[zcols].iloc[-1].copy()

    # Apply minimum threshold
    if min_z_threshold is not None and min_z_threshold > 0:
        latest_z = latest_z.where(latest_z >= min_z_threshold, other=0.0)

    if method == 'softmax':
        # softmax over z (use temperature)
        z_vals = latest_z.values.astype(float)
        # subtract max for numerical stability
        z_adj = (z_vals / float(temperature)) - (np.nanmax(z_vals / float(temperature)))
        exp = np.exp(z_adj)
        exp = np.where(np.isfinite(exp), exp, 0.0)
        scores = pd.Series(exp, index=latest_z.index)
    else:
        # positive-clamp method
        pos = latest_z.clip(lower=0.0)
        if pos.sum() <= 0:
            scores = latest_z.abs()
        else:
            scores = pos

    if scores.sum() <= 0:
        # fallback uniform weights
        weights = pd.Series(1.0 / len(scores), index=scores.index)
    else:
        weights = scores / scores.sum()

    # enforce max per-asset cap
    if max_weight is not None and max_weight > 0:
        weights = weights.clip(upper=max_weight)
        # renormalize after clipping
        if weights.sum() > 0:
            weights = weights / weights.sum()

    # Build order records for each sector
    order_records = []
    for s, w in weights.items():
        ticker = s.replace("_Z", "")
        # Fetch latest price from reg matrix
        if ticker in reg.columns:
            price = reg[ticker].iloc[-1]
        else:
            price = latest_state.get(ticker, 1.0)

        target_alloc_value = portfolio_value * w
        shares = int(np.floor(target_alloc_value / price)) if price > 0 else 0

        # Transaction cost & slippage model (simple, configurable)
        # Default assumptions (can be tuned via function args later):
        fixed_fee = 1.0                         # USD per order
        commission_per_share = 0.0             # USD per share
        commission_bps = 0.0005                # proportion of notional (0.05%)
        base_slippage_pct = 0.001              # 0.1% base slippage
        slippage_scale = 0.5                    # scales with order size relative to portfolio

        order_value = shares * price
        # slippage increases with relative order size (simple heuristic)
        rel_size = (order_value / float(max(portfolio_value, 1.0))) if portfolio_value > 0 else 0.0
        slippage_pct = base_slippage_pct + slippage_scale * rel_size
        slippage_pct = float(max(slippage_pct, 0.0))

        slippage_usd = shares * price * slippage_pct
        commission_usd = shares * commission_per_share + order_value * commission_bps
        total_tx_cost = fixed_fee + slippage_usd + commission_usd

        est_exec_price_adjusted = price * (1.0 + slippage_pct)
        est_cash_needed = shares * est_exec_price_adjusted + total_tx_cost

        order_records.append({
            "Ticker": ticker,
            "Action": "BUY_MARKET" if shares > 0 else "HOLD",
            "Target_Weight": f"{w * 100:.2f}%",
            "Order_Volume_Shares": shares,
            "Estimated_Execution_Price": f"${price:.2f}",
            "Estimated_Execution_Price_Adjusted": f"${est_exec_price_adjusted:.4f}",
            "Estimated_Slippage_USD": f"${slippage_usd:.2f}",
            "Commission_USD": f"${commission_usd:.2f}",
            "Fixed_Fee_USD": f"${fixed_fee:.2f}",
            "Total_Transaction_Cost_USD": f"${total_tx_cost:.2f}",
            "Estimated_Cash_Needed": f"${est_cash_needed:.2f}"
        })

    order_slip_df = pd.DataFrame(order_records)
    order_slip_df.to_csv(output_slip, index=False)
    print(f"[SUCCESS] Sector-driven Execution Order Slip generated at: '{output_slip}'")
    return order_slip_df

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate execution order slips from sector signals')
    parser.add_argument('--portfolio', type=float, default=100000.0)
    parser.add_argument('--min-z', type=float, default=0.0)
    parser.add_argument('--max-weight', type=float, default=0.2)
    parser.add_argument('--method', type=str, default='positive', choices=['positive','softmax'])
    parser.add_argument('--temperature', type=float, default=1.0)
    args = parser.parse_args()
    generate_execution_order_slips(portfolio_value=args.portfolio, min_z_threshold=args.min_z, max_weight=args.max_weight, method=args.method, temperature=args.temperature)
