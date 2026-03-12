"""Full cloud AI validation script: data generation, training, API inference."""

import os
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cloud_ai.cloud_api import ModelRegistry, app
from cloud_ai.data_generation import generate_synthetic_cloud_history
from cloud_ai.failure_model import train_failure_model
from cloud_ai.rul_model import train_rul_model


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, "cloud_health_history.csv")
        rul_model_path = os.path.join(tmpdir, "rul_model.pkl")
        failure_model_path = os.path.join(tmpdir, "failure_model.pkl")

        df = generate_synthetic_cloud_history(output_path=data_path, rows=600, seed=7)
        print(f"[1/4] Generated synthetic training data rows={len(df)} at {data_path}")

        train_rul_model(data_path=data_path, model_path=rul_model_path)
        train_failure_model(data_path=data_path, model_path=failure_model_path)
        print("[2/4] Trained both cloud models")

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            ModelRegistry.rul_model = None
            ModelRegistry.failure_model = None

            with TestClient(app) as client:
                health = client.get("/health")
                if health.status_code != 200:
                    raise RuntimeError(f"Health check failed: {health.status_code} {health.text}")
                print(f"[3/4] Health check passed: {health.json()}")

                payload = {
                    "vehicle_id": "VIT_CAR_001",
                    "timestamp_ms": 1707051123456,
                    "thermal_brake_margin": -0.21,
                    "thermal_engine_margin": 0.34,
                    "thermal_stress_index": 0.82,
                    "mechanical_vibration_anomaly_score": 0.77,
                    "mechanical_dominant_fault_band_hz": 142,
                    "mechanical_vibration_rms": 0.84,
                    "electrical_charging_efficiency_score": 0.81,
                    "electrical_battery_health_pct": 87,
                    "engine_rul_pct": 62,
                    "brake_rul_pct": 28,
                    "battery_rul_pct": 74,
                    "vehicle_health_score": 0.64,
                }
                resp = client.post("/analyze", json=payload)
                if resp.status_code != 200:
                    raise RuntimeError(f"Analyze failed: {resp.status_code} {resp.text}")

                body = resp.json()
                required = {
                    "vehicle_id",
                    "timestamp_ms",
                    "engine_rul_pct",
                    "brake_rul_pct",
                    "battery_rul_pct",
                    "fault_failure_probability_7d",
                    "fault_primary",
                    "fault_contributing_factors",
                    "recommendation",
                }
                if not required.issubset(set(body.keys())):
                    missing = required - set(body.keys())
                    raise RuntimeError(f"Missing output keys: {sorted(missing)}")
                print(f"[4/4] Analyze endpoint passed. Output: {body}")
        finally:
            os.chdir(old_cwd)


if __name__ == "__main__":
    main()
