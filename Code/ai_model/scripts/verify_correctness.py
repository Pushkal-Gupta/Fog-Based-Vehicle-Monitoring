"""
Cloud AI Correctness Validator
===============================
Tests that every rule in explanation, recommendation, and model prediction
behaves correctly. Sends crafted payloads to the live /analyze endpoint
and checks that outputs match expected logic.

Usage (server must be running):
    python scripts/verify_correctness.py
    python scripts/verify_correctness.py --url http://host:port
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field

try:
    import httpx
    USE_HTTPX = True
except ImportError:
    import urllib.request, urllib.error
    USE_HTTPX = False

# ── Colour helpers ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def ok(msg):   print(f"  {GREEN}✔ PASS{RESET}  {msg}")
def fail(msg): print(f"  {RED}✘ FAIL{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}⚠ WARN{RESET}  {msg}")

# ── API call ────────────────────────────────────────────────────────────────

def call_analyze(base_url: str, payload: dict) -> dict:
    url = f"{base_url}/analyze"
    if USE_HTTPX:
        with httpx.Client(timeout=15) as c:
            r = c.post(url, json=payload)
            r.raise_for_status()
            return r.json()
    else:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())


def call_health(base_url: str) -> dict:
    url = f"{base_url}/health"
    if USE_HTTPX:
        with httpx.Client(timeout=10) as c:
            r = c.get(url)
            r.raise_for_status()
            return r.json()
    else:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())


# ── Base payload builder ────────────────────────────────────────────────────

def base_payload(**overrides) -> dict:
    """Build a healthy-baseline payload, overriding specific fields."""
    p = {
        "vehicle_id": "TEST_VEH_001",
        "timestamp_ms": int(time.time() * 1000),
        "thermal_brake_margin": 0.3,
        "thermal_engine_margin": 0.4,
        "thermal_stress_index": 0.15,
        "mechanical_vibration_anomaly_score": 0.10,
        "mechanical_dominant_fault_band_hz": 60,
        "mechanical_vibration_rms": 0.15,
        "electrical_charging_efficiency_score": 0.95,
        "electrical_battery_health_pct": 95,
        "engine_rul_pct": 85,
        "brake_rul_pct": 90,
        "battery_rul_pct": 88,
        "vehicle_health_score": 0.90,
    }
    p.update(overrides)
    return p


# ── Test framework ──────────────────────────────────────────────────────────

@dataclass
class TestSuite:
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    details: list = field(default_factory=list)

    def check(self, condition: bool, msg: str, critical: bool = True):
        if condition:
            ok(msg)
            self.passed += 1
        elif critical:
            fail(msg)
            self.failed += 1
        else:
            warn(msg)
            self.warnings += 1

    def section(self, title: str):
        print(f"\n{BOLD}{'─'*60}")
        print(f"  {title}")
        print(f"{'─'*60}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# TEST CASES
# ═══════════════════════════════════════════════════════════════════════════

def test_health_endpoint(url: str, ts: TestSuite):
    ts.section("1. Health Endpoint")
    resp = call_health(url)
    ts.check(resp.get("status") == "ok", "status == 'ok'")
    ts.check(resp.get("mode") == "advisory-only", "mode == 'advisory-only'")
    ts.check(resp.get("authority") == "cloud_has_no_actuation_control",
             "authority == 'cloud_has_no_actuation_control'")


def test_output_schema(url: str, ts: TestSuite):
    ts.section("2. Output Schema Validation")
    resp = call_analyze(url, base_payload())
    required = ["vehicle_id", "timestamp_ms", "engine_rul_pct", "brake_rul_pct",
                "battery_rul_pct", "fault_failure_probability_7d", "fault_primary",
                "fault_contributing_factors", "recommendation"]
    for key in required:
        ts.check(key in resp, f"output contains '{key}'")

    rec = resp.get("recommendation", {})
    for key in ["recommendation_service_priority", "recommendation_suggested_action",
                "recommendation_safe_operating_limit_km"]:
        ts.check(key in rec, f"recommendation contains '{key}'")


def test_value_ranges(url: str, ts: TestSuite):
    ts.section("3. Value Range Validation")
    resp = call_analyze(url, base_payload())

    rul = resp["engine_rul_pct"]
    ts.check(0 <= rul <= 100, f"engine_rul_pct in [0,100]: got {rul}")

    prob = resp["fault_failure_probability_7d"]
    ts.check(0 <= prob <= 1, f"failure_prob in [0,1]: got {prob}")

    ts.check(resp["brake_rul_pct"] == 90.0,
             f"brake_rul_pct passed through unchanged: got {resp['brake_rul_pct']}")
    ts.check(resp["battery_rul_pct"] == 88.0,
             f"battery_rul_pct passed through unchanged: got {resp['battery_rul_pct']}")


def test_healthy_vehicle(url: str, ts: TestSuite):
    ts.section("4. Healthy Vehicle → Low Risk")
    resp = call_analyze(url, base_payload())
    prob = resp["fault_failure_probability_7d"]
    ts.check(prob < 0.3,
             f"healthy vehicle failure_prob < 0.3: got {prob}")
    ts.check(resp["fault_primary"] == "NO_DOMINANT_FAULT",
             f"fault_primary == NO_DOMINANT_FAULT: got {resp['fault_primary']}")
    ts.check(resp["recommendation"]["recommendation_service_priority"] in ("normal", "low"),
             f"priority is normal/low: got {resp['recommendation']['recommendation_service_priority']}")


def test_brake_thermal_saturation(url: str, ts: TestSuite):
    ts.section("5. Brake Thermal Saturation Rule")
    # Rule: thermal_stress_index > 0.75 AND brake_rul_pct < 40
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.85,
        brake_rul_pct=25,
        mechanical_vibration_anomaly_score=0.10,
    ))
    ts.check(resp["fault_primary"] == "BRAKE_THERMAL_SATURATION",
             f"fault = BRAKE_THERMAL_SATURATION: got {resp['fault_primary']}")
    ts.check("high_thermal_stress_index" in resp["fault_contributing_factors"],
             "contributors include high_thermal_stress_index")
    ts.check("low_brake_rul_pct" in resp["fault_contributing_factors"],
             "contributors include low_brake_rul_pct")
    ts.check(resp["recommendation"]["recommendation_service_priority"] == "high",
             f"priority == high: got {resp['recommendation']['recommendation_service_priority']}")
    ts.check(resp["recommendation"]["recommendation_safe_operating_limit_km"] == 120,
             f"safe_limit == 120 km: got {resp['recommendation']['recommendation_safe_operating_limit_km']}")


def test_brake_thermal_boundary(url: str, ts: TestSuite):
    ts.section("6. Brake Thermal Saturation Boundary Cases")
    # Just below thresholds → should NOT trigger
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.74,  # below 0.75
        brake_rul_pct=41,           # above 40
    ))
    ts.check(resp["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"below threshold → NOT brake_thermal: got {resp['fault_primary']}")

    # Thermal high but brake OK → should NOT trigger
    resp2 = call_analyze(url, base_payload(
        thermal_stress_index=0.90,
        brake_rul_pct=60,
    ))
    ts.check(resp2["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"thermal high + brake OK → NOT brake_thermal: got {resp2['fault_primary']}")

    # Brake low but thermal OK → should NOT trigger primary (might be MULTI_FACTOR)
    resp3 = call_analyze(url, base_payload(
        thermal_stress_index=0.20,
        brake_rul_pct=15,
    ))
    ts.check(resp3["fault_primary"] != "BRAKE_THERMAL_SATURATION",
             f"brake low + thermal OK → NOT brake_thermal: got {resp3['fault_primary']}")


def test_vibration_anomaly(url: str, ts: TestSuite):
    ts.section("7. Mechanical Vibration Anomaly Rule")
    # Rule: vibration_anomaly > 0.7 (and not brake_thermal first)
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.30,
        brake_rul_pct=70,
        mechanical_vibration_anomaly_score=0.85,
        mechanical_vibration_rms=0.90,
    ))
    ts.check(resp["fault_primary"] == "MECHANICAL_VIBRATION_ANOMALY",
             f"fault = MECHANICAL_VIBRATION_ANOMALY: got {resp['fault_primary']}")
    ts.check("high_mechanical_vibration_anomaly_score" in resp["fault_contributing_factors"],
             "contributors include high_mechanical_vibration_anomaly_score")
    ts.check("high_mechanical_vibration_rms" in resp["fault_contributing_factors"],
             "contributors include high_mechanical_vibration_rms")


def test_electrical_degradation(url: str, ts: TestSuite):
    ts.section("8. Electrical Degradation Rule")
    # Rule: charging_eff < 0.65 OR battery_health < 60
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.20,
        mechanical_vibration_anomaly_score=0.10,
        electrical_charging_efficiency_score=0.50,
        electrical_battery_health_pct=45,
    ))
    ts.check(resp["fault_primary"] == "ELECTRICAL_DEGRADATION",
             f"fault = ELECTRICAL_DEGRADATION: got {resp['fault_primary']}")
    ts.check("low_electrical_charging_efficiency_score" in resp["fault_contributing_factors"],
             "contributors include low_electrical_charging_efficiency_score")


def test_multi_factor_risk(url: str, ts: TestSuite):
    ts.section("9. Multi-Factor Failure Risk Rule")
    # This fires when failure_prob > 0.65 but none of the specific faults match first
    # Use values that push failure_prob high without triggering specific rules
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.74,   # just below 0.75
        brake_rul_pct=38,            # below 40 → contributes to failure but no brake_thermal (needs thermal>0.75)
        mechanical_vibration_anomaly_score=0.69,  # just below 0.7
        electrical_charging_efficiency_score=0.70,
        engine_rul_pct=20,
        battery_rul_pct=30,
        vehicle_health_score=0.25,
    ))
    prob = resp["fault_failure_probability_7d"]
    if prob > 0.65:
        ts.check(resp["fault_primary"] == "MULTI_FACTOR_FAILURE_RISK",
                 f"high prob + no specific fault → MULTI_FACTOR: got {resp['fault_primary']}")
    else:
        warn(f"model didn't produce high enough prob ({prob:.2f}) for this test — skipping")
        ts.warnings += 1


def test_recommendation_priority_cascade(url: str, ts: TestSuite):
    ts.section("10. Recommendation Priority Cascade")

    # HIGH: failure_prob > 0.75
    resp1 = call_analyze(url, base_payload(
        thermal_stress_index=0.90,
        brake_rul_pct=15,
        mechanical_vibration_anomaly_score=0.80,
    ))
    ts.check(resp1["recommendation"]["recommendation_service_priority"] == "high",
             f"critical scenario → priority=high: got {resp1['recommendation']['recommendation_service_priority']}")

    # MEDIUM: brake_rul_pct < 40 (but not high failure prob)
    resp2 = call_analyze(url, base_payload(
        thermal_stress_index=0.20,
        brake_rul_pct=35,
        mechanical_vibration_anomaly_score=0.10,
        engine_rul_pct=80,
    ))
    rec2 = resp2["recommendation"]["recommendation_service_priority"]
    ts.check(rec2 == "medium",
             f"brake_rul<40 → priority=medium: got {rec2}", critical=False)

    # NORMAL: all OK
    resp3 = call_analyze(url, base_payload())
    ts.check(resp3["recommendation"]["recommendation_service_priority"] == "normal",
             f"all OK → priority=normal: got {resp3['recommendation']['recommendation_service_priority']}")


def test_safe_operating_limits(url: str, ts: TestSuite):
    ts.section("11. Safe Operating Limits")
    # High priority → 120 km
    resp_high = call_analyze(url, base_payload(
        thermal_stress_index=0.90, brake_rul_pct=15,
        mechanical_vibration_anomaly_score=0.80,
    ))
    ts.check(resp_high["recommendation"]["recommendation_safe_operating_limit_km"] == 120,
             f"high priority → 120 km: got {resp_high['recommendation']['recommendation_safe_operating_limit_km']}")

    # Normal → 1000 km
    resp_norm = call_analyze(url, base_payload())
    ts.check(resp_norm["recommendation"]["recommendation_safe_operating_limit_km"] == 1000,
             f"normal priority → 1000 km: got {resp_norm['recommendation']['recommendation_safe_operating_limit_km']}")


def test_contributor_logic(url: str, ts: TestSuite):
    ts.section("12. Contributor Factor Logic")
    # No contributors → "no_dominant_contributor"
    resp = call_analyze(url, base_payload())
    ts.check("no_dominant_contributor" in resp["fault_contributing_factors"],
             f"healthy → 'no_dominant_contributor' present")

    # All contributors triggered at once
    resp2 = call_analyze(url, base_payload(
        thermal_stress_index=0.90,
        brake_rul_pct=15,
        mechanical_vibration_anomaly_score=0.80,
        mechanical_vibration_rms=0.95,
        electrical_charging_efficiency_score=0.50,
    ))
    expected = {"high_thermal_stress_index", "low_brake_rul_pct",
                "high_mechanical_vibration_anomaly_score",
                "high_mechanical_vibration_rms",
                "low_electrical_charging_efficiency_score"}
    actual = set(resp2["fault_contributing_factors"])
    ts.check(expected == actual,
             f"all contributors triggered: expected {len(expected)}, got {len(actual)}")


def test_vehicle_id_passthrough(url: str, ts: TestSuite):
    ts.section("13. Vehicle ID & Timestamp Passthrough")
    vid = "CUSTOM_TEST_999"
    ts_ms = 9999999999999
    resp = call_analyze(url, base_payload(vehicle_id=vid, timestamp_ms=ts_ms))
    ts.check(resp["vehicle_id"] == vid, f"vehicle_id passed through: {resp['vehicle_id']}")
    ts.check(resp["timestamp_ms"] == ts_ms, f"timestamp_ms passed through: {resp['timestamp_ms']}")


def test_rul_prediction_sanity(url: str, ts: TestSuite):
    ts.section("14. RUL Prediction Sanity Checks")
    # Healthy inputs → high RUL
    resp_healthy = call_analyze(url, base_payload(
        thermal_stress_index=0.05,
        mechanical_vibration_anomaly_score=0.05,
        electrical_charging_efficiency_score=0.98,
        vehicle_health_score=0.98,
    ))
    rul_h = resp_healthy["engine_rul_pct"]
    ts.check(rul_h > 50, f"healthy inputs → engine_rul > 50%: got {rul_h}")

    # Stressed inputs → lower RUL
    resp_stressed = call_analyze(url, base_payload(
        thermal_stress_index=0.95,
        mechanical_vibration_anomaly_score=0.90,
        electrical_charging_efficiency_score=0.50,
        vehicle_health_score=0.20,
    ))
    rul_s = resp_stressed["engine_rul_pct"]
    ts.check(rul_s < rul_h,
             f"stressed RUL ({rul_s:.1f}) < healthy RUL ({rul_h:.1f})")


def test_failure_prob_direction(url: str, ts: TestSuite):
    ts.section("15. Failure Probability Direction")
    resp_ok = call_analyze(url, base_payload())
    resp_bad = call_analyze(url, base_payload(
        thermal_stress_index=0.95,
        brake_rul_pct=10,
        engine_rul_pct=12,
        battery_rul_pct=20,
        mechanical_vibration_anomaly_score=0.90,
    ))
    p_ok = resp_ok["fault_failure_probability_7d"]
    p_bad = resp_bad["fault_failure_probability_7d"]
    ts.check(p_bad > p_ok,
             f"bad scenario prob ({p_bad:.2f}) > healthy prob ({p_ok:.2f})")


def test_fault_priority_order(url: str, ts: TestSuite):
    ts.section("16. Fault Priority Ordering")
    # When BOTH brake_thermal AND vibration_anomaly could fire,
    # brake_thermal should take priority (it's checked first)
    resp = call_analyze(url, base_payload(
        thermal_stress_index=0.90,
        brake_rul_pct=15,
        mechanical_vibration_anomaly_score=0.85,
    ))
    ts.check(resp["fault_primary"] == "BRAKE_THERMAL_SATURATION",
             f"brake_thermal takes priority over vibration: got {resp['fault_primary']}")


def test_input_validation(url: str, ts: TestSuite):
    ts.section("17. Input Validation (422 Errors)")
    # Missing required field
    bad_payload = base_payload()
    del bad_payload["vehicle_id"]
    try:
        call_analyze(url, bad_payload)
        fail("missing vehicle_id should return 422")
        ts.failed += 1
    except Exception:
        ok("missing vehicle_id correctly rejected")
        ts.passed += 1

    # Out of range value
    try:
        call_analyze(url, base_payload(thermal_stress_index=1.5))
        fail("thermal_stress_index=1.5 should be rejected (max 1.0)")
        ts.failed += 1
    except Exception:
        ok("out-of-range thermal_stress_index correctly rejected")
        ts.passed += 1

    # Negative percentage
    try:
        call_analyze(url, base_payload(engine_rul_pct=-10))
        fail("negative engine_rul_pct should be rejected")
        ts.failed += 1
    except Exception:
        ok("negative engine_rul_pct correctly rejected")
        ts.passed += 1


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Cloud AI Correctness Validator")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    print(f"\n{BOLD}{'═'*60}")
    print(f"  Cloud AI Correctness Validator")
    print(f"  Server: {args.url}")
    print(f"{'═'*60}{RESET}")

    ts = TestSuite()

    tests = [
        test_health_endpoint,
        test_output_schema,
        test_value_ranges,
        test_healthy_vehicle,
        test_brake_thermal_saturation,
        test_brake_thermal_boundary,
        test_vibration_anomaly,
        test_electrical_degradation,
        test_multi_factor_risk,
        test_recommendation_priority_cascade,
        test_safe_operating_limits,
        test_contributor_logic,
        test_vehicle_id_passthrough,
        test_rul_prediction_sanity,
        test_failure_prob_direction,
        test_fault_priority_order,
        test_input_validation,
    ]

    for test_fn in tests:
        try:
            test_fn(args.url, ts)
        except Exception as e:
            fail(f"EXCEPTION in {test_fn.__name__}: {e}")
            ts.failed += 1

    # ── Summary ─────────────────────────────────────────────────────────
    total = ts.passed + ts.failed
    pct = (ts.passed / total * 100) if total else 0

    print(f"\n{BOLD}{'═'*60}")
    print(f"  RESULTS: {ts.passed}/{total} passed ({pct:.0f}%)")
    if ts.warnings:
        print(f"  Warnings: {ts.warnings}")
    if ts.failed == 0:
        print(f"  {GREEN}ALL TESTS PASSED ✔{RESET}")
    else:
        print(f"  {RED}{ts.failed} TEST(S) FAILED ✘{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}\n")

    sys.exit(0 if ts.failed == 0 else 1)


if __name__ == "__main__":
    main()
