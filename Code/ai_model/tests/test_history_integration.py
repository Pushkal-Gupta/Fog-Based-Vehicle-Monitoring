import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from cloud_ai.cloud_api import ModelRegistry, app
from cloud_ai.data_generation import generate_synthetic_cloud_history
from cloud_ai.failure_model import train_failure_model
from cloud_ai.history import InMemoryHistoryProvider
from cloud_ai.rul_model import train_rul_model


class HistoricalInferenceTests(unittest.TestCase):
    def test_analyze_uses_and_persists_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "cloud_health_history.csv")
            rul_path = os.path.join(tmpdir, "rul_model.pkl")
            failure_path = os.path.join(tmpdir, "failure_model.pkl")

            generate_synthetic_cloud_history(output_path=csv_path, rows=300, seed=99)
            train_rul_model(data_path=csv_path, model_path=rul_path)
            train_failure_model(data_path=csv_path, model_path=failure_path)

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                ModelRegistry.rul_model = None
                ModelRegistry.failure_model = None
                ModelRegistry.history_provider = InMemoryHistoryProvider()

                with TestClient(app) as client:
                    payload_1 = {
                        "vehicle_id": "VIT_CAR_HIST",
                        "timestamp_ms": 1707051123456,
                        "thermal_brake_margin": -0.21,
                        "thermal_engine_margin": 0.34,
                        "thermal_stress_index": 0.91,
                        "mechanical_vibration_anomaly_score": 0.89,
                        "mechanical_dominant_fault_band_hz": 142,
                        "mechanical_vibration_rms": 0.95,
                        "electrical_charging_efficiency_score": 0.62,
                        "electrical_battery_health_pct": 78,
                        "engine_rul_pct": 45,
                        "brake_rul_pct": 32,
                        "battery_rul_pct": 70,
                        "vehicle_health_score": 0.52,
                    }
                    first = client.post("/analyze", json=payload_1)
                    self.assertEqual(first.status_code, 200)
                    first_body = first.json()
                    self.assertEqual(first_body["history_points_used"], 0)

                    payload_2 = dict(payload_1)
                    payload_2["timestamp_ms"] = payload_1["timestamp_ms"] + 1000
                    payload_2["thermal_stress_index"] = 0.3
                    payload_2["mechanical_vibration_anomaly_score"] = 0.25
                    payload_2["engine_rul_pct"] = 72
                    payload_2["brake_rul_pct"] = 68
                    payload_2["vehicle_health_score"] = 0.78
                    second = client.post("/analyze", json=payload_2)
                    self.assertEqual(second.status_code, 200)
                    second_body = second.json()
                    self.assertGreaterEqual(second_body["history_points_used"], 1)

                    # Historical blending should affect the second inference trajectory.
                    self.assertNotEqual(
                        first_body["fault_failure_probability_7d"],
                        second_body["fault_failure_probability_7d"],
                    )
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
