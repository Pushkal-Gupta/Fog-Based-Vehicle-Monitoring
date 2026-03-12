"""Synthetic Section-6 style data generation for cloud AI training/testing."""

from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_cloud_history(
    output_path: str = "cloud_health_history.csv",
    rows: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    thermal_stress_index = rng.uniform(0.0, 1.0, rows)
    vibration_anomaly = rng.uniform(0.0, 1.0, rows)
    charging_eff = rng.uniform(0.45, 1.0, rows)
    vehicle_health = rng.uniform(0.2, 1.0, rows)

    brake_rul_pct = np.clip(100 - 62 * thermal_stress_index - 38 * vibration_anomaly, 0, 100)
    battery_rul_pct = np.clip(68 + 30 * charging_eff - 22 * thermal_stress_index, 0, 100)
    engine_rul_pct = np.clip(
        96 - 52 * thermal_stress_index - 24 * vibration_anomaly + 8 * vehicle_health,
        0,
        100,
    )

    engine_rul_pct_future = np.clip(
        engine_rul_pct - 11 * thermal_stress_index - 7 * vibration_anomaly + rng.normal(0, 1.5, rows),
        0,
        100,
    )

    brake_rul_pct_future = np.clip(
        brake_rul_pct - 14 * thermal_stress_index - 10 * vibration_anomaly + rng.normal(0, 1.5, rows),
        0,
        100,
    )

    battery_rul_pct_future = np.clip(
        battery_rul_pct - 8 * thermal_stress_index + 12 * (1.0 - charging_eff) + rng.normal(0, 1.5, rows),
        0,
        100,
    )

    failure_next_7_days = (
        (engine_rul_pct < 45)
        | (brake_rul_pct < 35)
        | ((thermal_stress_index > 0.8) & (vibration_anomaly > 0.65))
    ).astype(int)

    df = pd.DataFrame(
        {
            "vehicle_id": [f"VIT_CAR_{i:04d}" for i in range(rows)],
            "timestamp_ms": 1707051123456 + np.arange(rows),
            "thermal_brake_margin": np.round(rng.uniform(-0.35, 0.45, rows), 3),
            "thermal_engine_margin": np.round(rng.uniform(-0.25, 0.55, rows), 3),
            "thermal_stress_index": np.round(thermal_stress_index, 4),
            "mechanical_vibration_anomaly_score": np.round(vibration_anomaly, 4),
            "mechanical_dominant_fault_band_hz": np.round(rng.uniform(90, 210, rows), 2),
            "mechanical_vibration_rms": np.round(rng.uniform(0.15, 1.2, rows), 3),
            "electrical_charging_efficiency_score": np.round(charging_eff, 4),
            "electrical_battery_health_pct": np.round(np.clip(55 + 45 * charging_eff, 0, 100), 2),
            "engine_rul_pct": np.round(engine_rul_pct, 3),
            "brake_rul_pct": np.round(brake_rul_pct, 3),
            "battery_rul_pct": np.round(battery_rul_pct, 3),
            "vehicle_health_score": np.round(vehicle_health, 4),
            "brake_health_index": np.round(brake_rul_pct / 100.0, 4),
            "engine_rul_pct_future": np.round(engine_rul_pct_future, 3),
            "brake_rul_pct_future": np.round(brake_rul_pct_future, 3),
            "battery_rul_pct_future": np.round(battery_rul_pct_future, 3),
            "failure_next_7_days": failure_next_7_days,
        }
    )

    if set(df["failure_next_7_days"].unique()) != {0, 1}:
        raise ValueError("Generated dataset does not contain both failure classes.")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    generated = generate_synthetic_cloud_history()
    print(f"Generated {len(generated)} rows in cloud_health_history.csv")
