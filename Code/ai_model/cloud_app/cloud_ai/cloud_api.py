"""FastAPI advisory service for cloud AI maintenance analytics."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException

from cloud_ai.explanation import explain_fault
from cloud_ai.failure_model import FAILURE_FEATURES
from cloud_ai.history import blend, build_history_provider_from_env, summarize_history
from cloud_ai.recommendation import recommend_action
from cloud_ai.rul_model import RUL_FEATURES
from cloud_ai.schemas import CloudInput, CloudOutput

app = FastAPI(title="Cloud AI Advisory API", version="2.1.0")

RUL_MODEL_PATH = Path("rul_model.pkl")
FAILURE_MODEL_PATH = Path("failure_model.pkl")


class ModelRegistry:
    rul_model = None
    failure_model = None
    history_provider = None


@app.on_event("startup")
def load_models() -> None:
    if not RUL_MODEL_PATH.exists() or not FAILURE_MODEL_PATH.exists():
        raise RuntimeError(
            "Model files not found. Train models first: "
            "python -m cloud_ai.rul_model && python -m cloud_ai.failure_model"
        )

    ModelRegistry.rul_model = joblib.load(RUL_MODEL_PATH)
    ModelRegistry.failure_model = joblib.load(FAILURE_MODEL_PATH)
    if ModelRegistry.history_provider is None:
        ModelRegistry.history_provider = build_history_provider_from_env()


@app.get("/health")
def health() -> dict[str, Any]:
    backend_name = ModelRegistry.history_provider.__class__.__name__
    if backend_name == "MongoHistoryProvider":
        history_backend = "mongo"
    elif backend_name == "InMemoryHistoryProvider":
        history_backend = "memory"
    else:
        history_backend = "none"
    return {
        "status": "ok",
        "mode": "advisory-only",
        "authority": "cloud_has_no_actuation_control",
        "history_backend": history_backend,
        "history_window_size": int(os.getenv("HISTORY_WINDOW_SIZE", "50")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "")),
    }


@app.post("/analyze", response_model=CloudOutput)
def analyze(data: CloudInput) -> CloudOutput:
    if ModelRegistry.rul_model is None or ModelRegistry.failure_model is None:
        raise HTTPException(status_code=503, detail="Models are not loaded")

    if ModelRegistry.history_provider is None:
        ModelRegistry.history_provider = build_history_provider_from_env()

    history_limit = int(os.getenv("HISTORY_WINDOW_SIZE", "50"))
    history_records = ModelRegistry.history_provider.fetch_recent(data.vehicle_id, history_limit)
    history_snapshot = summarize_history(history_records)

    # Blend Section-6 current state with same-vehicle historical aggregates for robustness.
    rul_feature_map = {
        "thermal_stress_index": blend(data.thermal_stress_index, history_snapshot.avg_thermal_stress_index),
        "brake_health_index": blend(data.brake_rul_pct / 100.0, None if history_snapshot.avg_brake_rul_pct is None else history_snapshot.avg_brake_rul_pct / 100.0),
        "mechanical_vibration_anomaly_score": blend(data.mechanical_vibration_anomaly_score, history_snapshot.avg_vibration_anomaly_score),
        "electrical_charging_efficiency_score": blend(data.electrical_charging_efficiency_score, history_snapshot.avg_charging_efficiency),
        "vehicle_health_score": blend(data.vehicle_health_score, history_snapshot.avg_vehicle_health_score),
    }
    rul_vector = pd.DataFrame([rul_feature_map])[RUL_FEATURES]
    predicted_engine_rul_pct = float(ModelRegistry.rul_model.predict(rul_vector)[0])
    predicted_engine_rul_pct = max(0.0, min(100.0, predicted_engine_rul_pct))

    blended_engine_rul_for_failure = blend(predicted_engine_rul_pct, history_snapshot.avg_engine_rul_pct)
    blended_brake_rul_for_failure = blend(data.brake_rul_pct, history_snapshot.avg_brake_rul_pct)
    blended_battery_rul_for_failure = blend(data.battery_rul_pct, history_snapshot.avg_battery_rul_pct)
    blended_thermal_stress_for_failure = blend(data.thermal_stress_index, history_snapshot.avg_thermal_stress_index)
    blended_vibration_for_failure = blend(
        data.mechanical_vibration_anomaly_score,
        history_snapshot.avg_vibration_anomaly_score,
    )

    failure_vector = pd.DataFrame(
        [
            {
                "engine_rul_pct": blended_engine_rul_for_failure,
                "brake_rul_pct": blended_brake_rul_for_failure,
                "battery_rul_pct": blended_battery_rul_for_failure,
                "thermal_stress_index": blended_thermal_stress_for_failure,
                "mechanical_vibration_anomaly_score": blended_vibration_for_failure,
            }
        ]
    )[FAILURE_FEATURES]
    failure_prob = float(ModelRegistry.failure_model.predict_proba(failure_vector)[0][1])

    fault_primary, contributors = explain_fault(data, failure_prob)
    recommendation = recommend_action(
        failure_prob=failure_prob,
        engine_rul_pct=predicted_engine_rul_pct,
        brake_rul_pct=data.brake_rul_pct,
        battery_rul_pct=data.battery_rul_pct,
        fault_primary=fault_primary,
        contributing_factors=contributors,
    )

    ModelRegistry.history_provider.save_record(data.model_dump())

    return CloudOutput(
        vehicle_id=data.vehicle_id,
        timestamp_ms=data.timestamp_ms,
        engine_rul_pct=round(predicted_engine_rul_pct, 2),
        brake_rul_pct=round(data.brake_rul_pct, 2),
        battery_rul_pct=round(data.battery_rul_pct, 2),
        fault_failure_probability_7d=round(failure_prob, 2),
        fault_primary=fault_primary,
        fault_contributing_factors=contributors,
        recommendation=recommendation,
        history_points_used=history_snapshot.points_used,
    )
