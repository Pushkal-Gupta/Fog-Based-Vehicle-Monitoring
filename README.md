# Fog-Based Vehicle Monitoring System

---

## Technical Domain

This project belongs to the domain of **vehicular cyber-physical systems (CPS)**, integrating embedded sensing, fog computing, and cloud-assisted intelligence to enable real-time vehicle health monitoring, safety decision-making, and predictive maintenance.

The system follows a layered **edge–fog–cloud architecture**, with explicit emphasis on **low-latency, safety-critical intelligence executed locally** rather than relying solely on remote cloud infrastructure.

---

## Motivation and Problem Context

Modern vehicles continuously generate high-frequency telemetry data such as thermal states, mechanical vibration, electrical load behavior, and driver interaction patterns. While existing connected-vehicle platforms collect this data effectively, they suffer from fundamental architectural limitations.

Cloud-centric processing introduces unavoidable **latency**, which is unacceptable for fast-evolving mechanical or thermal faults such as brake overheating, bearing degradation, or electrical instability. Continuous transmission of raw telemetry also leads to excessive bandwidth usage, high operational cost, and poor scalability. Most critically, when connectivity degrades or disappears entirely, cloud-dependent systems lose their ability to react—leaving vehicles unprotected exactly when intelligent response is required.

This project addresses these gaps by relocating **decision authority closer to the vehicle**, enabling autonomous, deterministic responses even under poor or zero network connectivity.

---

## System Overview

The Fog-Based Vehicle Monitoring System introduces a **hierarchical intelligence model** inspired by biological reflex mechanisms. Just as the human nervous system executes reflex actions locally before involving the brain, this system performs immediate safety decisions at the fog layer while reserving the cloud for long-term learning and analytics.

At a high level, the system:

- Continuously monitors vehicle subsystems through embedded sensing
- Computes compact, meaningful health representations locally
- Executes safety and protection logic without cloud dependency
- Synchronizes summarized state information with the cloud when available

---

## Architectural Layers

### 1. Edge Layer (Vehicle-Embedded Hardware)

The edge layer consists of an ESP32-based embedded node interfaced with vehicle sensors. Its responsibilities include:

- Capturing raw physical signals (thermal, electrical, mechanical, motion)
- Performing basic filtering and signal conditioning
- Time-stamping and forwarding structured measurements to the fog layer

This layer is intentionally kept lightweight and deterministic, focusing solely on faithful signal acquisition.

---

### 2. Fog Layer (Vehicular Fog Node)

The fog layer is the **core intelligence layer** of the system. It performs real-time computation and decision-making with millisecond-level responsiveness. Key responsibilities include:

- Feature extraction such as RMS values, FFT-based spectral analysis, variance, and rate-of-change metrics
- Construction of **vehicular health vectors** representing subsystem state rather than raw data
- Evaluation of safety conditions using multi-parameter logic
- Autonomous actuation decisions during critical events

The fog node remains fully operational even during network outages, ensuring continuous protection and monitoring.

---

### 3. Cloud Layer (Analytics and Learning)

The cloud layer serves as a non-critical, supplementary intelligence tier. Its functions include:

- Long-term storage of health vectors and event summaries
- Training and refinement of predictive models
- Fleet-level trend analysis and anomaly aggregation
- Supporting dashboards and historical insights

The cloud is **never in the critical decision path** for safety actions.

---

### 4. Visualization Layer (Digital Twin Interface)

The visualization layer provides real-time insight into vehicle state through a digital twin representation. It displays:

- Live subsystem health indicators
- Alerts and fault explanations
- Maintenance recommendations and degradation trends

This layer has no authority over actuation or safety logic and functions purely as an observational interface.

---

## Health Vectorization Concept

Rather than streaming high-frequency raw telemetry, the system computes **compact health vectors** at the fog layer. These vectors encode the essential state of vehicle subsystems, including:

- Thermal stress indices
- Brake and powertrain health scores
- Electrical charging and battery condition
- Vibration and mechanical anomaly indicators
- Driver behavior influence factors

This approach significantly reduces transmitted data volume while preserving all information necessary for decision-making and analytics.

---

## Autonomous Safety and Control Logic

Safety decisions are derived from **correlated multi-signal evaluation**, not isolated thresholds. The system considers:

- Absolute parameter limits
- Rate-of-change anomalies
- Component degradation levels
- Cross-domain interactions (for example, driver behavior amplifying thermal stress)

When critical conditions are detected, the fog node can initiate actions such as:

- Vehicle speed limitation
- Brake cooling activation
- Suppression of aggressive braking
- Immediate driver alerts

All actions are executed locally with deterministic latency.

---

## Predictive Maintenance and Lifecycle Estimation

Beyond immediate safety response, the system continuously estimates the **Remaining Useful Life (RUL)** of critical components. Unlike static service intervals, RUL is derived from observed degradation patterns, enabling:

- Early fault detection
- Condition-based maintenance
- Reduced unplanned downtime

This shifts vehicle maintenance from reactive intervention to predictive planning.

---

## Example Operational Scenario

In a brake overheating scenario:

1. Edge sensors detect elevated temperature and abnormal rise rate
2. Fog layer computes thermal stress and brake health indices
3. Multi-condition logic classifies the situation as critical
4. Local actuation is triggered to limit speed and enable cooling
5. Event summary is logged and synchronized to the cloud when available

Total response time remains within milliseconds, independent of network state.

---

## Key Advantages

- Deterministic safety response without cloud reliance
- Resilience to network latency and outages
- Significant reduction in transmitted data volume
- Scalable across vehicle types and powertrains
- Enables intelligent, condition-based maintenance

---

## Implementation Status

- Vehicle-integrated ESP32 edge prototype
- Fully functional fog middleware with autonomous decision logic
- Cloud backend for analytics and long-term storage
- Live digital twin dashboard for visualization

---

## Intended Applications

- Passenger and commercial vehicles
- Fleet monitoring platforms
- Smart transportation infrastructure
- Advanced driver-assistance research
- Predictive after-sales maintenance systems

---

## Disclaimer

This repository is provided for academic, research, and experimental purposes. The system architecture, algorithms, and workflows presented here represent original engineering work. Unauthorized commercial use, redistribution, or deployment may be subject to applicable intellectual property and regulatory considerations.

---

## Short Description

A fog-enabled vehicular monitoring system enabling real-time safety decisions and predictive maintenance through local intelligence and cloud-assisted analytics.
