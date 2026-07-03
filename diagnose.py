import requests
import pandas as pd
import os

FRED_KEY = "82188cf054f50b743ec2385a6bf81be8"

print("FRED API DIAGNOSTIC TEST")
print("="*50)

# Test 1: Direct API call
url = f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL&api_key={FRED_KEY}&file_type=json"
print(f"Testing: {url}")
try:
    r = requests.get(url, timeout=10)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if "error_message" in data:
            print(f"FRED ERROR: {data['error_message']}")
        else:
            observations = data.get("observations", [])
            print(f"FRED API WORKS! Got {len(observations)} data points")
            if observations:
                latest = observations[-1]
                print(f"   Latest M2: ${latest.get('value', 'N/A')}B")
            else:
                print("   No observation data returned.")
    else:
        print(f"HTTP ERROR: {r.text}")
except Exception as e:
    print(f"CONNECTION FAILED: {str(e)}")

# Test 2: Check file paths
print("\nFILE PATH CHECK")
paths = [
    r"c:\Users\ceyxc\New folder\pipeline_data.py",
    r"c:\Users\ceyxc\New folder\raw_macro_panel.csv",
    r"c:\Users\ceyxc\New folder\engine_regime.py"
]
for p in paths:
    exists = "YES" if os.path.exists(p) else "NO"
    print(f"{exists} {p}")
