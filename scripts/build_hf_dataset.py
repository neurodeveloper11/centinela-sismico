"""
build_hf_dataset.py - Global Seismic Dataset Generator for Hugging Face Datasets.
Curates, standardizes, and exports global earthquake catalogs to Apache Parquet format.
Author: Fabio Ignacio Torres Benítez
"""

import os
import sys
import math
import time
import requests
import pandas as pd

# Fix Windows console unicode issues
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from quakemind_engine import calculate_attenuation_mmi

DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)


def calculate_seismic_energy_joules(magnitude: float) -> float:
    """Calculates Gutenberg-Richter radiated seismic energy: log10(E) = 4.8 + 1.5 * M."""
    return 10 ** (4.8 + 1.5 * magnitude)


def fetch_significant_and_major_quakes() -> pd.DataFrame:
    """
    Fetches significant monthly quakes and M4.5+ daily global events from USGS,
    standardizing them into an analytical schema.
    """
    urls = [
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson"
    ]

    records = []
    seen_ids = set()

    for url in urls:
        try:
            r = requests.get(url, timeout=12, headers={"User-Agent": "QuakeMind-Global/1.0"})
            if r.status_code == 200:
                data = r.json()
                for feat in data.get("features", []):
                    qid = feat.get("id")
                    if qid in seen_ids:
                        continue
                    seen_ids.add(qid)

                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])

                    mag = props.get("mag")
                    if mag is None:
                        continue

                    mag = float(mag)
                    depth = float(coords[2])
                    lat = float(coords[1])
                    lon = float(coords[0])

                    # Depth classification
                    if depth <= 70.0:
                        depth_class = "Shallow (0-70 km)"
                    elif depth <= 300.0:
                        depth_class = "Intermediate (70-300 km)"
                    else:
                        depth_class = "Deep (>300 km)"

                    energy_j = calculate_seismic_energy_joules(mag)

                    records.append({
                        "event_id": qid,
                        "title": props.get("title", ""),
                        "place": props.get("place", ""),
                        "magnitude": round(mag, 2),
                        "magnitude_type": props.get("magType", "Mw"),
                        "depth_km": round(depth, 1),
                        "depth_category": depth_class,
                        "latitude": lat,
                        "longitude": lon,
                        "time_epoch_ms": props.get("time", 0),
                        "time_iso_utc": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(props.get("time", 0) / 1000.0)),
                        "seismic_energy_joules": energy_j,
                        "usgs_alert_level": props.get("alert") or "green",
                        "felt_reports_count": props.get("felt") or 0,
                        "usgs_mmi": props.get("mmi") or calculate_attenuation_mmi(mag, max(depth, 5.0)),
                        "tsunami_alert": bool(props.get("tsunami", 0)),
                        "event_url": props.get("url", "")
                    })
        except Exception as e:
            print(f"Warning fetching {url}: {e}")

    df = pd.DataFrame(records)
    return df


def main():
    print("[QuakeMind] Ingesting and curating global seismic dataset...")
    df = fetch_significant_and_major_quakes()

    if df.empty:
        print("[QuakeMind] Warning: No live records fetched, skipping save.")
        return

    parquet_path = os.path.join(DATASET_DIR, "global_seismic_risk_catalog.parquet")
    csv_path = os.path.join(DATASET_DIR, "global_seismic_risk_catalog.csv")

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"[QuakeMind] Successfully compiled {len(df)} global seismic events.")
    print(f"[QuakeMind] Saved Parquet: {parquet_path}")
    print(f"[QuakeMind] Saved CSV: {csv_path}")


if __name__ == "__main__":
    main()
