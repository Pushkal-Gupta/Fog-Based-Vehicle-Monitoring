# Fog Module

## Overview

The fog module is the **core intelligence and decision-making layer** of the Fog-Based Vehicle Monitoring System. It operates between the embedded hardware layer and the cloud, executing real-time computation, system health evaluation, and autonomous safety actions with minimal latency.

This module is designed to function **independently of cloud connectivity**, ensuring continuous vehicle protection under network degradation or complete disconnection.

---

## Role in the System

The fog module acts as the **local reflex engine** of the vehicle. While the cloud provides long-term analytics and learning, the fog module is responsible for **immediate interpretation and action**.

It is the only layer in the system that:

- Correlates multi-domain vehicle signals
- Determines safety-critical conditions
- Triggers protective or corrective actions locally

---

## Core Responsibilities

- Receiving structured telemetry from the ESP32 hardware layer
- Performing feature extraction and signal analysis
- Constructing compact vehicular health vectors
- Evaluating safety and fault conditions using multi-parameter logic
- Executing autonomous actuation decisions
- Managing operational modes based on network latency and availability

---

## Data Processing Pipeline

1. **Input Reception**  
   Receives timestamped sensor measurements from the hardware layer.

2. **Feature Extraction**  
   Computes statistical and spectral features such as:
   - RMS and variance
   - FFT-based harmonic components
   - Rate-of-change metrics
   - Vibration and thermal indicators

3. **Health Vector Construction**  
   Transforms raw features into semantic health indices representing the state of vehicle subsystems.

4. **Decision Logic**  
   Applies rule-based and model-assisted evaluation to classify system state.

5. **Actuation and Reporting**  
   Executes local actions and generates summarized events for downstream layers.

---

## Example Health Vector

```json
{
  "thermal_stress_index": 0.82,
  "brake_health_index": 0.39,
  "vibration_anomaly_score": 0.77,
  "driver_aggression_score": 0.58,
  "vehicle_health_score": 0.64,
  "alert_level": "critical"
}
```

---

## Safety and Decision Logic

Decisions within the fog module are not based on single thresholds. Instead, the system evaluates **correlated conditions across multiple domains** to determine system state and severity.

The evaluation considers:

- Absolute parameter violations
- Rate-of-change anomalies
- Component degradation levels
- Cross-domain amplification effects (for example, driver behavior combined with thermal rise)

When predefined safety conditions are met, the fog module classifies the severity of the event and initiates the appropriate response.

---

## Autonomous Actuation

Based on the evaluated severity, the fog module may issue autonomous control commands such as:

- Vehicle speed limitation
- Brake cooling activation
- Suppression of aggressive braking
- Immediate driver alerts

All actions are executed **locally at the fog layer**, without waiting for cloud confirmation, ensuring deterministic response times.

---

## Operating Modes

### Cloud-Connected Mode

Normal operating state with periodic synchronization of health vectors, events, and summaries to the cloud.

### Survival Mode

Activated when network latency exceeds acceptable limits or connectivity is lost.  
In this mode, all inference, decision-making, and actuation continue locally without external dependency.

---

## Non-Responsibilities

The fog module explicitly does **not**:

- Capture raw physical sensor signals
- Train machine learning models
- Provide user-facing visualization
- Perform long-term data storage

These responsibilities are handled by other system layers.

---

## Execution Environment

- Runs on edge-adjacent compute platforms (for example, Raspberry Pi or vehicle gateways)
- Designed for low-latency, deterministic execution
- Optimized for continuous operation in resource-constrained environments

---

## Design Principles

- Local-first intelligence
- Deterministic response over probabilistic delay
- Semantic data over raw telemetry
- Safety before analytics

---

## Summary

The fog module transforms vehicle monitoring from a cloud-dependent observer into a **self-reliant, safety-aware system** capable of real-time decision-making under all network conditions.
