import os
import tempfile
import unittest

import pandas as pd
from fastapi.testclient import TestClient

from cloud_ai.cloud_api import ModelRegistry, app
from cloud_ai.failure_model import train_failure_model
from cloud_ai.rul_model import train_rul_model


class EndToEndCloudAITests(unittest.TestCase):
    def _build_dataset(self, rows: int = 160) -> pd.DataFrame:
        records = []
        for i in range(rows):
            thermal_stress_index = ((i * 7) % 100) / 100
            mechanical_vibration_anomaly_score = ((i * 11) % 100) / 100
            electrical_charging_efficiency_score = ((i * 13) % 100) / 100
            vehicle_health_score = ((i * 17) % 100) / 100

            brake_rul_pct = max(0.0, min(100.0, 100 - 70 * thermal_stress_index - 40 * mechanical_vibration_anomaly_score))
            battery_rul_pct = max(0.0, min(100.0, 85 + 15 * electrical_charging_efficiency_score - 25 * thermal_stress_index))
            engine_rul_pct = max(0.0, min(100.0, 95 - 55 * thermal_stress_index - 25 * mechanical_vibration_anomaly_score + 10 * vehicle_health_score))
            engine_rul_pct_future = max(0.0, min(100.0, engine_rul_pct - 10 * thermal_stress_index - 6 * mechanical_vibration_anomaly_score))

            failure_next_7_days = int(
                (engine_rul_pct < 45 and mechanical_vibration_anomaly_score > 0.6)
                or brake_rul_pct < 35
                or thermal_stress_index > 0.8
            )

            records.append(
                {
                    "vehicle_id": f"VIT_CAR_{i:03d}",
                    "timestamp_ms": 1707051123456 + i,
                    "thermal_brake_margin": -0.21,
                    "thermal_engine_margin": 0.34,
                    "thermal_stress_index": thermal_stress_index,
                    "mechanical_vibration_anomaly_score": mechanical_vibration_anomaly_score,
                    "mechanical_dominant_fault_band_hz": 120 + (i % 40),
                    "mechanical_vibration_rms": 0.3 + (i % 12) / 20,
                    "electrical_charging_efficiency_score": electrical_charging_efficiency_score,
                    "electrical_battery_health_pct": 60 + (i % 40),
                    "engine_rul_pct": engine_rul_pct,
                    "brake_rul_pct": brake_rul_pct,
                    "battery_rul_pct": battery_rul_pct,
                    "vehicle_health_score": vehicle_health_score,
                    "brake_health_index": brake_rul_pct / 100.0,
                    "engine_rul_pct_future": engine_rul_pct_future,
                    "failure_next_7_days": failure_next_7_days,
                }
            )

        df = pd.DataFrame(records)
        assert set(df["failure_next_7_days"].unique()) == {0, 1}
        return df

    def test_training_and_inference_api(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "cloud_health_history.csv")
            self._build_dataset().to_csv(csv_path, index=False)

            rul_path = os.path.join(tmpdir, "rul_model.pkl")
            failure_path = os.path.join(tmpdir, "failure_model.pkl")
            train_rul_model(data_path=csv_path, model_path=rul_path)
            train_failure_model(data_path=csv_path, model_path=failure_path)

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                ModelRegistry.rul_model = None
                ModelRegistry.failure_model = None

                with TestClient(app) as client:
                    health_response = client.get("/health")
                    self.assertEqual(health_response.status_code, 200)
                    self.assertEqual(health_response.json()["mode"], "advisory-only")

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
                    analyze_response = client.post("/analyze", json=payload)

                self.assertEqual(analyze_response.status_code, 200)
                body = analyze_response.json()
                self.assertIn("vehicle_id", body)
                self.assertIn("timestamp_ms", body)
                self.assertIn("engine_rul_pct", body)
                self.assertIn("fault_failure_probability_7d", body)
                self.assertIn("fault_primary", body)
                self.assertIn("fault_contributing_factors", body)
                self.assertIn("recommendation", body)
                self.assertGreaterEqual(body["engine_rul_pct"], 0.0)
                self.assertLessEqual(body["engine_rul_pct"], 100.0)
                self.assertGreaterEqual(body["fault_failure_probability_7d"], 0.0)
                self.assertLessEqual(body["fault_failure_probability_7d"], 1.0)
                self.assertIn("recommendation_service_priority", body["recommendation"])
                self.assertIn("recommendation_suggested_action", body["recommendation"])
                self.assertIn("recommendation_safe_operating_limit_km", body["recommendation"])
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
