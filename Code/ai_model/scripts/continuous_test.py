"""
Continuous Cloud AI Tester
==========================
Sends randomized vehicle telemetry to /analyze every N seconds.
Simulates a range of vehicle conditions: healthy, degrading, and critical.

Usage:
    python scripts/continuous_test.py                     # default: every 3s, infinite
    python scripts/continuous_test.py --interval 1        # every 1s
    python scripts/continuous_test.py --count 20          # send 20 requests then stop
    python scripts/continuous_test.py --url http://host:8000  # custom server URL
"""

import argparse
import json
import random
import time
import sys
from datetime import datetime

try:
    import httpx

    USE_HTTPX = True
except ImportError:
    import urllib.request
    import urllib.error

    USE_HTTPX = False


# ---------------------------------------------------------------------------
# Vehicle scenario profiles
# ---------------------------------------------------------------------------
SCENARIOS = {
    "healthy": {
        "thermal_brake_margin": (0.2, 0.6),
        "thermal_engine_margin": (0.3, 0.7),
        "thermal_stress_index": (0.05, 0.25),
        "mechanical_vibration_anomaly_score": (0.01, 0.15),
        "mechanical_dominant_fault_band_hz": (20, 80),
        "mechanical_vibration_rms": (0.05, 0.20),
        "electrical_charging_efficiency_score": (0.90, 0.99),
        "electrical_battery_health_pct": (90, 100),
        "engine_rul_pct": (70, 100),
        "brake_rul_pct": (70, 100),
        "battery_rul_pct": (80, 100),
        "vehicle_health_score": (0.80, 1.0),
    },
    "degrading": {
        "thermal_brake_margin": (-0.05, 0.15),
        "thermal_engine_margin": (0.10, 0.30),
        "thermal_stress_index": (0.40, 0.65),
        "mechanical_vibration_anomaly_score": (0.35, 0.60),
        "mechanical_dominant_fault_band_hz": (80, 160),
        "mechanical_vibration_rms": (0.40, 0.65),
        "electrical_charging_efficiency_score": (0.70, 0.85),
        "electrical_battery_health_pct": (60, 80),
        "engine_rul_pct": (35, 60),
        "brake_rul_pct": (30, 55),
        "battery_rul_pct": (45, 70),
        "vehicle_health_score": (0.45, 0.65),
    },
    "critical": {
        "thermal_brake_margin": (-0.50, -0.15),
        "thermal_engine_margin": (-0.20, 0.05),
        "thermal_stress_index": (0.80, 1.0),
        "mechanical_vibration_anomaly_score": (0.75, 1.0),
        "mechanical_dominant_fault_band_hz": (140, 300),
        "mechanical_vibration_rms": (0.80, 1.0),
        "electrical_charging_efficiency_score": (0.40, 0.65),
        "electrical_battery_health_pct": (20, 50),
        "engine_rul_pct": (5, 25),
        "brake_rul_pct": (3, 20),
        "battery_rul_pct": (10, 35),
        "vehicle_health_score": (0.10, 0.35),
    },
}

VEHICLE_IDS = [
    "VIT_CAR_001",
    "VIT_CAR_002",
    "VIT_TRUCK_010",
    "VIT_BUS_005",
    "VIT_EV_003",
]


def rand_range(lo, hi):
    return round(random.uniform(lo, hi), 2)


def generate_payload():
    scenario_name = random.choices(
        ["healthy", "degrading", "critical"], weights=[0.3, 0.4, 0.3]
    )[0]
    s = SCENARIOS[scenario_name]
    payload = {
        "vehicle_id": random.choice(VEHICLE_IDS),
        "timestamp_ms": int(time.time() * 1000),
    }
    for key, (lo, hi) in s.items():
        payload[key] = rand_range(lo, hi)
    return scenario_name, payload


def post_analyze(base_url, payload):
    url = f"{base_url}/analyze"
    body = json.dumps(payload).encode()

    if USE_HTTPX:
        with httpx.Client(timeout=10) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            return r.json()
    else:
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())


# ---------------------------------------------------------------------------
# Pretty-print helpers
# ---------------------------------------------------------------------------
SEVERITY_COLORS = {
    "healthy": "\033[92m",   # green
    "degrading": "\033[93m", # yellow
    "critical": "\033[91m",  # red
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def severity_from_response(resp):
    prob = resp.get("fault_failure_probability_7d", 0)
    if prob >= 0.7:
        return "critical"
    elif prob >= 0.3:
        return "degrading"
    return "healthy"


def print_result(idx, scenario, payload, resp, elapsed_ms):
    sev = severity_from_response(resp)
    color = SEVERITY_COLORS.get(sev, "")

    header = f"{BOLD}#{idx:>4}{RESET}  {datetime.now().strftime('%H:%M:%S')}  " \
             f"vehicle={payload['vehicle_id']:<15}  " \
             f"input_scenario={scenario:<10}"
    print(header)

    prob = resp.get("fault_failure_probability_7d", "?")
    fault = resp.get("fault_primary", "NONE")
    priority = resp.get("recommendation", {}).get("recommendation_service_priority", "?")
    action = resp.get("recommendation", {}).get("recommendation_suggested_action", "?")
    limit_km = resp.get("recommendation", {}).get("recommendation_safe_operating_limit_km", "?")
    factors = resp.get("fault_contributing_factors", [])

    print(f"       {color}failure_prob_7d={prob}  fault={fault}  priority={priority}{RESET}")
    print(f"       RUL  engine={resp.get('engine_rul_pct','?')}%  "
          f"brake={resp.get('brake_rul_pct','?')}%  "
          f"battery={resp.get('battery_rul_pct','?')}%")
    if factors:
        print(f"       {DIM}factors: {', '.join(factors)}{RESET}")
    print(f"       action: {action}  safe_limit: {limit_km} km  "
          f"{DIM}({elapsed_ms:.0f}ms){RESET}")
    print(f"       {'─' * 60}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Continuous Cloud AI Tester")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of the API server")
    parser.add_argument("--interval", type=float, default=3.0, help="Seconds between requests")
    parser.add_argument("--count", type=int, default=0, help="Number of requests (0 = infinite)")
    args = parser.parse_args()

    print(f"\n{'='*65}")
    print(f"  Cloud AI Continuous Tester")
    print(f"  Server : {args.url}")
    print(f"  Interval: {args.interval}s   Count: {'infinite' if args.count == 0 else args.count}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*65}\n")

    idx = 0
    stats = {"healthy": 0, "degrading": 0, "critical": 0, "errors": 0}

    try:
        while True:
            idx += 1
            if args.count and idx > args.count:
                break

            scenario, payload = generate_payload()
            try:
                t0 = time.perf_counter()
                resp = post_analyze(args.url, payload)
                elapsed = (time.perf_counter() - t0) * 1000

                sev = severity_from_response(resp)
                stats[sev] = stats.get(sev, 0) + 1
                print_result(idx, scenario, payload, resp, elapsed)

            except Exception as e:
                stats["errors"] += 1
                print(f"{BOLD}#{idx:>4}{RESET}  ERROR: {e}")

            time.sleep(args.interval)

    except KeyboardInterrupt:
        pass

    total = sum(v for k, v in stats.items() if k != "errors")
    print(f"\n{'='*65}")
    print(f"  Summary: {total} requests  |  "
          f"🟢 {stats['healthy']}  🟡 {stats['degrading']}  🔴 {stats['critical']}  "
          f"❌ {stats['errors']} errors")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
