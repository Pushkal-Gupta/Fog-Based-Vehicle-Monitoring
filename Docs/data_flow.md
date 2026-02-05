# System Data Flow and Authority Separation

This document describes the **end-to-end data flow** in the Fog-Based Vehicle Monitoring System and clearly defines **where decisions are made, where intelligence runs, and what data is shared across system boundaries**.

The architecture is intentionally divided into two independent paths:

1. A **safety-critical local path** (fog-only)
2. An **analytics and visibility path** (cloud-only)

---

## 1. Safety-Critical Path (Local, Fog-Only)

This path handles **real-time safety decisions** and **physical actuation**.  
All computation in this path is **local, deterministic, and latency-bounded**.

```text
Hardware Dataset (Section 1)
        ↓
Fog Health Vectors (Section 2)
        ↓
Fog Binary Safety Classifier
        ↓
Actuation Dataset (Section 5)
        ↓
Hardware (ESP32)
```

### Key Characteristics

- Executes entirely at the fog layer

- Contains the only model allowed to trigger actuation

- Operates without cloud dependency

- Optimized for deterministic response time

### Authority

- The fog node has full authority over safety decisions

- The cloud has no visibility or control over this path

---

## 2. Analytics and Visibility Path (Cloud-Only)

This path supports **long-term analytics, prediction, and visualization**.  
It is **non-safety-critical** and does not participate in actuation.

```text
Hardware Dataset
        ↓
Fog Health Vectors
        ↓
Processed Health + AI Output (Section 6)
        ↓
Cloud
        ↓
Recommendation Engine
        ↓
Dashboard
```

### Key Characteristics

- Receives only processed, fog-curated data

- No raw or intermediate fog data is exposed

- Used for predictive modeling and advisory outputs

- Latency-tolerant and non-authoritative

---

## 3. Dataset Boundary Rules

The system enforces **strict dataset boundaries** to preserve safety, clarity, and authority separation across layers.

### Guaranteed Invariants

- Only **Section 6** is transmitted to the cloud
- Only **one AI-like model** exists at the fog layer
- The cloud **never receives Section 2 directly**
- No cloud model can **trigger actuation**
- All physical control **originates at the fog**

---

## 4. Architectural Implications

This separation ensures:

- Deterministic safety behavior
- Reduced attack surface
- Clear responsibility boundaries
- Explainable system behavior
- Compliance with safety-aware **cyber-physical system (CPS)** design principles

The fog acts as a **trusted execution boundary**, while the cloud functions as a **pure analytics and advisory layer**.

---

## 5. Summary

- Safety-critical reasoning is **local and fog-only**
- Cloud receives **only processed analytics data**
- Actuation is **never cloud-driven**
- Predictive intelligence and recommendations are **advisory only**

This design guarantees that **real-time safety decisions remain independent of network conditions and cloud availability**, while still enabling advanced analytics and system observability.
