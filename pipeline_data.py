"""Data ingestion pipeline for the Macro Quant War Room.

This module downloads macroeconomic indicators and asset prices, then constructs
inter-market ratio signals used by the regime detection engine.
"""

import os
import pandas as pd
import yfinance as yf
import requests


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='backslashreplace').decode('ascii'))
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)

# =====================================================================
# FILE 1: THE DATA INGESTION PIPELINE (AUTHENTICATED)
# Role: Connects to internet using your verified API key, saves to CSV.
# =====================================================================

# Hardcoded authenticated credential string
FRED_API_KEY = "82188cf054f50b743ec2385a6bf81be8"

def download_macro_indicators():
    """Pulls raw monthly economic metrics directly from the St. Louis Fed API."""
    print("[1/3] Contacting FRED API with verified credentials...")
    
    # Core FRED metrics plus optional alt-data placeholders
    metrics = {
        "M2": "M2SL",
        "Yield_Curve": "T10Y2Y",
        "Fed_Rates": "FEDFUNDS",
        "Corporate_BAA": "BAA",
        # Optional/experimental series (placeholders - may require correct series ids)
        "Baltic_Dry": "BALTICDRY",   # placeholder series id; may be unavailable
        "Cass_Freight": "CASSFREIGHT" # placeholder series id; may be unavailable
    }
    macro_df = pd.DataFrame()
    
    for name, series_id in metrics.items():
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
        try:
            res = requests.get(url).json()
            
            # Error checking loop
            if "error_message" in res:
                print(f"[!] FRED API Error for {name}: {res['error_message']}")
                continue
                
            df = pd.DataFrame(res["observations"])
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            
            # Align everything cleanly month-by-month
            df = df.set_index("date").resample("MS").last().ffill()
            macro_df[name] = df["value"]
            print(f"  └─ Success: Retrieved authentic data stream for [{name}]")
        except Exception as e:
            safe_print(f"[!] Connection failed for {name}: {e}")
            
    return macro_df

def download_asset_prices():
    """Pulls historical closing prices from Yahoo Finance."""
    print("[2/3] Contacting Yahoo Finance API for Asset Pricing...")
    assets = {
        "SPY": "SPY", "QQQ": "QQQ", "IBB": "IBB",
        # 11 Select Sector SPDR ETFs (plus communications and real estate)
        "XLK": "XLK", "XLF": "XLF", "XLE": "XLE",
        "XLY": "XLY", "XLP": "XLP", "XLI": "XLI",
        "XLV": "XLV", "XLB": "XLB", "XLU": "XLU",
        "XLC": "XLC", "XLRE": "XLRE"
    }
    asset_df = pd.DataFrame()
    
    for name, ticker in assets.items():
        try:
            df = yf.Ticker(ticker).history(period="10y", interval="1mo")
            df.index = df.index.tz_localize(None).to_period("M").to_timestamp()
            asset_df[name] = df["Close"].resample("MS").last().ffill()
            print(f"  └─ Success: Retrieved market pricing for [{name}]")
        except Exception as e:
            safe_print(f"[!] Failed to pull {name} from Yahoo Finance: {e}")
            
    return asset_df

def execute_pipeline():
    macro = download_macro_indicators()
    assets = download_asset_prices()
    
    # --- Calculate leading inter-market ratios (institutional gauges)
    try:
        # Risk-On Vector: XLK / XLP
        if "XLK" in assets.columns and "XLP" in assets.columns:
            macro["RiskOn_XLK_XLP"] = (assets["XLK"] / assets["XLP"]).resample("MS").last().ffill()

        # Economic Expansion Vector: XLI / XLU
        if "XLI" in assets.columns and "XLU" in assets.columns:
            macro["EconExp_XLI_XLU"] = (assets["XLI"] / assets["XLU"]).resample("MS").last().ffill()

        # Inflation Hedging Vector: XLB / XLP
        if "XLB" in assets.columns and "XLP" in assets.columns:
            macro["Inflation_XLB_XLP"] = (assets["XLB"] / assets["XLP"]).resample("MS").last().ffill()

        # Copper-to-Gold ratio via Yahoo tickers
        try:
            for t in ["HG=F", "GC=F"]:
                if t not in assets.columns:
                    df = yf.Ticker(t).history(period="10y", interval="1mo")
                    df.index = df.index.tz_localize(None).to_period("M").to_timestamp()
                    assets[t] = df["Close"].resample("MS").last().ffill()
            if "HG=F" in assets.columns and "GC=F" in assets.columns:
                macro["Copper_Gold"] = (assets["HG=F"] / assets["GC=F"]).resample("MS").last().ffill()
        except Exception:
            pass
    except Exception as e:
        safe_print(f"[!] Failed to compute inter-market ratios: {e}")

    # Merge both datasets using their dates
    master_panel = pd.concat([macro, assets], axis=1).dropna()
    
    # Sort chronologically ascending for standard model calculations
    master_panel = master_panel.sort_index(ascending=True)
    
    # Save it down as a CSV file in the same folder
    output_filename = r"c:\Users\ceyxc\New folder\raw_macro_panel.csv"
    master_panel.to_csv(output_filename)
    print(f"[3/3] Success! Combined historical spreadsheet saved as: '{output_filename}'")

if __name__ == "__main__":
    execute_pipeline()
