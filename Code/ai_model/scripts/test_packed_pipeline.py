"""
Script to Verify Packed Pipeline
=================================
Loads `cloud_ai_pipeline.pkl` and runs a prediction.

Usage:
    python scripts/test_packed_pipeline.py
"""

import sys
import os
import joblib

# Ensure project root is in path so it can find 'cloud_ai' module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cloud_ai.schemas import CloudInput

def main():
    pkl_path = "cloud_ai_pipeline.pkl"
    if not os.path.exists(pkl_path):
        print(f"❌ Pickle file {pkl_path} not found. Run scripts/package_pipeline.py first.")
        return

    print(f"📦 Loading pipeline from {pkl_path}...")
    pipeline = joblib.load(pkl_path)
    print("✅ Pipeline loaded successfully!")

    # Test Data
    payload = {
        "vehicle_id": "TEST_PACKED_001",
        "timestamp_ms": 1707051123456,
        "thermal_brake_margin": 0.30,
        "thermal_engine_margin": 0.40,
        "thermal_stress_index": 0.85,  # High stress -> should trigger brake thermal fault
        "mechanical_vibration_anomaly_score": 0.10,
        "mechanical_dominant_fault_band_hz": 60.0,
        "mechanical_vibration_rms": 0.15,
        "electrical_charging_efficiency_score": 0.95,
        "electrical_battery_health_pct": 95.0,
        "engine_rul_pct": 85.0,
        "brake_rul_pct": 20.0,  # Low brake RUL
        "battery_rul_pct": 88.0,
        "vehicle_health_score": 0.90,
    }

    print("\n🔍 Running prediction...")
    result = pipeline.predict(payload)

    print("\n📊 Result:")
    print(f"  • Vehicle ID: {result['vehicle_id']}")
    print(f"  • Fault: {result['fault_primary']}")
    print(f"  • Contributors: {result['fault_contributing_factors']}")
    print(f"  • Priority: {result['recommendation']['recommendation_service_priority']}")
    print(f"  • Action: {result['recommendation']['recommendation_suggested_action']}")
    print(f"  • Limit: {result['recommendation']['recommendation_safe_operating_limit_km']} km")

    if result['fault_primary'] == "BRAKE_THERMAL_SATURATION":
        print("\n✅ Verification PASSED: Correctly detected brake thermal fault.")
    else:
        print(f"\n❌ Verification FAILED: Expected BRAKE_THERMAL_SATURATION, got {result['fault_primary']}")

if __name__ == "__main__":
    main()
