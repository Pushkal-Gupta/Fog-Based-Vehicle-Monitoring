# AI Models and Intelligence Architecture

This document explains **all AI and intelligence models used in the Fog-Based Vehicle Monitoring System**, including where they run, what type of models they are, and how they interact with the system data pipeline.

The system intentionally uses **multiple narrow, explainable models** instead of a single monolithic AI. Each model has a clearly bounded responsibility and authority, aligned with strict fog–cloud separation.

---

## AI Models Overview (At a Glance)

| #   | Model Name                        | Runs On | Model Type                      | Input Dataset Section | Output Dataset Section |
| --- | --------------------------------- | ------- | ------------------------------- | --------------------- | ---------------------- |
| 1   | Critical Safety Classifier        | **Fog** | Binary Classifier (Rule-Based)  | Section 1 + internal  | Section 5 and 6        |
| 2   | Remaining Useful Life (RUL) Model | Cloud   | Regression / Survival Model     | Section 6 (+ history) | Section 7              |
| 3   | Failure Probability Model         | Cloud   | Probabilistic Binary Classifier | Section 6 (+ history) | Section 7              |
| 4   | Degradation Trend Model           | Cloud   | Multiclass Classifier           | Section 6 (+ history) | Section 7              |
| 5   | Fault Explanation Engine          | Cloud   | Rule-Based Inference            | Section 7             | Section 7              |
| 6   | Recommendation Engine             | Cloud   | Rule-Based Policy Engine        | Section 7             | Section 7              |

**Section 2 (Fog Health Vectors) never leaves the fog**

**Section 6 is the only dataset transmitted to the cloud**

**Section 7 is cloud-internal, analytics-only data derived from Section 6 and history, with no feedback path to fog computation or actuation.**

---

## Design Principles

- **Fog decides** what happens _now_
- **AI predicts** what may happen _next_
- **Rules explain** why decisions were made
- **Hardware executes** actions

No cloud-based model has actuation authority.

---

## 1. Critical Safety Classifier (Fog)

### Purpose

Detect **immediate safety-critical conditions** and trigger autonomous actuation.

### Where It Runs

- **Fog node only**

### Model Type

**Binary classifier (deterministic, rule-based)**  
Outputs: `CRITICAL` or `NON_CRITICAL`

This is intentionally **not** a machine learning model.

### Inputs

From `dataset.md` (fog-internal only):

- Section 1: Raw hardware telemetry
- Section 3: Computed indices

Key inputs:

- `brake_temp_c`
- `brake_temp_rise_rate`
- `brake_health_index`
- `thermal_stress_index`

### Logic

```text
IF brake_temp_c > 180
AND brake_temp_rise_rate > 3.0
AND brake_health_index < 0.4
→ CRITICAL
```

## Outputs

**Section 5: Fog → Hardware Actuation Event**

This is the **only model allowed to cause physical action**.

---

## 2. Remaining Useful Life (RUL) Estimation Model

### Purpose

Estimate how much usable life remains in key vehicle components.

### Where It Runs

- Cloud (training + inference)

### Model Type

**Regression / Survival Analysis**

**Examples:**

- Random Forest Regressor
- Gradient Boosted Regressor
- Weibull-based survival model

### Inputs

- **Section 6:** Processed health and lifecycle data
- Historical **Section 6** records

Section 6 already encapsulates fog-derived health summaries and trends.

### Outputs

- **Section 6:** `rul_estimates`

```json
{
  "engine_rul_pct": 62,
  "brake_rul_pct": 28,
  "battery_rul_pct": 74
}
```

### Notes

RUL is **contextual guidance**, never a safety trigger.

---

## 3. Failure Probability Model

### Purpose

Predict the likelihood of component failure within a short horizon (for example, 7 days).

### Where It Runs

- Cloud

### Model Type

**Probabilistic Binary Classifier**

**Examples:**

- Logistic Regression
- Gradient Boosting Classifier

### Inputs

- **Section 6:** Current analytics packet
- Historical **Section 6** records

### Outputs

- **Section 6:** `failure_probability_7d`

```json
{
  "failure_probability_7d": 0.61
}
```

### Notes

Used for **urgency assessment**, not actuation.

---

## 4. Degradation Trend Model

### Purpose

Classify long-term degradation behavior of subsystems.

### Where It Runs

- Cloud

### Model Type

**Multiclass Classifier**

**Possible classes:**

- `stable`
- `slow_degrading`
- `rapid_degrading`

### Inputs

- **Section 6:** Temporal health and efficiency trends
- Long-term **Section 6** history

### Outputs

- **Section 6:** `battery_degradation_trend`

```json
{
  "battery_degradation_trend": "stable"
}
```

### Notes

Improves explainability for maintenance planning.

---

## 5. Fault Explanation Engine

### Purpose

Explain why a fault is occurring or likely to occur.

### Where It Runs

- Cloud

### Model Type

**Rule-based inference engine**

This is not a machine learning model.

### Inputs

- **Section 6 only**, including:
  - Health vectors
  - RUL estimates
  - Failure probabilities
  - Usage behavior summaries

### Outputs

- **Section 6:** `fault_inference`

```json
{
  "primary_fault": "BRAKE_THERMAL_SATURATION",
  "contributing_factors": [
    "high_brake_temp_rise_rate",
    "low_brake_pad_remaining",
    "moderate_driver_aggression"
  ]
}
```

### Notes

Critical for **transparency and human trust.**

---

## 6. Recommendation Engine

### Purpose

Translate technical risk into human-readable maintenance guidance.

### Where It Runs

- Cloud

### Model Type

**Rule-based policy engine**

### Inputs

From **Section 6**:

- RUL estimates
- Failure probability
- Fault inference

### Outputs

- **Section 6:** `recommendations`

```json
{
  "service_priority": "high",
  "suggested_action": "Brake inspection and pad replacement",
  "safe_operating_limit_km": 120
}
```

### Notes

This layer **does not predict**; it **advises**.

---

## Summary

- Fog uses a **binary safety classifier**
- Cloud consumes **only Section 6**
- AI predicts **future risk**
- Fog decides **present action**
- Policies convert predictions into **recommendations**

This architecture guarantees **deterministic safety**, **strict authority separation**, and **cloud-independent operation**, while still enabling advanced analytics and system observability.
