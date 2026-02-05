# Proposed Tech Stack

This document outlines the proposed technology stack for the **Fog-Based Vehicle Monitoring System**, aligned with the system’s layered architecture and responsibility separation.

---

## 1. Hardware & Embedded Layer (`hardware_esp32`)

**Purpose:** Physical signal acquisition and low-level actuation

- **Microcontroller:** ESP32
- **Firmware Language:** C / C++ (Arduino / ESP-IDF)
- **Sensors:**
  - Thermal (engine, brake, radiator)
  - Electrical (battery voltage, current)
  - Motion & vibration (IMU / gyroscope)
- **Interfaces:** I2C, SPI, GPIO, ADC
- **Actuation:** Relays / GPIO-controlled actuators

**Role:**  
This layer captures real-world vehicle signals and executes actuation commands issued by the fog layer. It performs no interpretation or decision-making.

---

## 2. Communication Layer

**Purpose:** Reliable data transfer from vehicle to fog node

- **Protocol:** MQTT
- **Broker:** Eclipse Mosquitto
- **Data Format:** JSON (schema-defined telemetry and health packets)

**Role:**  
Ensures lightweight, fault-tolerant communication under intermittent connectivity conditions.

---

## 3. Fog Layer (`fog_module`)

### Fog Node Implementation: **Mobile Phone–Based Fog Computing**

**Purpose:** Real-time intelligence, safety decision-making, and autonomous actuation

Instead of a dedicated edge device (such as a Raspberry Pi), the fog layer is implemented on a **mobile phone inside the vehicle**.

---

### Conceptual Idea

**Every vehicle occupant already carries a powerful computing device: a smartphone.**  
This system leverages that fact by using a mobile phone as the **vehicular fog node**.

The phone acts as a **local reflex engine**, executing safety-critical logic close to the vehicle without relying on cloud connectivity.

---

### How It Works

1. **ESP32 collects sensor data** from the vehicle.
2. **Telemetry is transmitted via MQTT** over Wi-Fi hotspot or Bluetooth.
3. **A mobile application (Android)** running on the phone receives this data.
4. The phone executes:
   - Feature extraction (FFT, RMS, rate-of-change)
   - Health vector construction
   - Safety and fault decision logic
5. **Actuation commands** are sent back to the ESP32 when required.
6. Health summaries are synchronized to the cloud when connectivity permits.

---

### Why a Mobile Phone Works as a Fog Node

- Multi-core CPUs with sufficient processing power
- Built-in networking (Wi-Fi, LTE, 5G)
- Battery-backed power (continues operating when vehicle power fluctuates)
- Always present inside the vehicle
- No additional hardware cost

---

### Fog Layer Tech Stack (Mobile)

- **Platform:** Android Smartphone
- **Language:** Python (via service layer) or Kotlin/Java
- **Libraries:**
  - NumPy, SciPy – signal processing
  - Pandas – health vector handling
- **AI Inference:** TensorFlow Lite (optional)
- **Communication:** MQTT client
- **Operating Modes:**
  - Cloud-connected mode
  - Survival (offline) mode

**Role:**  
The fog layer is the **only layer allowed to decide and act**.

---

## 4. AI / Machine Learning Layer (`ai_model`)

**Purpose:** Predictive intelligence and lifecycle estimation

- **Frameworks:**
  - Scikit-learn
  - TensorFlow / TensorFlow Lite
- **Model Types:**
  - Anomaly detection classifiers
  - Regression models for RUL estimation
- **Training:** Cloud or offline environments
- **Inference:** Cloud or fog (mobile phone)

**Role:**  
Provides probabilistic predictions and degradation trends. Does not control actuation.

---

## 5. Backend Layer (`backend`)

**Purpose:** Data persistence, APIs, and long-term analytics

- **Framework:** FastAPI or Flask
- **Database:** MongoDB (Atlas or local)
- **APIs:** REST / WebSocket

**Role:**  
Stores health vectors, events, and analytics data for visualization and reporting.

---

## 6. Frontend Layer (`frontend`)

**Purpose:** Visualization and system observability

- **Framework:** React.js
- **Visualization:** Chart.js / Recharts
- **Real-Time Updates:** WebSockets
- **Hosting:** Vercel / Netlify

**Role:**  
Displays vehicle health and alerts. No control authority.

---

## 7. DevOps & Tooling

- **Version Control:** Git, GitHub
- **Containerization:** Docker (fog backend, cloud services)
- **Dependency Management:** `requirements.txt`
- **Testing:**
  - Simulated sensor streams
  - MQTT test clients

---

## Architectural Philosophy

- Hardware measures reality
- Mobile fog decides and acts
- AI predicts and advises
- Backend stores and serves
- Frontend visualizes

---

## Summary

Using a **mobile phone as the fog node** transforms the system into a **hardware-minimal, cost-effective, and highly deployable architecture**. It enables real-time, autonomous vehicle intelligence without additional edge hardware, while preserving strict separation of responsibilities across layers.
