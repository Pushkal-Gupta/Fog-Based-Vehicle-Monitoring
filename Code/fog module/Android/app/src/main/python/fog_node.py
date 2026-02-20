import time
import requests
import threading
from collections import deque
from statistics import mean, variance

# ============================================================
# CONFIG
# ============================================================

SAMPLE_PERIOD = 0.025
WINDOW_SEC = 1.0
MAX_SAMPLES = int(WINDOW_SEC / SAMPLE_PERIOD)

BRAKE_MAX_TEMP = 220.0
MAX_SAFE_RISE = 6.0

ESP32_IP = "10.213.19.38"
CLOUD_URL = "https://fog-based-vehicle-monitoring.onrender.com/api/intelligence/insert"

# ============================================================
# UTILS
# ============================================================

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# ============================================================
# BUFFER
# ============================================================

class TelemetryBuffer:
    def __init__(self):
        self.samples = deque(maxlen=MAX_SAMPLES)

    def push(self, sample):
        if sample:
            self.samples.append(sample)

    def full(self):
        return len(self.samples) == MAX_SAMPLES

    def all(self):
        return list(self.samples)


# ============================================================
# AGGREGATION
# ============================================================

def aggregate(samples):
    s = lambda k: [x[k] for x in samples]
    last = samples[-1]

    t0 = samples[0]["timestamp_ms"]
    t1 = samples[-1]["timestamp_ms"]
    dt = (t1 - t0) / 1000.0 if t1 != t0 else 1.0

    rpm_series = s("motor_rpm")

    return {
        "device_id": last["device_id"],
        "vehicle_id": last["vehicle_id"],
        "timestamp_ms": t1,

        "brake_temp_c": max(s("brake_temp_c")),
        "brake_temp_rise_rate": (samples[-1]["brake_temp_c"] - samples[0]["brake_temp_c"]) / dt,

        "engine_oil_temp_c": mean(s("engine_oil_temp_c")),

        "motor_rpm": mean(rpm_series),
        "engine_rpm_variance": variance(rpm_series) if len(rpm_series) > 1 else 0,

        "vibration_rms": (sum(v*v for v in s("vibration_rms"))/len(samples))**0.5,
        "dominant_vibration_hz": mean(s("dominant_vibration_hz")),

        "battery_voltage_v": mean(s("battery_voltage_v")),
        "output_voltage_v": mean(s("output_voltage_v")),
        "battery_health_pct": last["battery_health_pct"],

        "engine_rul_pct": last["engine_rul_pct"],
        "brake_rul_pct": last["brake_rul_pct"],
        "battery_rul_pct": last["battery_rul_pct"],

        "brake_pad_remaining_pct": last["brake_pad_remaining_pct"],
        "brake_disc_score": last["brake_disc_score"]
    }


# ============================================================
# HEALTH MODEL
# ============================================================

def compute_health(d):

    thermal_stress = clamp(
        0.7*(d["brake_temp_c"]/BRAKE_MAX_TEMP) +
        0.3*(d["brake_temp_rise_rate"]/MAX_SAFE_RISE)
    )

    brake_health = clamp(
        0.6*(d["brake_pad_remaining_pct"]/100) +
        0.4*d["brake_disc_score"]
    )

    vehicle_health = (
            0.35*(d["engine_rul_pct"]/100)+
            0.45*(d["brake_rul_pct"]/100)+
            0.20*(d["battery_rul_pct"]/100)
    )
    vehicle_health *= (1-0.4*thermal_stress)

    expected_band = d["motor_rpm"]/60 if d["motor_rpm"] else 1
    vibration_ratio = d["dominant_vibration_hz"]/expected_band
    vibration_risk = clamp(0.7*(vibration_ratio/2.5)+0.3*(d["vibration_rms"]/1.2))

    thermal_protection = (
            d["brake_temp_c"]>180 and
            d["brake_temp_rise_rate"]>3 and
            brake_health<0.4
    )

    emergency = clamp(
        0.4*thermal_stress + 0.3*vibration_risk + 0.3*(1-vehicle_health)
    ) > 0.85

    actuation = thermal_protection or emergency

    return {
        "thermal_stress": thermal_stress,
        "brake_health": brake_health,
        "vehicle_health": vehicle_health,
        "thermal_protection": thermal_protection,
        "emergency": emergency,
        "actuation": actuation,
        "confidence": round(0.6+0.4*thermal_stress,2)
    }


# ============================================================
# PACKETS
# ============================================================

def build_actuation_packet(d,h):

    return {
        "timestamp_ms": d["timestamp_ms"],
        "decision_origin": "fog_node",
        "cloud_dependency": False,

        "trigger_measured_brake_temp_c": d["brake_temp_c"],
        "trigger_brake_temp_rise_rate": d["brake_temp_rise_rate"],
        "trigger_brake_health_index": h["brake_health"],

        "fog_decision_critical_class": int(h["thermal_protection"]),
        "fog_decision_actuation_triggered": int(h["actuation"]),
        "fog_decision_confidence": h["confidence"],

        "fog_thermal_protection_active": h["thermal_protection"],
        "fog_brake_stress_mitigation_active": h["thermal_protection"],
        "fog_vibration_damping_mode_active": h["emergency"],
        "fog_predictive_service_required": h["vehicle_health"] < 0.5,
        "fog_emergency_safeguard_active": h["emergency"]
    }

def build_cloud_packet(d, h):

    brake_margin = clamp((BRAKE_MAX_TEMP - d["brake_temp_c"]) / BRAKE_MAX_TEMP)
    engine_margin = clamp((140 - d["engine_oil_temp_c"]) / 140)

    charging_efficiency = clamp(d["output_voltage_v"] / d["battery_voltage_v"]) if d["battery_voltage_v"] else 0

    expected_band = d["motor_rpm"]/60 if d["motor_rpm"] else 1
    vibration_ratio = d["dominant_vibration_hz"]/expected_band
    vibration_anomaly = clamp(vibration_ratio/2.5)

    return {
        "vehicle_id": d["vehicle_id"],
        "timestamp_ms": d["timestamp_ms"],

        "thermal_brake_margin": brake_margin,
        "thermal_engine_margin": engine_margin,
        "thermal_stress_index": h["thermal_stress"],

        "mechanical_vibration_anomaly_score": vibration_anomaly,
        "mechanical_dominant_fault_band_hz": d["dominant_vibration_hz"],
        "mechanical_vibration_rms": d["vibration_rms"],

        "electrical_charging_efficiency_score": charging_efficiency,
        "electrical_battery_health_pct": d["battery_health_pct"],

        "engine_rul_pct": d["engine_rul_pct"],
        "brake_rul_pct": d["brake_rul_pct"],
        "battery_rul_pct": d["battery_rul_pct"],

        "vehicle_health_score": h["vehicle_health"]
    }

# ============================================================
# NETWORK
# ============================================================

def get_data_from_esp32():
    try:
        return requests.get(f"http://{ESP32_IP}/data", timeout=0.3).json()
    except:
        return None

def send_to_esp32(pkt):
    try:
        requests.put(f"http://{ESP32_IP}/actuate", json=pkt, timeout=0.3)
    except:
        pass

def send_to_backend(pkt):
    try:
        r = requests.post(CLOUD_URL, json=pkt, timeout=2)
        if r.status_code != 200:
            print("Cloud rejected:", r.status_code, r.text[:120])
    except Exception as e:
        print("Cloud send failed:", e)

# ============================================================
# MAIN LOOP
# ============================================================

def main_loop():

    buffer=TelemetryBuffer()
    next_tick=time.monotonic()
    last_cloud=time.monotonic()

    while True:

        raw=get_data_from_esp32()
        buffer.push(raw)

        if buffer.full():

            agg=aggregate(buffer.all())
            health=compute_health(agg)

            # ---- ACTUATION PATH ----
            if health["actuation"]:
                send_to_esp32(build_actuation_packet(agg,health))
                send_to_backend(build_cloud_packet(agg,health))
                last_cloud=time.monotonic()

            # ---- NORMAL TELEMETRY ----
            elif time.monotonic()-last_cloud>=1:
                send_to_backend(build_cloud_packet(agg,health))
                last_cloud=time.monotonic()

        next_tick+=SAMPLE_PERIOD
        sleep=next_tick-time.monotonic()
        if sleep>0:
            time.sleep(sleep)


def run():
    threading.Thread(target=main_loop, daemon=True).start()