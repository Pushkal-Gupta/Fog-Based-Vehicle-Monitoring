# AI Model Layer

## Overview

The AI model layer provides **predictive intelligence and risk estimation** for the Fog-Based Vehicle Monitoring System. It analyzes historical and aggregated vehicle health data to identify degradation patterns, estimate component lifespan, and support long-term decision-making.

This layer **does not participate in real-time safety actuation** and is not part of the latency-critical execution path.

---

## Role in the System

The AI model layer acts as the **analytical and learning component** of the system. While the fog module performs immediate interpretation and control, this layer focuses on:

- Learning from historical behavior
- Detecting long-term degradation trends
- Producing probabilistic risk assessments

Its outputs are advisory and are consumed by the fog layer and backend services.

---

## Core Responsibilities

- Training models using historical vehicle health vectors
- Performing inference for anomaly probability and degradation trends
- Estimating Remaining Useful Life (RUL) for critical components
- Refining models based on accumulated fleet-level data

---

## Inputs

The AI model layer consumes **preprocessed, semantic data** rather than raw sensor streams. Typical inputs include:

- Thermal stress indices
- Electrical health metrics
- Vibration and mechanical indicators
- Driver behavior influence factors
- Aggregated health vectors over time

Example input vector:

```json
{
  "thermal_stress_index": 0.82,
  "brake_health_index": 0.39,
  "vibration_anomaly_score": 0.77,
  "driver_aggression_score": 0.58
}
```

---

## Outputs

Model outputs are probabilistic and predictive in nature, including:

- Anomaly likelihood scores
- Component degradation trends
- Remaining Useful Life (RUL) estimates
- Risk classification labels

### Example Output

```json
{
  "brake_rul_pct": 28,
  "engine_rul_pct": 62,
  "battery_rul_pct": 74,
  "failure_probability_7d": 0.61
}
```

---

## Model Scope

The AI model layer may include:

- Statistical models for long-term trend analysis
- Machine learning classifiers for anomaly detection
- Regression models for lifecycle estimation
- Lightweight inference models for edge or fog deployment

Training and evaluation are typically performed in cloud or offline environments, while inference models may be optimized for deployment at the fog layer.

---

## Non-Responsibilities

The AI model layer explicitly does **not**:

- Capture or preprocess raw sensor signals
- Define safety thresholds or decision rules
- Trigger actuation or control actions
- Manage real-time system state

These responsibilities are owned by the fog module.

---

## Execution Environment

- Model training and evaluation in cloud or offline environments
- Optional lightweight inference deployment (for example, TensorFlow Lite)
- Non-real-time execution requirements

---

## Design Principles

- Prediction over control
- Probabilistic insight over deterministic action
- Semantic feature learning over raw signal processing
- Advisory intelligence, not authority

---

## Summary

The AI model layer enhances the system with **predictive and anticipatory intelligence**, enabling early fault detection and condition-based maintenance while leaving real-time safety decisions to the fog module.
