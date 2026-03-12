# Cloud AI Advisory Layer

This repository contains the **cloud-only intelligence layer** for predictive maintenance.

## Scope and Authority Separation

Cloud logic is advisory only:

- Remaining Useful Life (RUL) prediction
- Failure probability prediction
- Fault explanation
- Maintenance recommendation

Cloud does **not** perform real-time control or safety-critical actuation. Actuation authority remains fog-only.

## Quick start (from scratch)

If you just want to run everything end-to-end locally, use this sequence:

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Generate synthetic training data + train both models
python scripts/run_full_pipeline.py --output-dir . --rows 1000 --seed 42

# 3) Start API server
uvicorn cloud_ai.cloud_api:app --host 0.0.0.0 --port 8000
```

In a second terminal, test the server:

```bash
# Health
curl -s http://127.0.0.1:8000/health

# Analyze (Section-6 cloud input)
curl -s -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
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
    "vehicle_health_score": 0.64
  }'
```

Expected behavior:

- `/health` returns advisory-only status.
- `/analyze` returns cloud analytics only (RUL prediction, failure probability, explanation, recommendation).

## Input schema (Section 6 only)

The API accepts fog-curated analytics payloads (no raw Section-1 telemetry, no Section-2 fog internals):

```json
{
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
  "vehicle_health_score": 0.64
}
```

## Training

1. Prepare `cloud_health_history.csv` with required columns.
2. Train models:

```bash
python -m cloud_ai.rul_model
python -m cloud_ai.failure_model
```

This produces:

- `rul_model.pkl`
- `failure_model.pkl`

## Run API

```bash
uvicorn cloud_ai.cloud_api:app --host 0.0.0.0 --port 8000
```

## Endpoints

- `GET /health`
- `POST /analyze`

Example analytical output (Section 7 style, advisory-only):

```json
{
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,
  "engine_rul_pct": 58.21,
  "brake_rul_pct": 28.0,
  "battery_rul_pct": 74.0,
  "fault_failure_probability_7d": 0.61,
  "fault_primary": "BRAKE_THERMAL_SATURATION",
  "fault_contributing_factors": [
    "high_thermal_stress_index",
    "low_brake_rul_pct"
  ],
  "recommendation": {
    "recommendation_service_priority": "high",
    "recommendation_suggested_action": "Brake inspection and pad replacement",
    "recommendation_safe_operating_limit_km": 120
  }
}
```


## Historical data support (MongoDB)

Yes — the cloud API can take **historical Section-6 data** into account during inference.

At each `/analyze` call:

1. It fetches recent records for the same `vehicle_id` (window size from `HISTORY_WINDOW_SIZE`, default `50`).
2. It blends current Section-6 values with historical averages.
3. It predicts RUL and failure probability using these blended features.
4. It stores the current Section-6 payload back to history for the next cycle.

### Configure MongoDB backend

```bash
export CLOUD_MONGO_URI="mongodb://localhost:27017"
export CLOUD_MONGO_DB="cloud_ai"
export CLOUD_MONGO_COLLECTION="section6_history"
export HISTORY_WINDOW_SIZE=50
```

Then start API normally:

```bash
uvicorn cloud_ai.cloud_api:app --host 0.0.0.0 --port 8000
```

If `CLOUD_MONGO_URI` is not set or unavailable, the API falls back safely to no-history mode.

For local non-Mongo experimentation, you can use in-memory history:

```bash
export CLOUD_HISTORY_BACKEND=memory
```

`GET /health` reports which history backend is active (`mongo`, `memory`, or `none`).

## Groq LLM recommendations (optional)

The recommendation engine can use the **Groq API** for AI-generated maintenance advice.
When configured, Groq produces context-aware recommendations based on the full fault analysis.
If Groq is unavailable or errors, the system **automatically falls back** to the built-in rule-based engine.

### Configure Groq

```bash
export GROQ_API_KEY="gsk_your_key_here"
# Optional: override the default model (default: llama-3.3-70b-versatile)
export GROQ_MODEL="llama-3.3-70b-versatile"
```

Without `GROQ_API_KEY`, the API uses rule-based recommendations only (no Groq calls).

`GET /health` reports `"groq_configured": true/false`.

The recommendation output includes `"recommendation_source"`: either `"groq"` or `"rule_based"`.

## Validation

Run the full local validation suite:

```bash
python -m compileall cloud_ai tests
python -m unittest discover -s tests -v
```

The end-to-end test trains both models on a synthetic Section-6-style dataset and validates `/analyze` output through FastAPI `TestClient`.

## Generate synthetic training data

If you do not yet have historical cloud data, generate a Section-6 style training dataset:

```bash
python -m cloud_ai.data_generation
```

This creates `cloud_health_history.csv` with labels for:

- `engine_rul_pct_future` (for RUL regression)
- `failure_next_7_days` (for failure classification)

## One-command full validation

To test every part (data generation → training → API inference) run:

```bash
python scripts/test_everything.py
```


To generate data and train persisted artifacts in one command:

```bash
python scripts/run_full_pipeline.py --output-dir . --rows 1000 --seed 42
```

This will create:

- `cloud_health_history.csv`
- `rul_model.pkl`
- `failure_model.pkl`
