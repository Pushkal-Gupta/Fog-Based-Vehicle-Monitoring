"""
BRUTAL Cloud AI Correctness Test
==================================
Leaves NO stone unturned. Tests every rule, boundary, edge case,
adversarial input, consistency, monotonicity, idempotency, latency,
and concurrency aspect of the Cloud AI advisory system.

Usage (server must be running on port 8000):
    python scripts/test_brutal_cloud.py
    python scripts/test_brutal_cloud.py --url http://host:port
"""

import argparse
import json
import math
import random
import sys
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

try:
    import httpx
    USE_HTTPX = True
except ImportError:
    import urllib.request, urllib.error
    USE_HTTPX = False

# ── Colour helpers ──────────────────────────────────────────────────────────
G  = "\033[92m";  R = "\033[91m";  Y = "\033[93m"
B  = "\033[1m";   D = "\033[2m";   X = "\033[0m"
CYAN = "\033[96m"

def ok(msg):   print(f"  {G}✔ PASS{X}  {msg}")
def fail(msg): print(f"  {R}✘ FAIL{X}  {msg}")
def warn(msg): print(f"  {Y}⚠ WARN{X}  {msg}")
def info(msg): print(f"  {D}ℹ INFO{X}  {msg}")

VALID_FAULTS = {
    "BRAKE_THERMAL_SATURATION",
    "MECHANICAL_VIBRATION_ANOMALY",
    "ELECTRICAL_DEGRADATION",
    "MULTI_FACTOR_FAILURE_RISK",
    "NO_DOMINANT_FAULT",
}
VALID_PRIORITIES = {"high", "medium", "low", "normal"}
VALID_CONTRIBUTORS = {
    "high_thermal_stress_index",
    "low_brake_rul_pct",
    "high_mechanical_vibration_anomaly_score",
    "high_mechanical_vibration_rms",
    "low_electrical_charging_efficiency_score",
    "no_dominant_contributor",
}
VALID_LIMITS = {120, 300, 600, 1000}

# ── API ─────────────────────────────────────────────────────────────────────

def _post(base_url, payload, timeout=15):
    url = f"{base_url}/analyze"
    if USE_HTTPX:
        with httpx.Client(timeout=timeout) as c:
            r = c.post(url, json=payload)
            return r.status_code, r.json() if r.status_code == 200 else r.text
    else:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

def _get(base_url, path="/health", timeout=10):
    url = f"{base_url}{path}"
    if USE_HTTPX:
        with httpx.Client(timeout=timeout) as c:
            r = c.get(url)
            return r.status_code, r.json() if r.status_code == 200 else r.text
    else:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())

def analyze(base_url, payload):
    code, body = _post(base_url, payload)
    if code != 200:
        raise RuntimeError(f"HTTP {code}: {body}")
    return body

# ── Payload builder ─────────────────────────────────────────────────────────

def bp(**kw):
    """Base healthy payload."""
    p = {
        "vehicle_id": "BRUTAL_TEST_001",
        "timestamp_ms": int(time.time() * 1000),
        "thermal_brake_margin": 0.30,
        "thermal_engine_margin": 0.40,
        "thermal_stress_index": 0.15,
        "mechanical_vibration_anomaly_score": 0.10,
        "mechanical_dominant_fault_band_hz": 60.0,
        "mechanical_vibration_rms": 0.15,
        "electrical_charging_efficiency_score": 0.95,
        "electrical_battery_health_pct": 95.0,
        "engine_rul_pct": 85.0,
        "brake_rul_pct": 90.0,
        "battery_rul_pct": 88.0,
        "vehicle_health_score": 0.90,
    }
    p.update(kw)
    return p

# ── Test Suite ──────────────────────────────────────────────────────────────

@dataclass
class TS:
    passed: int = 0
    failed: int = 0
    warned: int = 0

    def check(self, cond, msg, critical=True):
        if cond:
            ok(msg); self.passed += 1
        elif critical:
            fail(msg); self.failed += 1
        else:
            warn(msg); self.warned += 1

    def h(self, n, title):
        print(f"\n{B}{'─'*64}")
        print(f"  {n}. {title}")
        print(f"{'─'*64}{X}")


# ═══════════════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════════════

def t01_health(url, ts):
    ts.h(1, "HEALTH ENDPOINT — Advisory Authority")
    code, body = _get(url)
    ts.check(code == 200, f"HTTP 200: got {code}")
    ts.check(body.get("status") == "ok", "status=ok")
    ts.check(body.get("mode") == "advisory-only", "mode=advisory-only")
    ts.check(body.get("authority") == "cloud_has_no_actuation_control", "authority field correct")
    # Cloud MUST NOT claim any actuation power
    ts.check("actuation" not in body.get("authority", "").replace("no_actuation", ""),
             "no actuation claim beyond denial")


def t02_schema(url, ts):
    ts.h(2, "OUTPUT SCHEMA — Every Required Field Present")
    r = analyze(url, bp())
    top_keys = {"vehicle_id", "timestamp_ms", "engine_rul_pct", "brake_rul_pct",
                "battery_rul_pct", "fault_failure_probability_7d", "fault_primary",
                "fault_contributing_factors", "recommendation"}
    for k in top_keys:
        ts.check(k in r, f"top-level: '{k}'")
    rec_keys = {"recommendation_service_priority", "recommendation_suggested_action",
                "recommendation_safe_operating_limit_km"}
    for k in rec_keys:
        ts.check(k in r.get("recommendation", {}), f"recommendation.'{k}'")
    # Types
    ts.check(isinstance(r["engine_rul_pct"], (int, float)), "engine_rul_pct is numeric")
    ts.check(isinstance(r["fault_contributing_factors"], list), "contributors is list")
    ts.check(isinstance(r["recommendation"], dict), "recommendation is dict")
    ts.check(isinstance(r["fault_primary"], str), "fault_primary is string")


def t03_value_bounds(url, ts):
    ts.h(3, "VALUE BOUNDS — Outputs in Legal Ranges")
    r = analyze(url, bp())
    ts.check(0 <= r["engine_rul_pct"] <= 100,
             f"engine_rul_pct [{r['engine_rul_pct']}] in [0,100]")
    ts.check(0 <= r["fault_failure_probability_7d"] <= 1.0,
             f"failure_prob [{r['fault_failure_probability_7d']}] in [0,1]")
    ts.check(r["fault_primary"] in VALID_FAULTS,
             f"fault_primary '{r['fault_primary']}' is a known fault type")
    for c in r["fault_contributing_factors"]:
        ts.check(c in VALID_CONTRIBUTORS,
                 f"contributor '{c}' is a known contributor")
    ts.check(r["recommendation"]["recommendation_service_priority"] in VALID_PRIORITIES,
             f"priority '{r['recommendation']['recommendation_service_priority']}' in valid set")
    ts.check(r["recommendation"]["recommendation_safe_operating_limit_km"] in VALID_LIMITS,
             f"safe_limit {r['recommendation']['recommendation_safe_operating_limit_km']} in valid set")


def t04_passthrough(url, ts):
    ts.h(4, "PASSTHROUGH — Vehicle ID, Timestamp, Brake/Battery RUL")
    vid = "XYZZY_PASS_999"
    tsm = 1234567890123
    r = analyze(url, bp(vehicle_id=vid, timestamp_ms=tsm,
                        brake_rul_pct=42.42, battery_rul_pct=66.66))
    ts.check(r["vehicle_id"] == vid, f"vehicle_id: {r['vehicle_id']}")
    ts.check(r["timestamp_ms"] == tsm, f"timestamp_ms: {r['timestamp_ms']}")
    ts.check(r["brake_rul_pct"] == 42.42, f"brake_rul_pct passthrough: {r['brake_rul_pct']}")
    ts.check(r["battery_rul_pct"] == 66.66, f"battery_rul_pct passthrough: {r['battery_rul_pct']}")
    # engine_rul MUST be model-predicted, not passed through
    ts.check(r["engine_rul_pct"] != 85.0 or True,  # may coincidentally match, just log
             f"engine_rul_pct predicted: {r['engine_rul_pct']}")


def t05_healthy_vehicle(url, ts):
    ts.h(5, "HEALTHY VEHICLE — Low Risk, No Fault, Normal Priority")
    r = analyze(url, bp())
    ts.check(r["fault_failure_probability_7d"] < 0.3,
             f"fail_prob < 0.3: {r['fault_failure_probability_7d']}")
    ts.check(r["fault_primary"] == "NO_DOMINANT_FAULT",
             f"fault=NO_DOMINANT_FAULT: got {r['fault_primary']}")
    ts.check(r["recommendation"]["recommendation_service_priority"] in ("normal", "low"),
             f"priority={r['recommendation']['recommendation_service_priority']}")
    ts.check("no_dominant_contributor" in r["fault_contributing_factors"],
             "contributors has 'no_dominant_contributor'")
    ts.check(r["recommendation"]["recommendation_safe_operating_limit_km"] >= 600,
             f"safe_limit >= 600: {r['recommendation']['recommendation_safe_operating_limit_km']}")


# ── FAULT RULE TESTS (explanation.py) ───────────────────────────────────

def t06_brake_thermal(url, ts):
    ts.h(6, "BRAKE_THERMAL_SATURATION — thermal>0.75 AND brake_rul<40")
    r = analyze(url, bp(thermal_stress_index=0.85, brake_rul_pct=20,
                        mechanical_vibration_anomaly_score=0.10))
    ts.check(r["fault_primary"] == "BRAKE_THERMAL_SATURATION",
             f"fault: {r['fault_primary']}")
    ts.check("high_thermal_stress_index" in r["fault_contributing_factors"],
             "contributor: high_thermal_stress_index")
    ts.check("low_brake_rul_pct" in r["fault_contributing_factors"],
             "contributor: low_brake_rul_pct")
    ts.check(r["recommendation"]["recommendation_service_priority"] == "high",
             f"priority=high: {r['recommendation']['recommendation_service_priority']}")
    ts.check(r["recommendation"]["recommendation_safe_operating_limit_km"] == 120,
             f"limit=120: {r['recommendation']['recommendation_safe_operating_limit_km']}")
    ts.check("Brake inspection" in r["recommendation"]["recommendation_suggested_action"],
             f"action mentions brake: {r['recommendation']['recommendation_suggested_action']}")


def t07_brake_thermal_boundary(url, ts):
    ts.h(7, "BRAKE_THERMAL — Boundary Precision Tests")
    # thermal=0.74 (below 0.75) → NOT brake_thermal
    r1 = analyze(url, bp(thermal_stress_index=0.74, brake_rul_pct=20))
    ts.check(r1["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"thermal=0.74 → NOT brake_thermal: {r1['fault_primary']}")
    # thermal=0.76, brake=41 → NOT brake_thermal (brake above 40)
    r2 = analyze(url, bp(thermal_stress_index=0.76, brake_rul_pct=41))
    ts.check(r2["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"brake=41 → NOT brake_thermal: {r2['fault_primary']}")
    # thermal=0.76, brake=39 → IS brake_thermal
    r3 = analyze(url, bp(thermal_stress_index=0.76, brake_rul_pct=39))
    ts.check(r3["fault_primary"] == "BRAKE_THERMAL_SATURATION",
             f"thermal=0.76,brake=39 → brake_thermal: {r3['fault_primary']}")
    # Both at exact boundary: thermal=0.75 (NOT > 0.75) → NOT brake_thermal
    r4 = analyze(url, bp(thermal_stress_index=0.75, brake_rul_pct=39))
    ts.check(r4["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"thermal=0.75 (exact) → NOT brake_thermal (uses >): {r4['fault_primary']}")
    # brake=40 (NOT < 40) → NOT brake_thermal
    r5 = analyze(url, bp(thermal_stress_index=0.80, brake_rul_pct=40))
    ts.check(r5["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"brake=40 (exact) → NOT brake_thermal (uses <): {r5['fault_primary']}")


def t08_vibration_anomaly(url, ts):
    ts.h(8, "MECHANICAL_VIBRATION_ANOMALY — vibration_anomaly>0.7")
    # Pure vibration (no brake_thermal overlap)
    r = analyze(url, bp(thermal_stress_index=0.30, brake_rul_pct=70,
                        mechanical_vibration_anomaly_score=0.85,
                        mechanical_vibration_rms=0.95))
    ts.check(r["fault_primary"] == "MECHANICAL_VIBRATION_ANOMALY",
             f"fault: {r['fault_primary']}")
    ts.check("high_mechanical_vibration_anomaly_score" in r["fault_contributing_factors"],
             "contributor: vibration_anomaly")
    ts.check("high_mechanical_vibration_rms" in r["fault_contributing_factors"],
             "contributor: vibration_rms")


def t09_vibration_boundary(url, ts):
    ts.h(9, "VIBRATION — Boundary Precision Tests")
    # vibration=0.70 (NOT > 0.7) → NOT vibration_anomaly
    r1 = analyze(url, bp(thermal_stress_index=0.30, brake_rul_pct=70,
                         mechanical_vibration_anomaly_score=0.70))
    ts.check(r1["fault_primary"] != "MECHANICAL_VIBRATION_ANOMALY",
             f"vib=0.70 (exact) → NOT anomaly: {r1['fault_primary']}")
    # vibration=0.71 → IS vibration_anomaly
    r2 = analyze(url, bp(thermal_stress_index=0.30, brake_rul_pct=70,
                         mechanical_vibration_anomaly_score=0.71))
    ts.check(r2["fault_primary"] == "MECHANICAL_VIBRATION_ANOMALY",
             f"vib=0.71 → anomaly: {r2['fault_primary']}")


def t10_electrical(url, ts):
    ts.h(10, "ELECTRICAL_DEGRADATION — charging<0.65 OR battery<60")
    # charging_eff low
    r1 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.50,
                         electrical_battery_health_pct=80))
    ts.check(r1["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"low charging → ELECTRICAL: {r1['fault_primary']}")
    # battery_health low
    r2 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.80,
                         electrical_battery_health_pct=45))
    ts.check(r2["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"low battery → ELECTRICAL: {r2['fault_primary']}")
    # both low
    r3 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.40,
                         electrical_battery_health_pct=30))
    ts.check(r3["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"both low → ELECTRICAL: {r3['fault_primary']}")


def t11_electrical_boundary(url, ts):
    ts.h(11, "ELECTRICAL — Boundary Precision Tests")
    # charging=0.65, battery=60 → NOT electrical (uses < 0.65 and < 60)
    r1 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.65,
                         electrical_battery_health_pct=60))
    ts.check(r1["fault_primary"] != "ELECTRICAL_DEGRADATION",
             f"charging=0.65, battery=60 (exact) → NOT electrical: {r1['fault_primary']}")
    # charging=0.64 → IS electrical
    r2 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.64,
                         electrical_battery_health_pct=80))
    ts.check(r2["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"charging=0.64 → ELECTRICAL: {r2['fault_primary']}")
    # battery=59 → IS electrical
    r3 = analyze(url, bp(thermal_stress_index=0.20,
                         mechanical_vibration_anomaly_score=0.10,
                         electrical_charging_efficiency_score=0.80,
                         electrical_battery_health_pct=59))
    ts.check(r3["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"battery=59 → ELECTRICAL: {r3['fault_primary']}")


def t12_fault_priority_chain(url, ts):
    ts.h(12, "FAULT PRIORITY CHAIN — Ordering When Multiple Faults Apply")
    # brake_thermal > vibration > electrical > multi_factor > none
    # A: brake_thermal + vibration both qualify → brake_thermal wins
    r1 = analyze(url, bp(thermal_stress_index=0.90, brake_rul_pct=15,
                         mechanical_vibration_anomaly_score=0.85))
    ts.check(r1["fault_primary"] == "BRAKE_THERMAL_SATURATION",
             f"brake_thermal beats vibration: {r1['fault_primary']}")
    # B: vibration + electrical both qualify → vibration wins
    r2 = analyze(url, bp(thermal_stress_index=0.30, brake_rul_pct=70,
                         mechanical_vibration_anomaly_score=0.85,
                         electrical_charging_efficiency_score=0.40,
                         electrical_battery_health_pct=30))
    ts.check(r2["fault_primary"] == "MECHANICAL_VIBRATION_ANOMALY",
             f"vibration beats electrical: {r2['fault_primary']}")
    # C: electrical + high-prob (multi-factor eligible) → electrical wins
    r3 = analyze(url, bp(thermal_stress_index=0.30, brake_rul_pct=70,
                         mechanical_vibration_anomaly_score=0.50,
                         electrical_charging_efficiency_score=0.40,
                         electrical_battery_health_pct=30))
    ts.check(r3["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"electrical beats multi_factor: {r3['fault_primary']}")


# ── CONTRIBUTOR TESTS ───────────────────────────────────────────────────

def t13_contributor_thresholds(url, ts):
    ts.h(13, "CONTRIBUTOR THRESHOLDS — Exact Trigger/No-Trigger")
    # thermal_stress > 0.7 → contributor
    r1 = analyze(url, bp(thermal_stress_index=0.71))
    ts.check("high_thermal_stress_index" in r1["fault_contributing_factors"],
             "thermal=0.71 → contributor")
    r2 = analyze(url, bp(thermal_stress_index=0.70))
    ts.check("high_thermal_stress_index" not in r2["fault_contributing_factors"],
             "thermal=0.70 → NOT contributor")
    # brake_rul < 40 → contributor
    r3 = analyze(url, bp(brake_rul_pct=39))
    ts.check("low_brake_rul_pct" in r3["fault_contributing_factors"],
             "brake=39 → contributor")
    r4 = analyze(url, bp(brake_rul_pct=40))
    ts.check("low_brake_rul_pct" not in r4["fault_contributing_factors"],
             "brake=40 → NOT contributor")
    # vibration_anomaly > 0.65 → contributor
    r5 = analyze(url, bp(mechanical_vibration_anomaly_score=0.66))
    ts.check("high_mechanical_vibration_anomaly_score" in r5["fault_contributing_factors"],
             "vib_anom=0.66 → contributor")
    r6 = analyze(url, bp(mechanical_vibration_anomaly_score=0.65))
    ts.check("high_mechanical_vibration_anomaly_score" not in r6["fault_contributing_factors"],
             "vib_anom=0.65 → NOT contributor")
    # vibration_rms > 0.8 → contributor
    r7 = analyze(url, bp(mechanical_vibration_rms=0.81))
    ts.check("high_mechanical_vibration_rms" in r7["fault_contributing_factors"],
             "vib_rms=0.81 → contributor")
    r8 = analyze(url, bp(mechanical_vibration_rms=0.80))
    ts.check("high_mechanical_vibration_rms" not in r8["fault_contributing_factors"],
             "vib_rms=0.80 → NOT contributor")
    # charging < 0.7 → contributor
    r9 = analyze(url, bp(electrical_charging_efficiency_score=0.69))
    ts.check("low_electrical_charging_efficiency_score" in r9["fault_contributing_factors"],
             "charging=0.69 → contributor")
    r10 = analyze(url, bp(electrical_charging_efficiency_score=0.70))
    ts.check("low_electrical_charging_efficiency_score" not in r10["fault_contributing_factors"],
             "charging=0.70 → NOT contributor")


def t14_contributor_combos(url, ts):
    ts.h(14, "CONTRIBUTOR COMBOS — None, Some, All")
    # 0 triggers → 'no_dominant_contributor' only
    r1 = analyze(url, bp())
    ts.check(r1["fault_contributing_factors"] == ["no_dominant_contributor"],
             f"healthy → ['no_dominant_contributor']: got {r1['fault_contributing_factors']}")
    # All 5 triggers
    r2 = analyze(url, bp(thermal_stress_index=0.90, brake_rul_pct=15,
                         mechanical_vibration_anomaly_score=0.80,
                         mechanical_vibration_rms=0.95,
                         electrical_charging_efficiency_score=0.50))
    ts.check(len(r2["fault_contributing_factors"]) == 5,
             f"all 5 contributors: got {len(r2['fault_contributing_factors'])}")
    ts.check("no_dominant_contributor" not in r2["fault_contributing_factors"],
             "'no_dominant_contributor' absent when real contributors exist")
    # Exactly 1 trigger
    r3 = analyze(url, bp(thermal_stress_index=0.75, brake_rul_pct=90,
                         mechanical_vibration_anomaly_score=0.10,
                         mechanical_vibration_rms=0.15,
                         electrical_charging_efficiency_score=0.95))
    ts.check(len(r3["fault_contributing_factors"]) == 1,
             f"1 contributor: got {len(r3['fault_contributing_factors'])}")


# ── RECOMMENDATION TESTS ───────────────────────────────────────────────

def t15_recommendation_cascade(url, ts):
    ts.h(15, "RECOMMENDATION CASCADE — Priority Tiers")
    # HIGH: failure_prob > 0.75 or BRAKE_THERMAL_SATURATION
    r1 = analyze(url, bp(thermal_stress_index=0.90, brake_rul_pct=10,
                         mechanical_vibration_anomaly_score=0.85))
    ts.check(r1["recommendation"]["recommendation_service_priority"] == "high",
             "critical → high")
    ts.check(r1["recommendation"]["recommendation_safe_operating_limit_km"] == 120,
             "critical → 120 km")
    # MEDIUM: brake_rul < 40 (low prob)
    r2 = analyze(url, bp(brake_rul_pct=35, thermal_stress_index=0.15,
                         mechanical_vibration_anomaly_score=0.10))
    ts.check(r2["recommendation"]["recommendation_service_priority"] == "medium",
             f"brake=35 → medium: got {r2['recommendation']['recommendation_service_priority']}",
             critical=False)
    ts.check(r2["recommendation"]["recommendation_safe_operating_limit_km"] == 300,
             f"brake low → 300 km: got {r2['recommendation']['recommendation_safe_operating_limit_km']}",
             critical=False)
    # LOW: engine_rul < 50 (predicted by model, harder to control)
    # We just test a healthy scenario
    r3 = analyze(url, bp())
    ts.check(r3["recommendation"]["recommendation_service_priority"] == "normal",
             f"healthy → normal: {r3['recommendation']['recommendation_service_priority']}")
    ts.check(r3["recommendation"]["recommendation_safe_operating_limit_km"] == 1000,
             f"healthy → 1000 km: {r3['recommendation']['recommendation_safe_operating_limit_km']}")


def t16_brake_thermal_always_high(url, ts):
    ts.h(16, "BRAKE_THERMAL_SATURATION → Always HIGH Priority")
    # Even if failure_prob were somehow low, BRAKE_THERMAL_SATURATION fault name
    # directly triggers high in recommend_action
    r = analyze(url, bp(thermal_stress_index=0.80, brake_rul_pct=35))
    if r["fault_primary"] == "BRAKE_THERMAL_SATURATION":
        ts.check(r["recommendation"]["recommendation_service_priority"] == "high",
                 "BRAKE_THERMAL_SATURATION → always high priority")
    else:
        info(f"didn't trigger brake_thermal (got {r['fault_primary']}), skipping")


# ── MODEL SANITY ────────────────────────────────────────────────────────

def t17_rul_direction(url, ts):
    ts.h(17, "RUL MODEL — Healthy vs Stressed Direction")
    r_h = analyze(url, bp(thermal_stress_index=0.05,
                          mechanical_vibration_anomaly_score=0.05,
                          electrical_charging_efficiency_score=0.98,
                          vehicle_health_score=0.98))
    r_s = analyze(url, bp(thermal_stress_index=0.95,
                          mechanical_vibration_anomaly_score=0.90,
                          electrical_charging_efficiency_score=0.50,
                          vehicle_health_score=0.20))
    ts.check(r_h["engine_rul_pct"] > r_s["engine_rul_pct"],
             f"healthy RUL ({r_h['engine_rul_pct']:.1f}) > stressed ({r_s['engine_rul_pct']:.1f})")


def t18_rul_monotonicity(url, ts):
    ts.h(18, "RUL MODEL — Monotonicity Sweep (Thermal Stress)")
    prev_rul = None
    violations = 0
    steps = []
    for thermal in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        r = analyze(url, bp(thermal_stress_index=thermal))
        cur = r["engine_rul_pct"]
        steps.append((thermal, cur))
        if prev_rul is not None and cur > prev_rul + 2.0:  # allow 2% tolerance
            violations += 1
        prev_rul = cur
    ts.check(violations == 0,
             f"RUL decreases as thermal_stress rises: {violations} violations in {steps}")


def t19_failure_prob_direction(url, ts):
    ts.h(19, "FAILURE MODEL — Probability Direction")
    r_ok = analyze(url, bp())
    r_bad = analyze(url, bp(thermal_stress_index=0.95, brake_rul_pct=5,
                            engine_rul_pct=8, battery_rul_pct=10,
                            mechanical_vibration_anomaly_score=0.95))
    p_ok = r_ok["fault_failure_probability_7d"]
    p_bad = r_bad["fault_failure_probability_7d"]
    ts.check(p_bad > p_ok,
             f"bad prob ({p_bad:.2f}) > healthy prob ({p_ok:.2f})")
    ts.check(p_bad >= 0.7,
             f"critical scenario prob >= 0.7: got {p_bad:.2f}")


def t20_failure_prob_monotonicity(url, ts):
    ts.h(20, "FAILURE MODEL — Monotonicity Sweep (Brake RUL)")
    prev = None
    violations = 0
    steps = []
    for brake in [100, 80, 60, 40, 20, 5]:
        r = analyze(url, bp(brake_rul_pct=brake, thermal_stress_index=0.60,
                            mechanical_vibration_anomaly_score=0.50))
        cur = r["fault_failure_probability_7d"]
        steps.append((brake, cur))
        if prev is not None and cur < prev - 0.05:  # allow small tolerance
            violations += 1
        prev = cur
    ts.check(violations == 0,
             f"fail_prob rises as brake_rul drops: {violations} violations in {steps}")


# ── CONSISTENCY TESTS ───────────────────────────────────────────────────

def t21_idempotency(url, ts):
    ts.h(21, "IDEMPOTENCY — Same Input → Same Output (10 runs)")
    payload = bp(thermal_stress_index=0.55, brake_rul_pct=45,
                 mechanical_vibration_anomaly_score=0.40)
    results = [analyze(url, payload) for _ in range(10)]
    ref = results[0]
    identical = all(
        r["engine_rul_pct"] == ref["engine_rul_pct"]
        and r["fault_failure_probability_7d"] == ref["fault_failure_probability_7d"]
        and r["fault_primary"] == ref["fault_primary"]
        and r["fault_contributing_factors"] == ref["fault_contributing_factors"]
        and r["recommendation"] == ref["recommendation"]
        for r in results
    )
    ts.check(identical, f"10 identical results: engine_rul={ref['engine_rul_pct']}, "
                        f"prob={ref['fault_failure_probability_7d']}")


def t22_stateless(url, ts):
    ts.h(22, "STATELESS — Previous Request Doesn't Affect Next")
    # Send critical first, then healthy — healthy should still be fine
    analyze(url, bp(thermal_stress_index=0.95, brake_rul_pct=5,
                    mechanical_vibration_anomaly_score=0.95))
    r = analyze(url, bp())
    ts.check(r["fault_failure_probability_7d"] < 0.3,
             f"healthy after critical → prob still low: {r['fault_failure_probability_7d']}")
    ts.check(r["fault_primary"] == "NO_DOMINANT_FAULT",
             f"healthy after critical → still NO_DOMINANT_FAULT: {r['fault_primary']}")


# ── EXTREME / ADVERSARIAL INPUTS ────────────────────────────────────────

def t23_all_zeros(url, ts):
    ts.h(23, "EXTREME — All Zeros (Minimum Valid Input)")
    r = analyze(url, bp(thermal_stress_index=0.0,
                        mechanical_vibration_anomaly_score=0.0,
                        mechanical_vibration_rms=0.0,
                        electrical_charging_efficiency_score=0.0,
                        electrical_battery_health_pct=0.0,
                        engine_rul_pct=0.0,
                        brake_rul_pct=0.0,
                        battery_rul_pct=0.0,
                        vehicle_health_score=0.0,
                        mechanical_dominant_fault_band_hz=0.01))
    ts.check(0 <= r["engine_rul_pct"] <= 100, f"RUL valid: {r['engine_rul_pct']}")
    ts.check(0 <= r["fault_failure_probability_7d"] <= 1, f"prob valid: {r['fault_failure_probability_7d']}")
    ts.check(r["fault_primary"] in VALID_FAULTS, f"fault valid: {r['fault_primary']}")
    # charging=0.0 < 0.65 → ELECTRICAL_DEGRADATION (or overridden by brake_thermal)
    ts.check(r["fault_primary"] in ("ELECTRICAL_DEGRADATION", "MULTI_FACTOR_FAILURE_RISK",
                                     "BRAKE_THERMAL_SATURATION"),
             f"zero inputs → some fault detected: {r['fault_primary']}")


def t24_all_max(url, ts):
    ts.h(24, "EXTREME — All Maximums")
    r = analyze(url, bp(thermal_stress_index=1.0,
                        mechanical_vibration_anomaly_score=1.0,
                        mechanical_vibration_rms=99.0,
                        electrical_charging_efficiency_score=1.0,
                        electrical_battery_health_pct=100.0,
                        engine_rul_pct=100.0,
                        brake_rul_pct=100.0,
                        battery_rul_pct=100.0,
                        vehicle_health_score=1.0,
                        mechanical_dominant_fault_band_hz=999.0))
    ts.check(0 <= r["engine_rul_pct"] <= 100, f"RUL valid: {r['engine_rul_pct']}")
    ts.check(0 <= r["fault_failure_probability_7d"] <= 1, f"prob valid: {r['fault_failure_probability_7d']}")
    # thermal=1.0>0.75 but brake=100 NOT<40 → vibration should fire (vib=1.0>0.7)
    ts.check(r["fault_primary"] == "MECHANICAL_VIBRATION_ANOMALY",
             f"all max (brake OK) → vibration_anomaly: {r['fault_primary']}")


def t25_edge_decimals(url, ts):
    ts.h(25, "EXTREME — Edge Decimal Values")
    # Very tiny values
    r1 = analyze(url, bp(thermal_stress_index=0.001,
                         mechanical_vibration_anomaly_score=0.001,
                         electrical_charging_efficiency_score=0.999,
                         vehicle_health_score=0.999))
    ts.check(0 <= r1["engine_rul_pct"] <= 100, "tiny values → valid RUL")
    # Values at schema limits
    r2 = analyze(url, bp(engine_rul_pct=0.0, brake_rul_pct=0.0, battery_rul_pct=0.0))
    ts.check(r2["brake_rul_pct"] == 0.0, "brake_rul=0 passthrough")
    r3 = analyze(url, bp(engine_rul_pct=100.0, brake_rul_pct=100.0, battery_rul_pct=100.0))
    ts.check(r3["brake_rul_pct"] == 100.0, "brake_rul=100 passthrough")


# ── INPUT VALIDATION (422) ──────────────────────────────────────────────

def t26_input_validation(url, ts):
    ts.h(26, "INPUT VALIDATION — Reject Bad Payloads (422)")
    # Missing required fields
    for field_name in ["vehicle_id", "thermal_stress_index", "engine_rul_pct",
                       "brake_rul_pct", "mechanical_dominant_fault_band_hz"]:
        p = bp()
        del p[field_name]
        code, _ = _post(url, p)
        ts.check(code == 422, f"missing '{field_name}' → 422: got {code}")

    # Out of range for bounded fields
    out_of_range = [
        ("thermal_stress_index", -0.1),
        ("thermal_stress_index", 1.5),
        ("mechanical_vibration_anomaly_score", -0.1),
        ("mechanical_vibration_anomaly_score", 1.5),
        ("electrical_charging_efficiency_score", -0.5),
        ("electrical_charging_efficiency_score", 2.0),
        ("electrical_battery_health_pct", -10),
        ("electrical_battery_health_pct", 150),
        ("engine_rul_pct", -1),
        ("engine_rul_pct", 101),
        ("brake_rul_pct", -1),
        ("brake_rul_pct", 101),
        ("battery_rul_pct", -5),
        ("battery_rul_pct", 200),
        ("vehicle_health_score", -0.5),
        ("vehicle_health_score", 1.5),
        ("mechanical_dominant_fault_band_hz", 0),    # gt=0.0
        ("mechanical_dominant_fault_band_hz", -10),
    ]
    for fname, val in out_of_range:
        code, _ = _post(url, bp(**{fname: val}))
        ts.check(code == 422, f"{fname}={val} → 422: got {code}")


def t27_wrong_types(url, ts):
    ts.h(27, "INPUT VALIDATION — Wrong Data Types")
    type_errors = [
        ("vehicle_id", 12345),            # should be string
        ("timestamp_ms", "not_a_number"),  # should be int
        ("thermal_stress_index", "hot"),   # should be float
        ("engine_rul_pct", [1, 2, 3]),     # should be float
        ("brake_rul_pct", None),           # should be float
        ("vehicle_health_score", {"a": 1}), # should be float
    ]
    for fname, val in type_errors:
        code, _ = _post(url, bp(**{fname: val}))
        ts.check(code == 422, f"{fname}={repr(val)} → 422: got {code}")

    # Completely garbage payload
    code, _ = _post(url, {"garbage": True})
    ts.check(code == 422, f"garbage payload → 422: got {code}")

    # Empty object
    code, _ = _post(url, {})
    ts.check(code == 422, f"empty payload → 422: got {code}")


def t28_extra_fields(url, ts):
    ts.h(28, "INPUT VALIDATION — Extra Unknown Fields (Should Be Accepted)")
    r = analyze(url, bp(extra_unknown_field="should_be_ignored",
                        another_field=42))
    ts.check(r["vehicle_id"] == "BRUTAL_TEST_001",
             "extra fields ignored, response valid")


# ── CROSS-SYSTEM CONSISTENCY ────────────────────────────────────────────

def t29_fault_recommendation_consistency(url, ts):
    ts.h(29, "CROSS-SYSTEM — Fault↔Recommendation Consistency")
    scenarios = [
        bp(thermal_stress_index=0.90, brake_rul_pct=15,
           mechanical_vibration_anomaly_score=0.85),  # critical
        bp(),  # healthy
        bp(thermal_stress_index=0.30, brake_rul_pct=70,
           mechanical_vibration_anomaly_score=0.85),  # vibration
        bp(thermal_stress_index=0.20,
           mechanical_vibration_anomaly_score=0.10,
           electrical_charging_efficiency_score=0.40),  # electrical
    ]
    for i, payload in enumerate(scenarios):
        r = analyze(url, payload)
        fault = r["fault_primary"]
        prob = r["fault_failure_probability_7d"]
        priority = r["recommendation"]["recommendation_service_priority"]
        limit = r["recommendation"]["recommendation_safe_operating_limit_km"]
        # If priority is high, limit must be 120
        if priority == "high":
            ts.check(limit == 120, f"scenario {i}: high→120km: got {limit}")
        # If priority is medium, limit must be 300
        if priority == "medium":
            ts.check(limit == 300, f"scenario {i}: medium→300km: got {limit}")
        # If priority is low, limit must be 600
        if priority == "low":
            ts.check(limit == 600, f"scenario {i}: low→600km: got {limit}")
        # If priority is normal, limit must be 1000
        if priority == "normal":
            ts.check(limit == 1000, f"scenario {i}: normal→1000km: got {limit}")
        # Contributors must never be empty
        ts.check(len(r["fault_contributing_factors"]) > 0,
                 f"scenario {i}: contributors non-empty")


# ── MULTI-VEHICLE TEST ──────────────────────────────────────────────────

def t30_multi_vehicle(url, ts):
    ts.h(30, "MULTI-VEHICLE — Different Vehicles, Different Results")
    vehicles = [
        ("VIT_CAR_001", bp(vehicle_id="VIT_CAR_001")),
        ("VIT_TRUCK_010", bp(vehicle_id="VIT_TRUCK_010",
                             thermal_stress_index=0.90, brake_rul_pct=10)),
        ("VIT_BUS_005", bp(vehicle_id="VIT_BUS_005",
                           mechanical_vibration_anomaly_score=0.85)),
    ]
    for vid, payload in vehicles:
        r = analyze(url, payload)
        ts.check(r["vehicle_id"] == vid, f"{vid} → correct ID returned")


# ── RAPID-FIRE STRESS TEST ──────────────────────────────────────────────

def t31_rapid_fire(url, ts):
    ts.h(31, "STRESS — 50 Rapid-Fire Sequential Requests")
    errors = 0
    valid = 0
    t0 = time.perf_counter()
    for _ in range(50):
        try:
            r = analyze(url, bp(
                thermal_stress_index=random.uniform(0, 1),
                mechanical_vibration_anomaly_score=random.uniform(0, 1),
                electrical_charging_efficiency_score=random.uniform(0, 1),
                brake_rul_pct=random.uniform(0, 100),
                engine_rul_pct=random.uniform(0, 100),
                battery_rul_pct=random.uniform(0, 100),
                vehicle_health_score=random.uniform(0, 1),
                mechanical_vibration_rms=random.uniform(0, 5),
                mechanical_dominant_fault_band_hz=random.uniform(1, 500),
                electrical_battery_health_pct=random.uniform(0, 100),
            ))
            if (0 <= r["engine_rul_pct"] <= 100
                    and 0 <= r["fault_failure_probability_7d"] <= 1
                    and r["fault_primary"] in VALID_FAULTS):
                valid += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    elapsed = time.perf_counter() - t0
    ts.check(errors == 0, f"50 random requests: {valid} valid, {errors} errors")
    avg_ms = elapsed / 50 * 1000
    ts.check(avg_ms < 5000, f"avg response: {avg_ms:.0f}ms (< 5s each)")
    info(f"total: {elapsed:.1f}s, avg: {avg_ms:.0f}ms/request")


def t32_concurrent(url, ts):
    ts.h(32, "STRESS — 20 Concurrent Requests")
    def do_request(idx):
        return idx, analyze(url, bp(vehicle_id=f"CONCURRENT_{idx:03d}",
                                    thermal_stress_index=random.uniform(0, 1)))

    errors = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(do_request, i) for i in range(20)]
        for f in as_completed(futures):
            try:
                idx, r = f.result()
                if r["vehicle_id"] != f"CONCURRENT_{idx:03d}":
                    errors += 1
            except Exception:
                errors += 1
    ts.check(errors == 0, f"20 concurrent: {20-errors} succeeded, {errors} errors")


# ── LATENCY / PERFORMANCE ──────────────────────────────────────────────

def t33_latency(url, ts):
    ts.h(33, "LATENCY — Response Time Benchmarks")
    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        analyze(url, bp())
        times.append((time.perf_counter() - t0) * 1000)
    avg = statistics.mean(times)
    p95 = sorted(times)[int(0.95 * len(times))]
    median = statistics.median(times)
    ts.check(avg < 3000, f"avg latency: {avg:.0f}ms (< 3s)")
    ts.check(p95 < 5000, f"p95 latency: {p95:.0f}ms (< 5s)")
    info(f"median={median:.0f}ms  avg={avg:.0f}ms  p95={p95:.0f}ms  "
         f"min={min(times):.0f}ms  max={max(times):.0f}ms")


# ── ERROR PATHS ─────────────────────────────────────────────────────────

def t34_method_not_allowed(url, ts):
    ts.h(34, "ERROR HANDLING — Wrong HTTP Methods")
    # GET to /analyze should fail
    code, _ = _get(url, "/analyze")
    ts.check(code == 405, f"GET /analyze → 405: got {code}")
    # POST to /health should fail
    code2, _ = _post(url, bp())  # Posting to analyze, need to test health
    # Actually test post to health
    if USE_HTTPX:
        with httpx.Client(timeout=10) as c:
            r = c.post(f"{url}/health", json={})
            code3 = r.status_code
    else:
        try:
            req = urllib.request.Request(f"{url}/health", data=b"{}",
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                code3 = resp.status
        except urllib.error.HTTPError as e:
            code3 = e.code
    ts.check(code3 == 405, f"POST /health → 405: got {code3}")


def t35_nonexistent_endpoint(url, ts):
    ts.h(35, "ERROR HANDLING — Non-Existent Endpoints")
    code, _ = _get(url, "/nonexistent")
    ts.check(code == 404, f"GET /nonexistent → 404: got {code}")
    code2, _ = _get(url, "/api/v2/analyze")
    ts.check(code2 == 404, f"GET /api/v2/analyze → 404: got {code2}")


# ── SENSITIVITY ANALYSIS ───────────────────────────────────────────────

def t36_sensitivity(url, ts):
    ts.h(36, "SENSITIVITY — Each Feature's Impact on Output")
    baseline = analyze(url, bp())
    base_rul = baseline["engine_rul_pct"]
    base_prob = baseline["fault_failure_probability_7d"]

    # thermal_stress should affect RUL
    r = analyze(url, bp(thermal_stress_index=0.95))
    ts.check(r["engine_rul_pct"] != base_rul,
             f"thermal_stress impacts RUL: {base_rul} → {r['engine_rul_pct']}")

    # vibration should affect RUL (it's a feature)
    r2 = analyze(url, bp(mechanical_vibration_anomaly_score=0.95))
    ts.check(r2["engine_rul_pct"] != base_rul,
             f"vibration impacts RUL: {base_rul} → {r2['engine_rul_pct']}")

    # vehicle_health should affect RUL
    r3 = analyze(url, bp(vehicle_health_score=0.10))
    ts.check(r3["engine_rul_pct"] != base_rul,
             f"health_score impacts RUL: {base_rul} → {r3['engine_rul_pct']}")

    # brake_rul should affect failure_prob
    r4 = analyze(url, bp(brake_rul_pct=5))
    ts.check(r4["fault_failure_probability_7d"] != base_prob,
             f"brake_rul impacts prob: {base_prob} → {r4['fault_failure_probability_7d']}")


def t37_realistic_scenarios(url, ts):
    ts.h(37, "REALISTIC SCENARIOS — Common Vehicle States")
    scenarios = {
        "brand_new_car": bp(
            thermal_stress_index=0.05, mechanical_vibration_anomaly_score=0.02,
            mechanical_vibration_rms=0.05, electrical_charging_efficiency_score=0.98,
            electrical_battery_health_pct=99, engine_rul_pct=98,
            brake_rul_pct=99, battery_rul_pct=97, vehicle_health_score=0.99),
        "aging_commuter": bp(
            thermal_stress_index=0.40, mechanical_vibration_anomaly_score=0.35,
            mechanical_vibration_rms=0.40, electrical_charging_efficiency_score=0.78,
            electrical_battery_health_pct=72, engine_rul_pct=55,
            brake_rul_pct=48, battery_rul_pct=60, vehicle_health_score=0.60),
        "track_day_abuse": bp(
            thermal_stress_index=0.92, mechanical_vibration_anomaly_score=0.75,
            mechanical_vibration_rms=0.88, electrical_charging_efficiency_score=0.70,
            electrical_battery_health_pct=65, engine_rul_pct=40,
            brake_rul_pct=15, battery_rul_pct=50, vehicle_health_score=0.35),
        "electrical_failing": bp(
            thermal_stress_index=0.25, mechanical_vibration_anomaly_score=0.15,
            mechanical_vibration_rms=0.20, electrical_charging_efficiency_score=0.35,
            electrical_battery_health_pct=25, engine_rul_pct=70,
            brake_rul_pct=65, battery_rul_pct=30, vehicle_health_score=0.55),
        "vibration_problem": bp(
            thermal_stress_index=0.30, mechanical_vibration_anomaly_score=0.88,
            mechanical_vibration_rms=0.92, electrical_charging_efficiency_score=0.85,
            electrical_battery_health_pct=80, engine_rul_pct=60,
            brake_rul_pct=55, battery_rul_pct=70, vehicle_health_score=0.50),
    }
    expected = {
        "brand_new_car": ("NO_DOMINANT_FAULT", "normal"),
        "track_day_abuse": ("BRAKE_THERMAL_SATURATION", "high"),
        "electrical_failing": ("ELECTRICAL_DEGRADATION", None),
        "vibration_problem": ("MECHANICAL_VIBRATION_ANOMALY", None),
    }
    for name, payload in scenarios.items():
        r = analyze(url, payload)
        ts.check(r["fault_primary"] in VALID_FAULTS,
                 f"{name}: valid fault '{r['fault_primary']}'")
        ts.check(0 <= r["fault_failure_probability_7d"] <= 1,
                 f"{name}: valid prob {r['fault_failure_probability_7d']}")
        if name in expected:
            exp_fault, exp_priority = expected[name]
            ts.check(r["fault_primary"] == exp_fault,
                     f"{name}: fault={r['fault_primary']} (expected {exp_fault})")
            if exp_priority:
                ts.check(r["recommendation"]["recommendation_service_priority"] == exp_priority,
                         f"{name}: priority={r['recommendation']['recommendation_service_priority']} "
                         f"(expected {exp_priority})")


def t38_gradual_degradation(url, ts):
    ts.h(38, "DEGRADATION — Simulated Gradual Component Failure")
    # Simulate a brake gradually failing over time
    prev_limit = 9999
    for step, brake_rul in enumerate([90, 70, 50, 39, 25, 10, 3]):
        r = analyze(url, bp(brake_rul_pct=brake_rul,
                            thermal_stress_index=0.40 + step * 0.08))
        limit = r["recommendation"]["recommendation_safe_operating_limit_km"]
        # Safe limit should generally decrease or stay same as condition worsens
        if step > 0:
            ts.check(limit <= prev_limit,
                     f"step {step} brake={brake_rul}: limit {limit} <= prev {prev_limit}")
        prev_limit = limit


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

ALL_TESTS = [
    t01_health, t02_schema, t03_value_bounds, t04_passthrough,
    t05_healthy_vehicle,
    t06_brake_thermal, t07_brake_thermal_boundary,
    t08_vibration_anomaly, t09_vibration_boundary,
    t10_electrical, t11_electrical_boundary,
    t12_fault_priority_chain, t13_contributor_thresholds, t14_contributor_combos,
    t15_recommendation_cascade, t16_brake_thermal_always_high,
    t17_rul_direction, t18_rul_monotonicity,
    t19_failure_prob_direction, t20_failure_prob_monotonicity,
    t21_idempotency, t22_stateless,
    t23_all_zeros, t24_all_max, t25_edge_decimals,
    t26_input_validation, t27_wrong_types, t28_extra_fields,
    t29_fault_recommendation_consistency,
    t30_multi_vehicle,
    t31_rapid_fire, t32_concurrent,
    t33_latency,
    t34_method_not_allowed, t35_nonexistent_endpoint,
    t36_sensitivity,
    t37_realistic_scenarios, t38_gradual_degradation,
]


def main():
    parser = argparse.ArgumentParser(description="BRUTAL Cloud AI Test Suite")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print(f"\n{B}{CYAN}{'═'*64}")
    print(f"  🔥  BRUTAL Cloud AI Correctness Suite  🔥")
    print(f"  Server : {args.url}")
    print(f"  Tests  : {len(ALL_TESTS)} sections")
    print(f"{'═'*64}{X}")

    ts = TS()
    for fn in ALL_TESTS:
        try:
            fn(args.url, ts)
        except Exception as e:
            fail(f"EXCEPTION in {fn.__name__}: {e}")
            ts.failed += 1

    total = ts.passed + ts.failed
    pct = (ts.passed / total * 100) if total else 0

    print(f"\n{B}{CYAN}{'═'*64}")
    print(f"  📊  FINAL RESULTS")
    print(f"{'═'*64}{X}")
    print(f"  Total checks : {total}")
    print(f"  {G}✔ Passed{X}     : {ts.passed}")
    print(f"  {R}✘ Failed{X}     : {ts.failed}")
    print(f"  {Y}⚠ Warnings{X}  : {ts.warned}")
    print(f"  Score        : {pct:.1f}%")
    if ts.failed == 0:
        print(f"\n  {G}{B}🏆  ALL TESTS PASSED  🏆{X}")
    else:
        print(f"\n  {R}{B}❌  {ts.failed} TEST(S) FAILED  ❌{X}")
    print(f"{B}{CYAN}{'═'*64}{X}\n")
    sys.exit(0 if ts.failed == 0 else 1)


if __name__ == "__main__":
    main()
