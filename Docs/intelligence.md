# AI Models and Intelligence Architecture

This document explains all AI and intelligence components used in the **Fog-Based Vehicle Monitoring System**, including where they run, what type of intelligence they represent, and how they interact with the system data pipeline.

The system intentionally uses **multiple narrow, explainable components** instead of a single monolithic AI. Each component has a clearly bounded responsibility and authority, aligned with strict fog–cloud separation.

---

## AI / Intelligence Components Overview

| #   | Component Name                    | Runs On | Type                                | Input Dataset            | Output Dataset |
| --- | --------------------------------- | ------- | ----------------------------------- | ------------------------ | -------------- |
| 1   | Critical Safety Classifier        | Fog     | Deterministic Rule-Based Classifier | Section 1 + fog-internal | Section 5      |
| 2   | Remaining Useful Life (RUL) Model | Cloud   | Regression / Survival Model         | Section 6 (+ history)    | Section 7      |
| 3   | Failure Probability Model         | Cloud   | Probabilistic Binary Classifier     | Section 6 (+ history)    | Section 7      |
| 4   | Fault Explanation Engine          | Cloud   | Rule-Based Inference Engine         | Section 6 + Section 7    | Section 7      |
| 5   | Recommendation Engine             | Cloud   | Rule-Based Policy Engine            | Section 7                | Section 7      |

**Section 2 (Fog Health Vectors) never leaves the fog.**  
**Section 6 is the only dataset transmitted to the cloud.**  
**Section 7 is cloud-internal, analytics-only data with no feedback path to fog computation or actuation.**

---

## Design Principles

- Fog decides what happens **now**
- Cloud predicts what may happen **next**
- Rules explain **why** predictions and risks exist
- Hardware executes actions
- No cloud-based intelligence has actuation authority

---

## 1. Critical Safety Classifier (Fog)

### Purpose

Detect immediate safety-critical conditions and trigger autonomous actuation.

This component answers the question:  
**“Is the vehicle in danger right now?”**

### Where It Runs

Fog node only

### Type

Binary classifier (deterministic, rule-based)

This is intentionally **not** a machine learning model.

### Inputs (fog-internal only)

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

**Section 5:** Fog → Hardware Actuation Event

This is the **only component in the system allowed to cause physical action**.

---

## Analogy

The **Critical Safety Classifier** is like a **circuit breaker**.

It does not forecast future problems or analyze trends.  
It simply detects an unsafe condition **right now** and immediately intervenes to prevent damage.

---

## 2. Remaining Useful Life (RUL) Estimation Model

### Purpose

Estimate how much usable life remains in key vehicle components.

This model answers:

> **“How worn is this component, based on how it has been used so far?”**

---

### Where It Runs

Cloud (training and inference)

---

### Type

Regression / Survival Analysis

---

### Inputs

- Section 6 (flattened health and lifecycle features)
- Historical Section 6 records

---

### Outputs (Section 7)

- `engine_rul_pct`
- `brake_rul_pct`
- `battery_rul_pct`

---

### Analogy

RUL estimation is like checking **how much tread is left on a tire**.

You are not predicting the exact day the tire will fail.  
You are estimating how much usable material remains, based on past wear and usage conditions.

---

### Notes

- RUL is **prognostic**, not reactive
- It is **never used as a safety trigger**
- Low RUL does **not** imply imminent failure

---

## 3. Failure Probability Model

### Purpose

Estimate short-horizon failure risk (for example, within 7 days).

This model answers:

> **“Given current conditions, how likely is failure soon?”**

---

### Where It Runs

Cloud

---

### Type

Probabilistic Binary Classifier

---

### Inputs

- Section 6 (current flattened features)
- Historical Section 6 records

---

### Outputs (Section 7)

- `failure_probability_7d`

---

### Analogy

This model is like a **weather forecast**.

A 70% chance of rain does not guarantee rain,  
but it strongly influences near-term decisions and preparedness.

---

### Notes

- Complementary to RUL
- Short-term and context-sensitive
- Has **no actuation authority**

---

## 4. Fault Explanation Engine

### Purpose

Provide transparent, human-readable explanations for predicted or emerging faults.

This component answers:

> **“Why does the system believe this fault is occurring?”**

---

### Where It Runs

Cloud

---

### Type

Rule-based inference engine (non-ML)

---

### Inputs

- Section 6 (current health features)
- Section 7 (RUL estimates and failure probability)

---

### Outputs (Section 7)

- `primary_fault`
- `contributing_factors`

---

### Analogy

This engine is like a **doctor explaining a diagnosis**.

The test results already exist.  
The explanation connects them into a coherent, understandable narrative.

---

### Notes

- Critical for trust and auditability
- Does not predict or decide
- Purely explanatory

---

## 5. Recommendation Engine

### Purpose

Translate technical risk into actionable maintenance guidance.

This component answers:

> **“What should the human do next?”**

---

### Where It Runs

Cloud

---

### Type

Rule-based policy engine

---

### Inputs

- RUL estimates
- Failure probability
- Fault inference

---

### Outputs (Section 7)

- `service_priority`
- `suggested_action`
- `safe_operating_limit_km`

---

### Analogy

This engine is like a **maintenance advisor**.

It does not diagnose problems or control the vehicle.  
It simply converts known risks into clear, practical guidance.

---

### Notes

- Does not learn
- Does not predict
- Enforces predefined safety and maintenance policies

---

## Summary

- Fog performs deterministic, real-time safety decisions
- Cloud consumes only flattened Section 6 features
- AI components predict future risk, not present action
- Rule engines explain and contextualize predictions
- Policy engines convert risk into guidance
- Physical actuation remains fog-exclusive

This architecture guarantees **deterministic safety**, **strict authority separation**, and **cloud-independent operation**, while still enabling advanced analytics and system observability.
