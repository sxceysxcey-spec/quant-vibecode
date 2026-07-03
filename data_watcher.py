"""Watchdog service for the Macro Quant War Room data pipeline.

This module monitors the raw data file and triggers the ingestion and regime
engine when new data becomes available.
"""

import time
import os
import subprocess
import sys
import logging
from pathlib import Path


ROOT = Path(__file__).parent
RAW_PATH = ROOT / "raw_macro_panel.csv"
PIPELINE_SCRIPT = ROOT / "pipeline_data.py"
ENGINE_SCRIPT = ROOT / "engine_regime.py"
PROCESSED_PATH = ROOT / "processed_regime_matrix.csv"

WATCH_INTERVAL = int(os.environ.get("DATA_WATCH_INTERVAL", 60))
LOG_FILE = ROOT / "data_watcher.log"

# configure logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


def run_script(script_path):
    """Execute a script using the current Python interpreter and log the result."""
    logging.info(f"Running: {script_path}")
    try:
        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=60*15)
        if res.stdout:
            logging.info(res.stdout)
        if res.returncode != 0:
            logging.warning(f"Script {script_path} exited with {res.returncode}")
            if res.stderr:
                logging.warning(res.stderr)
        else:
            logging.info(f"Script {script_path} completed successfully")
    except subprocess.TimeoutExpired as te:
        logging.error(f"Script {script_path} timed out: {te}")
    except Exception as e:
        logging.exception(f"Failed to run {script_path}: {e}")


def get_mtime(p: Path):
    try:
        return p.stat().st_mtime
    except Exception:
        return 0


def main():
    logging.info("Starting data_watcher - polling for raw data changes")
    last_raw_mtime = get_mtime(RAW_PATH)

    # Force an initial pipeline+engine run if processed file missing
    if not PROCESSED_PATH.exists():
        print("Processed file missing - running full pipeline and engine")
        run_script(PIPELINE_SCRIPT)
        run_script(ENGINE_SCRIPT)
        last_raw_mtime = get_mtime(RAW_PATH)

    try:
        while True:
            time.sleep(WATCH_INTERVAL)
            try:
                current_raw_mtime = get_mtime(RAW_PATH)
                if current_raw_mtime > last_raw_mtime:
                    logging.info("Detected change in raw data - running pipeline and engine")
                    run_script(PIPELINE_SCRIPT)
                    run_script(ENGINE_SCRIPT)
                    last_raw_mtime = current_raw_mtime
                else:
                    # idle
                    logging.debug("No change detected in raw data")
            except Exception:
                logging.exception("Error during watch loop")
    except KeyboardInterrupt:
        logging.info("data_watcher stopped by user")


if __name__ == "__main__":
    main()
