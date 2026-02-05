# AI Models and Intelligence Architecture

This document explains **all AI and intelligence models used in the Fog-Based Vehicle Monitoring System**, including where they run, what type of models they are, and how they interact with the system data pipeline.

The system intentionally uses **multiple narrow, explainable models** instead of a single monolithic AI. Each model has a clearly bounded responsibility and authority.

---

## AI Models Overview (At a Glance)

| #   | Model Name                        | Runs On | Model Type                      | Input Dataset Section | Output Dataset Section |
| --- | --------------------------------- | ------- | ------------------------------- | --------------------- | ---------------------- |
| 1   | Critical Safety Classifier        | **Fog** | Binary Classifier (Rule-Based)  | Section 1, Section 3  | Section 5              |
| 2   | Remaining Useful Life (RUL) Model | Cloud   | Regression / Survival Model     | Section 2             | Section 6              |
| 3   | Failure Probability Model         | Cloud   | Probabilistic Binary Classifier | Section 2 + history   | Section 6              |
| 4   | Degradation Trend Model           | Cloud   | Multiclass Classifier           | Section 2             | Section 6              |
| 5   | Fault Explanation Engine          | Cloud   | Rule-Based Inference            | Section 2 + Section 6 | Section 6              |
| 6   | Recommendation Engine             | Cloud   | Rule-Based Policy Engine        | Section 6             | Section 6              |

---

## Design Principle

- **Fog decides** what happens _now_
- **AI predicts** what may happen _next_
- **Rules explain** why decisions were made
- **Hardware executes** actions

No AI model directly triggers actuation.

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

From `dataset.md`:

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
- Optional lightweight inference on the fog

### Model Type

**Regression / Survival Analysis**

**Examples:**

- Random Forest Regressor
- Gradient Boosted Regressor
- Weibull-based survival model

### Inputs

- **Section 2:** Fog-computed health vectors
- Historical health trends

**Key features:**

- Thermal stress index
- Brake health index
- Vibration anomaly score
- Electrical efficiency metrics

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

- **Section 2:** Health vectors
- Historical degradation patterns

**Key signals:**

- Thermal margins
- Rate-of-change metrics
- Vibration anomalies
- Usage stress factors

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

- **Section 2:** Electrical and lifecycle state metrics
- Long-term historical windows

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

Explain **why** a fault is occurring or likely to occur.

### Where It Runs

- Cloud

### Model Type

**Rule-based inference engine**

> This is **not** a machine learning model.

### Inputs

- **Section 2:** Health vectors
- **Section 6:** AI predictions (RUL, probabilities)

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

Translate technical risk into **human-readable maintenance guidance**.

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
- Cloud uses **regression and probabilistic classifiers**
- AI predicts **future risk**
- Fog decides **present action**
- Policies convert predictions into **recommendations**
