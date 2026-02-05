# ESP32 Hardware Layer

## Overview

The ESP32 hardware layer represents the **vehicle-embedded sensing and actuation interface** of the Fog-Based Vehicle Monitoring System. It is responsible for reliable acquisition of physical signals from the vehicle and for executing low-level actuator commands when instructed by the fog module.

This layer is intentionally kept **simple, deterministic, and interpretation-free**.

---

## Role in the System

The ESP32 functions as the **physical interface to reality**. It converts real-world vehicle signals into digital measurements and forwards them upstream without applying system-level interpretation or decision logic.

All safety decisions and control policies are defined outside this layer.

---

## Core Responsibilities

- Interfacing with vehicle sensors (thermal, electrical, motion, vibration)
- Performing analog-to-digital conversion (ADC)
- Applying basic signal conditioning and noise filtering
- Time-stamping measurements
- Transmitting structured telemetry to the fog module
- Executing actuator or relay commands issued by the fog module

---

## Typical Outputs

The ESP32 produces **raw or lightly processed measurements** suitable for upstream analysis.

Example output:

```json
{
  "engine_temp_c": 92.4,
  "brake_temp_c": 185.6,
  "battery_voltage_v": 12.6,
  "gyro_z_dps": 0.98,
  "timestamp": 1707051123456
}
```

---

## Communication

- Sends telemetry to the fog module over network or serial interfaces
- Receives explicit actuation commands from the fog module
- Does not communicate directly with cloud or frontend components

---

## Non-Responsibilities

The ESP32 hardware layer explicitly does **not**:

- Interpret sensor data
- Detect faults or anomalies
- Define thresholds or safety rules
- Make control or actuation decisions
- Perform machine learning or inference
- Store long-term data

All higher-level intelligence resides in the fog and AI layers.

---

## Execution Environment

- Runs on ESP32 microcontroller hardware
- Designed for real-time, deterministic execution
- Operates under constrained CPU, memory, and power budgets
- Optimized for continuous operation in vehicular environments

---

## Design Principles

- Accurate measurement over interpretation
- Deterministic timing over complex logic
- Simplicity for reliability
- Obedience to upstream control authority

---

## Summary

The ESP32 hardware layer provides a **reliable, deterministic bridge between physical vehicle systems and higher-level intelligence**, ensuring accurate sensing and faithful execution of control commands without embedding system logic at the hardware level.
