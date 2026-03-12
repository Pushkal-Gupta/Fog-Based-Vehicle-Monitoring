"""
Script to Package Cloud AI into a Single .pkl File
===================================================
Creates a `CloudAIPipeline` object that wraps:
1. RUL Prediction Model
2. Failure Prediction Model
3. History Logic (In-Memory)
4. Fault Explanation Rules
5. Recommendation Engine (Groq + Rule-Based)

Usage:
    python scripts/package_pipeline.py
    # Output: cloud_ai_pipeline.pkl
"""

import os
import sys
import joblib
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloud_ai.explanation import explain_fault
from cloud_ai.recommendation import recommend_action
from cloud_ai.history import blend, summarize_history, InMemoryHistoryProvider
from cloud_ai.rul_model import RUL_FEATURES
from cloud_ai.failure_model import FAILURE_FEATURES
from cloud_ai.schemas import CloudInput, CloudOutput, Recommendation


class CloudAIPipeline:
    def __init__(self, rul_model, failure_model):
        self.rul_model = rul_model
        self.failure_model = failure_model
        self.history_provider = InMemoryHistoryProvider()
        self.history_limit = 50

    def predict(self, data: dict) -> dict:
        """
        Main inference method.
        Input:  dict (or CloudInput object)
        Output: dict (CloudOutput)
        """
        # 1. Validate Input
        if isinstance(data, dict):
            # Parse via Pydantic to ensure types/ranges
            input_obj = CloudInput(**data)
        else:
            input_obj = data

        # 2. History Handling
        history_records = self.history_provider.fetch_recent(input_obj.vehicle_id, self.history_limit)
        history_snapshot = summarize_history(history_records)

        # 3. Feature Blending (Current + History)
        # RUL Features
        rul_feature_map = {
            "thermal_stress_index": blend(input_obj.thermal_stress_index, history_snapshot.avg_thermal_stress_index),
            "brake_health_index": blend(input_obj.brake_rul_pct / 100.0, 
                                      None if history_snapshot.avg_brake_rul_pct is None 
                                      else history_snapshot.avg_brake_rul_pct / 100.0),
            "mechanical_vibration_anomaly_score": blend(input_obj.mechanical_vibration_anomaly_score, 
                                                      history_snapshot.avg_vibration_anomaly_score),
            "electrical_charging_efficiency_score": blend(input_obj.electrical_charging_efficiency_score, 
                                                        history_snapshot.avg_charging_efficiency),
            "vehicle_health_score": blend(input_obj.vehicle_health_score, history_snapshot.avg_vehicle_health_score),
        }
        
        # 4. RUL Prediction
        rul_vector = pd.DataFrame([rul_feature_map])[RUL_FEATURES]
        pred_engine_rul = float(self.rul_model.predict(rul_vector)[0])
        pred_engine_rul = max(0.0, min(100.0, pred_engine_rul))

        # 5. Failure Prediction
        # Blended features for failure model
        fail_feats = {
            "engine_rul_pct": blend(pred_engine_rul, history_snapshot.avg_engine_rul_pct),
            "brake_rul_pct": blend(input_obj.brake_rul_pct, history_snapshot.avg_brake_rul_pct),
            "battery_rul_pct": blend(input_obj.battery_rul_pct, history_snapshot.avg_battery_rul_pct),
            "thermal_stress_index": blend(input_obj.thermal_stress_index, history_snapshot.avg_thermal_stress_index),
            "mechanical_vibration_anomaly_score": blend(
                input_obj.mechanical_vibration_anomaly_score,
                history_snapshot.avg_vibration_anomaly_score,
            ),
        }
        fail_vector = pd.DataFrame([fail_feats])[FAILURE_FEATURES]
        failure_prob = float(self.failure_model.predict_proba(fail_vector)[0][1])

        # 6. Explanation & Recommendation
        fault_primary, contributors = explain_fault(input_obj, failure_prob)
        
        # Recommendation (Pass Groq Key via env externally if needed)
        rec_dict = recommend_action(
            failure_prob=failure_prob,
            engine_rul_pct=pred_engine_rul,
            brake_rul_pct=input_obj.brake_rul_pct,
            battery_rul_pct=input_obj.battery_rul_pct,
            fault_primary=fault_primary,
            contributing_factors=contributors,
        )

        # 7. Save History
        # We save the *input* record for future context
        if isinstance(data, dict):
            self.history_provider.save_record(data)
        else:
            self.history_provider.save_record(input_obj.model_dump())

        # 8. Construct Output
        return {
            "vehicle_id": input_obj.vehicle_id,
            "timestamp_ms": input_obj.timestamp_ms,
            "engine_rul_pct": round(pred_engine_rul, 2),
            "brake_rul_pct": round(input_obj.brake_rul_pct, 2),
            "battery_rul_pct": round(input_obj.battery_rul_pct, 2),
            "fault_failure_probability_7d": round(failure_prob, 2),
            "fault_primary": fault_primary,
            "fault_contributing_factors": contributors,
            "recommendation": rec_dict,
            "history_points_used": history_snapshot.points_used,
        }


def main():
    print("📦 Packing Cloud AI Pipeline...")
    
    # Paths
    rul_path = Path("rul_model.pkl")
    fail_path = Path("failure_model.pkl")
    output_path = Path("cloud_ai_pipeline.pkl")

    if not rul_path.exists() or not fail_path.exists():
        print("❌ Models not found! Run training first.")
        return

    # Load Models
    print(f"  - Loading RUL model from {rul_path}")
    rul_model = joblib.load(rul_path)
    
    print(f"  - Loading Failure model from {fail_path}")
    fail_model = joblib.load(fail_path)

    # Create Pipeline
    pipeline = CloudAIPipeline(rul_model, fail_model)
    
    # Save
    print(f"  - Saving unified pipeline to {output_path}")
    joblib.dump(pipeline, output_path)
    
    print(f"\n✅ Done! You can now load it like this:\n")
    print(f"    import joblib")
    print(f"    pipeline = joblib.load('cloud_ai_pipeline.pkl')")
    print(f"    result = pipeline.predict(my_data_dict)")
    print(f"    # Note: Requires 'cloud_ai' package in valid python path")


if __name__ == "__main__":
    main()
