import os
import tempfile
import unittest

from cloud_ai.data_generation import generate_synthetic_cloud_history


class DataGenerationTests(unittest.TestCase):
    def test_generate_training_data_contains_required_columns_and_classes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "cloud_health_history.csv")
            df = generate_synthetic_cloud_history(output_path=output_path, rows=200, seed=123)

            self.assertTrue(os.path.exists(output_path))
            self.assertEqual(len(df), 200)

            required_cols = {
                "vehicle_id",
                "timestamp_ms",
                "thermal_stress_index",
                "mechanical_vibration_anomaly_score",
                "electrical_charging_efficiency_score",
                "engine_rul_pct",
                "brake_rul_pct",
                "battery_rul_pct",
                "vehicle_health_score",
                "brake_health_index",
                "engine_rul_pct_future",
                "failure_next_7_days",
            }
            self.assertTrue(required_cols.issubset(set(df.columns)))
            self.assertEqual(set(df["failure_next_7_days"].unique()), {0, 1})


if __name__ == "__main__":
    unittest.main()
