

# FINAL DATA FLOW (AUTHORITATIVE)

```
[ Edge + Local AI ]
        |
        |  (POST – summarized intelligence)
        v
[ FastAPI Backend ]
        |
        |  (store + cache)
        v
[ MongoDB ]
   |              |
   |              |
   v              v
[ Frontend ]   [ Cloud AI ]
                    |
                    |  (POST – long-term insights)
                    v
              [ Backend + DB ]
```

---

# 1. EDGE → BACKEND (Primary Ingest)

### Direction

**WRITE ONLY**

### Endpoint

```
POST /api/v1/vehicle/intelligence/ingest
```

### JSON (EXACT – stored as-is)

```json
{
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,

  "health_vectors": {
    "thermal": {
      "brake_thermal_margin": -0.21,
      "engine_thermal_margin": 0.34
    },
    "mechanical": {
      "vibration_anomaly_score": 0.77,
      "dominant_fault_band_hz": 142
    },
    "electrical": {
      "charging_efficiency_score": 0.81,
      "battery_degradation_trend": "stable"
    },
    "usage_behavior": {
      "driver_aggression_score": 0.58,
      "stress_amplification_factor": 1.27
    }
  },

  "rul_estimates": {
    "engine_rul_pct": 62,
    "brake_rul_pct": 28,
    "battery_rul_pct": 74
  },

  "fault_inference": {
    "primary_fault": "BRAKE_THERMAL_SATURATION",
    "contributing_factors": [
      "high_brake_temp_rise_rate",
      "low_brake_pad_remaining",
      "moderate_driver_aggression"
    ],
    "failure_probability_7d": 0.61
  },

  "vehicle_health_score": 0.64,

  "recommendations": {
    "service_priority": "high",
    "suggested_action": "Brake inspection and pad replacement",
    "safe_operating_limit_km": 120
  }
}
```

### Backend action

* Insert into **`vehicle_intelligence`**
* Update **`vehicle_state_cache.latest_intelligence`**
* Push WebSocket update
* ACK

### Response

```json
{ "status": "ok" }
```

---

# 2. DATABASE: PRIMARY COLLECTIONS

## A. `vehicle_intelligence` (append-only, time-series)

```json
{
  _id,
  vehicle_id,
  timestamp_ms,
  health_vectors,
  rul_estimates,
  fault_inference,
  vehicle_health_score,
  recommendations
}
```

**Indexes**

* `{ vehicle_id, timestamp_ms }`
* optional TTL if storage constrained

---

## B. `vehicle_state_cache` (1 doc per vehicle)

```json
{
  vehicle_id,
  last_seen,
  latest_intelligence
}
```

Used for:

* instant dashboard load
* Digital Twin sync

---

## C. `long_term_insights` (from cloud AI)

**Schema-flexible by design**

```json
{
  _id,
  vehicle_id,
  generated_at_ms,
  model_id,
  schema_version,

  insights: { },
  confidence_score,
  validity_window_days
}
```

> `insights` intentionally untyped
> You **must not hardcode structure** yet

---

# 3. BACKEND → FRONTEND (Dashboard Reads)

### A. On load (snapshot)

```
GET /api/v1/vehicles/VIT_CAR_001/latest
```

```json
{
  "vehicle_id": "VIT_CAR_001",
  "last_seen": 1707051123456,
  "current_state": {
    "vehicle_health_score": 0.64,
    "primary_fault": "BRAKE_THERMAL_SATURATION",
    "rul_estimates": {
      "engine_rul_pct": 62,
      "brake_rul_pct": 28,
      "battery_rul_pct": 74
    },
    "recommendations": {
      "service_priority": "high",
      "suggested_action": "Brake inspection and pad replacement"
    }
  },
  "long_term_insights": [ ... ]
}
```

---

### B. Realtime (Digital Twin)

**WebSocket event**

```json
{
  "type": "INTELLIGENCE_UPDATE",
  "vehicle_id": "VIT_CAR_001",
  "timestamp_ms": 1707051123456,
  "data": {
    "vehicle_health_score": 0.64,
    "primary_fault": "BRAKE_THERMAL_SATURATION",
    "service_priority": "high"
  }
}
```

---

# 4. BACKEND → CLOUD AI (Long-Horizon Analysis Input)

### Direction

**READ ONLY**

### Endpoint

```
GET /api/v1/intelligence/bulk
```

### JSON

```json
{
  "vehicle_id": "VIT_CAR_001",
  "window": {
    "from_ts": 1706000000000,
    "to_ts": 1707051123456
  },
  "records": [
    {
      "timestamp_ms": 1707051123456,
      "health_vectors": { ... },
      "rul_estimates": { ... },
      "fault_inference": { ... },
      "vehicle_health_score": 0.64
    }
  ]
}
```

---

# 5. CLOUD AI → BACKEND (Future / Long-Term Recommendations)

### Direction

**WRITE ONLY**

### Endpoint

```
POST /api/v1/insights/long-term
```

### JSON (schema-agnostic, future-proof)

```json
{
  "vehicle_id": "VIT_CAR_001",
  "generated_at_ms": 1708000000000,
  "model_id": "cloud-ai-v3",
  "schema_version": "experimental",

  "insights": {
    "predicted_failure_window_days": 21,
    "maintenance_bundle": [
      "brake_system",
      "suspension_alignment"
    ],
    "operational_advice": "Reduce aggressive braking to extend brake life"
  },

  "confidence_score": 0.86,
  "validity_window_days": 30
}
```

Backend:

* stores as-is
* never interprets fields
* frontend renders dynamically

---




