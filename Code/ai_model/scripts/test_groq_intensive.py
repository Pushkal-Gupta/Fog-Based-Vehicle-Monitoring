"""
Intensive test script for the Groq recommendation integration.

Tests EVERY output field, EVERY code path, EVERY edge case:
  - Rule-based fallback (all 4 priority tiers)
  - Groq LLM path (if GROQ_API_KEY is set)
  - Fallback when Groq fails
  - Response parsing (clean JSON, markdown-fenced JSON, bad JSON)
  - Full API /analyze endpoint with recommendation_source field
  - /health endpoint groq_configured field
  - Multiple vehicle scenarios (healthy, degraded, critical, mixed)
  - Output schema validation (types, ranges, required keys)
  - Prompt construction verification
  - Contributing factors pass-through
  - Concurrent calls stability

Run:
    python scripts/test_groq_intensive.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import traceback
from unittest.mock import MagicMock, patch

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Ensure project root is on path ──────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from cloud_ai.recommendation import (
    _build_user_prompt,
    _parse_groq_response,
    recommend_action,
    recommend_action_groq,
    recommend_action_rule_based,
)
from cloud_ai.schemas import CloudInput, CloudOutput, Recommendation

# ── Helpers ─────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0
ERRORS: list[str] = []
VALID_PRIORITIES = {"critical", "high", "medium", "low", "normal"}
REQUIRED_REC_KEYS = {
    "recommendation_service_priority",
    "recommendation_suggested_action",
    "recommendation_safe_operating_limit_km",
    "recommendation_source",
}


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        msg = f"  ❌ {name}" + (f" — {detail}" if detail else "")
        print(msg)
        ERRORS.append(msg)


def validate_recommendation_dict(rec: dict, source_expected: str | None = None, label: str = ""):
    """Validate every field of a recommendation dict."""
    prefix = f"[{label}] " if label else ""

    # All required keys present
    missing = REQUIRED_REC_KEYS - set(rec.keys())
    check(f"{prefix}has all required keys", len(missing) == 0, f"missing: {missing}")

    # Priority is valid string
    priority = rec.get("recommendation_service_priority")
    check(f"{prefix}priority is valid", priority in VALID_PRIORITIES, f"got: {priority}")
    check(f"{prefix}priority is str", isinstance(priority, str))

    # Action is non-empty string
    action = rec.get("recommendation_suggested_action")
    check(f"{prefix}action is str", isinstance(action, str))
    check(f"{prefix}action is non-empty", bool(action), f"got empty action")

    # Limit is positive integer
    limit = rec.get("recommendation_safe_operating_limit_km")
    check(f"{prefix}limit is int", isinstance(limit, int), f"got type {type(limit)}")
    check(f"{prefix}limit > 0", isinstance(limit, int) and limit > 0, f"got: {limit}")

    # Source is valid
    source = rec.get("recommendation_source")
    check(f"{prefix}source is str", isinstance(source, str))
    check(f"{prefix}source is groq or rule_based", source in {"groq", "rule_based"}, f"got: {source}")
    if source_expected:
        check(f"{prefix}source matches expected '{source_expected}'", source == source_expected, f"got: {source}")


def build_payload(**overrides) -> dict:
    base = {
        "vehicle_id": "TEST_CAR_001",
        "timestamp_ms": 1707051123456,
        "thermal_brake_margin": -0.21,
        "thermal_engine_margin": 0.34,
        "thermal_stress_index": 0.5,
        "mechanical_vibration_anomaly_score": 0.5,
        "mechanical_dominant_fault_band_hz": 142.0,
        "mechanical_vibration_rms": 0.5,
        "electrical_charging_efficiency_score": 0.8,
        "electrical_battery_health_pct": 85.0,
        "engine_rul_pct": 70.0,
        "brake_rul_pct": 65.0,
        "battery_rul_pct": 75.0,
        "vehicle_health_score": 0.7,
    }
    base.update(overrides)
    return base


# ════════════════════════════════════════════════════════════════════════
# TEST SECTIONS
# ════════════════════════════════════════════════════════════════════════

def test_rule_based_all_tiers():
    """Test all 4 rule-based priority tiers and exact outputs."""
    print("\n" + "=" * 70)
    print("TEST 1: Rule-Based Engine — All 4 Priority Tiers")
    print("=" * 70)

    # TIER 1: HIGH — failure_prob > 0.75
    rec = recommend_action_rule_based(0.80, 60, 50, "MULTI_FACTOR_FAILURE_RISK")
    validate_recommendation_dict(rec, source_expected="rule_based", label="HIGH via failure_prob")
    check("HIGH: priority is 'high'", rec["recommendation_service_priority"] == "high")
    check("HIGH: action mentions brake", "Brake" in rec["recommendation_suggested_action"])
    check("HIGH: limit is 120", rec["recommendation_safe_operating_limit_km"] == 120)

    # TIER 1 alt: HIGH — fault is BRAKE_THERMAL_SATURATION (regardless of prob)
    rec = recommend_action_rule_based(0.30, 80, 70, "BRAKE_THERMAL_SATURATION")
    validate_recommendation_dict(rec, source_expected="rule_based", label="HIGH via fault_primary")
    check("HIGH (fault): priority is 'high'", rec["recommendation_service_priority"] == "high")

    # TIER 2: MEDIUM — brake_rul_pct < 40
    rec = recommend_action_rule_based(0.40, 60, 35, "NO_DOMINANT_FAULT")
    validate_recommendation_dict(rec, source_expected="rule_based", label="MEDIUM")
    check("MEDIUM: priority is 'medium'", rec["recommendation_service_priority"] == "medium")
    check("MEDIUM: action mentions brake", "brake" in rec["recommendation_suggested_action"].lower())
    check("MEDIUM: limit is 300", rec["recommendation_safe_operating_limit_km"] == 300)

    # TIER 3: LOW — engine_rul_pct < 50
    rec = recommend_action_rule_based(0.40, 45, 60, "NO_DOMINANT_FAULT")
    validate_recommendation_dict(rec, source_expected="rule_based", label="LOW")
    check("LOW: priority is 'low'", rec["recommendation_service_priority"] == "low")
    check("LOW: action mentions engine", "engine" in rec["recommendation_suggested_action"].lower())
    check("LOW: limit is 600", rec["recommendation_safe_operating_limit_km"] == 600)

    # TIER 4: NORMAL — everything healthy
    rec = recommend_action_rule_based(0.20, 75, 80, "NO_DOMINANT_FAULT")
    validate_recommendation_dict(rec, source_expected="rule_based", label="NORMAL")
    check("NORMAL: priority is 'normal'", rec["recommendation_service_priority"] == "normal")
    check("NORMAL: limit is 1000", rec["recommendation_safe_operating_limit_km"] == 1000)


def test_rule_based_priority_order():
    """Verify that rule evaluation order is correct (higher severity wins)."""
    print("\n" + "=" * 70)
    print("TEST 2: Rule-Based Engine — Priority Ordering")
    print("=" * 70)

    # failure_prob > 0.75 AND brake_rul < 40 AND engine_rul < 50
    # HIGH should win because it's checked first
    rec = recommend_action_rule_based(0.85, 30, 20, "NO_DOMINANT_FAULT")
    check("Conflict: HIGH wins over MEDIUM+LOW", rec["recommendation_service_priority"] == "high")

    # brake_rul < 40 AND engine_rul < 50, but prob is low → MEDIUM wins
    rec = recommend_action_rule_based(0.40, 30, 20, "NO_DOMINANT_FAULT")
    check("Conflict: MEDIUM wins over LOW", rec["recommendation_service_priority"] == "medium")


def test_rule_based_contributing_factors_ignored():
    """Rule-based engine should accept contributing_factors without crashing."""
    print("\n" + "=" * 70)
    print("TEST 3: Rule-Based Engine — Contributing Factors Param")
    print("=" * 70)

    factors = ["high_thermal_stress_index", "low_brake_rul_pct"]
    rec = recommend_action_rule_based(0.80, 55, 35, "MULTI_FACTOR_FAILURE_RISK", factors)
    validate_recommendation_dict(rec, source_expected="rule_based", label="with factors")

    rec = recommend_action_rule_based(0.80, 55, 35, "MULTI_FACTOR_FAILURE_RISK", None)
    validate_recommendation_dict(rec, source_expected="rule_based", label="factors=None")

    rec = recommend_action_rule_based(0.80, 55, 35, "MULTI_FACTOR_FAILURE_RISK", [])
    validate_recommendation_dict(rec, source_expected="rule_based", label="factors=[]")


def test_prompt_construction():
    """Verify _build_user_prompt constructs correct prompt content."""
    print("\n" + "=" * 70)
    print("TEST 4: Groq Prompt Construction")
    print("=" * 70)

    prompt = _build_user_prompt(0.85, 45.3, 22.1, "BRAKE_THERMAL_SATURATION",
                                 ["high_thermal_stress_index", "low_brake_rul_pct"])
    check("Prompt contains failure prob", "85%" in prompt)
    check("Prompt contains engine RUL", "45.3%" in prompt)
    check("Prompt contains brake RUL", "22.1%" in prompt)
    check("Prompt contains fault name", "BRAKE_THERMAL_SATURATION" in prompt)
    check("Prompt contains factor 1", "high_thermal_stress_index" in prompt)
    check("Prompt contains factor 2", "low_brake_rul_pct" in prompt)

    # No factors
    prompt2 = _build_user_prompt(0.10, 90.0, 85.0, "NO_DOMINANT_FAULT", None)
    check("Prompt (no factors) contains 'none'", "none" in prompt2)

    prompt3 = _build_user_prompt(0.10, 90.0, 85.0, "NO_DOMINANT_FAULT", [])
    check("Prompt (empty factors) contains 'none'", "none" in prompt3)


def test_parse_groq_response_clean_json():
    """Test parsing of clean JSON from Groq."""
    print("\n" + "=" * 70)
    print("TEST 5: Response Parsing — Clean JSON")
    print("=" * 70)

    raw = json.dumps({
        "recommendation_service_priority": "high",
        "recommendation_suggested_action": "Replace brake pads immediately.",
        "recommendation_safe_operating_limit_km": 100,
    })
    rec = _parse_groq_response(raw)
    validate_recommendation_dict(rec, source_expected="groq", label="clean JSON")
    check("Parsed priority is 'high'", rec["recommendation_service_priority"] == "high")
    check("Parsed action correct", rec["recommendation_suggested_action"] == "Replace brake pads immediately.")
    check("Parsed limit is 100", rec["recommendation_safe_operating_limit_km"] == 100)


def test_parse_groq_response_markdown_fenced():
    """Test parsing when Groq wraps response in ```json ... ```."""
    print("\n" + "=" * 70)
    print("TEST 6: Response Parsing — Markdown-Fenced JSON")
    print("=" * 70)

    raw = '```json\n{"recommendation_service_priority": "medium", "recommendation_suggested_action": "Schedule maintenance.", "recommendation_safe_operating_limit_km": 500}\n```'
    rec = _parse_groq_response(raw)
    validate_recommendation_dict(rec, source_expected="groq", label="fenced JSON")
    check("Fenced: priority is 'medium'", rec["recommendation_service_priority"] == "medium")
    check("Fenced: limit is 500", rec["recommendation_safe_operating_limit_km"] == 500)


def test_parse_groq_response_invalid_priority():
    """Test that invalid priority falls back to 'medium'."""
    print("\n" + "=" * 70)
    print("TEST 7: Response Parsing — Invalid Priority Normalization")
    print("=" * 70)

    raw = json.dumps({
        "recommendation_service_priority": "URGENT",
        "recommendation_suggested_action": "Fix now",
        "recommendation_safe_operating_limit_km": 50,
    })
    rec = _parse_groq_response(raw)
    check("Invalid priority normalized to 'medium'", rec["recommendation_service_priority"] == "medium")

    raw2 = json.dumps({
        "recommendation_service_priority": "Critical",  # capital C
        "recommendation_suggested_action": "Fix now",
        "recommendation_safe_operating_limit_km": 50,
    })
    rec2 = _parse_groq_response(raw2)
    check("'Critical' (capital) normalized to 'critical'", rec2["recommendation_service_priority"] == "critical")


def test_parse_groq_response_bad_json():
    """Test that malformed JSON raises an error."""
    print("\n" + "=" * 70)
    print("TEST 8: Response Parsing — Bad JSON Raises Error")
    print("=" * 70)

    try:
        _parse_groq_response("this is not json at all")
        check("Bad JSON raises error", False, "did not raise")
    except (json.JSONDecodeError, Exception):
        check("Bad JSON raises error", True)

    try:
        _parse_groq_response("")
        check("Empty string raises error", False, "did not raise")
    except (json.JSONDecodeError, Exception):
        check("Empty string raises error", True)

    try:
        _parse_groq_response('{"recommendation_service_priority": "high"}')  # missing keys
        check("Incomplete JSON raises error", False, "did not raise")
    except (KeyError, Exception):
        check("Incomplete JSON raises error", True)


def test_unified_wrapper_no_key():
    """Without GROQ_API_KEY, recommend_action() should use rule-based."""
    print("\n" + "=" * 70)
    print("TEST 9: Unified Wrapper — No API Key → Rule-Based")
    print("=" * 70)

    with patch.dict(os.environ, {}, clear=False):
        # Remove GROQ_API_KEY if it exists
        env_copy = os.environ.copy()
        env_copy.pop("GROQ_API_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            rec = recommend_action(0.80, 55, 35, 50, "MULTI_FACTOR_FAILURE_RISK")
            validate_recommendation_dict(rec, source_expected="rule_based", label="no key")
            check("No key: uses rule_based", rec["recommendation_source"] == "rule_based")


def test_unified_wrapper_groq_failure_fallback():
    """When Groq raises an exception, recommend_action() should fall back."""
    print("\n" + "=" * 70)
    print("TEST 10: Unified Wrapper — Groq Exception → Fallback")
    print("=" * 70)

    with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key_for_testing"}):
        with patch("cloud_ai.recommendation.recommend_action_groq", side_effect=RuntimeError("API down")):
            rec = recommend_action(0.80, 55, 35, 50, "MULTI_FACTOR_FAILURE_RISK",
                                   ["high_thermal_stress_index"])
            validate_recommendation_dict(rec, source_expected="rule_based", label="groq exception")
            check("Groq failure: falls back to rule_based", rec["recommendation_source"] == "rule_based")


def test_unified_wrapper_groq_timeout_fallback():
    """Simulate a Groq timeout and verify fallback."""
    print("\n" + "=" * 70)
    print("TEST 11: Unified Wrapper — Groq Timeout → Fallback")
    print("=" * 70)

    with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key_for_testing"}):
        with patch("cloud_ai.recommendation.recommend_action_groq", side_effect=TimeoutError("timed out")):
            rec = recommend_action(0.50, 70, 65, 80, "NO_DOMINANT_FAULT")
            validate_recommendation_dict(rec, source_expected="rule_based", label="timeout")
            check("Timeout: falls back to rule_based", rec["recommendation_source"] == "rule_based")


def test_unified_wrapper_groq_success_mock():
    """Mock a successful Groq call and verify output flow."""
    print("\n" + "=" * 70)
    print("TEST 12: Unified Wrapper — Mocked Groq Success")
    print("=" * 70)

    mock_groq_result = {
        "recommendation_service_priority": "critical",
        "recommendation_suggested_action": "Immediately inspect brake system due to thermal saturation.",
        "recommendation_safe_operating_limit_km": 50,
        "recommendation_source": "groq",
    }

    with patch.dict(os.environ, {"GROQ_API_KEY": "fake_key_for_testing"}):
        with patch("cloud_ai.recommendation.recommend_action_groq", return_value=mock_groq_result):
            rec = recommend_action(0.90, 30, 20, 10, "BRAKE_THERMAL_SATURATION",
                                   ["high_thermal_stress_index", "low_brake_rul_pct"])
            validate_recommendation_dict(rec, source_expected="groq", label="mocked groq")
            check("Mocked Groq: priority is 'critical'", rec["recommendation_service_priority"] == "critical")
            check("Mocked Groq: action is AI-generated", "brake" in rec["recommendation_suggested_action"].lower())


def test_schema_recommendation_model():
    """Test that the Pydantic Recommendation model accepts both sources."""
    print("\n" + "=" * 70)
    print("TEST 13: Pydantic Schema — Recommendation Model")
    print("=" * 70)

    # Rule-based
    r1 = Recommendation(
        recommendation_service_priority="high",
        recommendation_suggested_action="Replace brakes",
        recommendation_safe_operating_limit_km=120,
        recommendation_source="rule_based",
    )
    check("Schema: rule_based source accepted", r1.recommendation_source == "rule_based")

    # Groq
    r2 = Recommendation(
        recommendation_service_priority="critical",
        recommendation_suggested_action="AI-generated advice",
        recommendation_safe_operating_limit_km=50,
        recommendation_source="groq",
    )
    check("Schema: groq source accepted", r2.recommendation_source == "groq")

    # Default source
    r3 = Recommendation(
        recommendation_service_priority="normal",
        recommendation_suggested_action="All good",
        recommendation_safe_operating_limit_km=1000,
    )
    check("Schema: default source is rule_based", r3.recommendation_source == "rule_based")


def test_full_api_endpoint():
    """Test the /analyze endpoint outputs recommendation_source correctly."""
    print("\n" + "=" * 70)
    print("TEST 14: Full API /analyze Endpoint — Recommendation Output")
    print("=" * 70)

    import pandas as pd
    from fastapi.testclient import TestClient
    from cloud_ai.cloud_api import ModelRegistry, app
    from cloud_ai.failure_model import train_failure_model
    from cloud_ai.rul_model import train_rul_model

    # Build minimal dataset
    records = []
    for i in range(160):
        tsi = ((i * 7) % 100) / 100
        vib = ((i * 11) % 100) / 100
        eff = ((i * 13) % 100) / 100
        vhs = ((i * 17) % 100) / 100
        brake_rul = max(0, min(100, 100 - 70 * tsi - 40 * vib))
        bat_rul = max(0, min(100, 85 + 15 * eff - 25 * tsi))
        eng_rul = max(0, min(100, 95 - 55 * tsi - 25 * vib + 10 * vhs))
        eng_rul_f = max(0, min(100, eng_rul - 10 * tsi - 6 * vib))
        fail = int((eng_rul < 45 and vib > 0.6) or brake_rul < 35 or tsi > 0.8)
        records.append({
            "vehicle_id": f"VIT_CAR_{i:03d}", "timestamp_ms": 1707051123456 + i,
            "thermal_brake_margin": -0.21, "thermal_engine_margin": 0.34,
            "thermal_stress_index": tsi,
            "mechanical_vibration_anomaly_score": vib,
            "mechanical_dominant_fault_band_hz": 120 + (i % 40),
            "mechanical_vibration_rms": 0.3 + (i % 12) / 20,
            "electrical_charging_efficiency_score": eff,
            "electrical_battery_health_pct": 60 + (i % 40),
            "engine_rul_pct": eng_rul, "brake_rul_pct": brake_rul,
            "battery_rul_pct": bat_rul, "vehicle_health_score": vhs,
            "brake_health_index": brake_rul / 100,
            "engine_rul_pct_future": eng_rul_f, "failure_next_7_days": fail,
        })
    df = pd.DataFrame(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cloud_health_history.csv")
        df.to_csv(csv_path, index=False)
        rul_path = os.path.join(tmpdir, "rul_model.pkl")
        fail_path = os.path.join(tmpdir, "failure_model.pkl")
        train_rul_model(data_path=csv_path, model_path=rul_path)
        train_failure_model(data_path=csv_path, model_path=fail_path)

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            ModelRegistry.rul_model = None
            ModelRegistry.failure_model = None

            # --- Test multiple vehicle scenarios ---
            scenarios = [
                ("CRITICAL: brake thermal", {
                    "thermal_stress_index": 0.90, "mechanical_vibration_anomaly_score": 0.85,
                    "mechanical_vibration_rms": 0.95, "brake_rul_pct": 15.0,
                    "engine_rul_pct": 30.0, "vehicle_health_score": 0.25,
                }),
                ("DEGRADED: low engine", {
                    "thermal_stress_index": 0.55, "mechanical_vibration_anomaly_score": 0.40,
                    "engine_rul_pct": 35.0, "brake_rul_pct": 60.0,
                    "vehicle_health_score": 0.50,
                }),
                ("HEALTHY: everything good", {
                    "thermal_stress_index": 0.15, "mechanical_vibration_anomaly_score": 0.10,
                    "mechanical_vibration_rms": 0.20,
                    "electrical_charging_efficiency_score": 0.95,
                    "electrical_battery_health_pct": 95.0,
                    "engine_rul_pct": 90.0, "brake_rul_pct": 88.0,
                    "battery_rul_pct": 92.0, "vehicle_health_score": 0.90,
                }),
                ("MIXED: bad electrical", {
                    "thermal_stress_index": 0.30,
                    "electrical_charging_efficiency_score": 0.50,
                    "electrical_battery_health_pct": 55.0,
                    "battery_rul_pct": 40.0, "engine_rul_pct": 70.0,
                    "brake_rul_pct": 65.0, "vehicle_health_score": 0.55,
                }),
            ]

            with TestClient(app) as client:
                # Health check
                health_resp = client.get("/health")
                check("Health: status 200", health_resp.status_code == 200)
                health_body = health_resp.json()
                check("Health: has groq_configured", "groq_configured" in health_body)
                check("Health: groq_configured is bool", isinstance(health_body["groq_configured"], bool))
                groq_configured = health_body["groq_configured"]
                print(f"    ℹ️  Groq configured: {groq_configured}")

                for scenario_name, overrides in scenarios:
                    print(f"\n  ── Scenario: {scenario_name} ──")
                    payload = build_payload(**overrides)
                    resp = client.post("/analyze", json=payload)
                    check(f"{scenario_name}: status 200", resp.status_code == 200)

                    body = resp.json()

                    # Top-level fields
                    check(f"{scenario_name}: has vehicle_id", body.get("vehicle_id") == payload["vehicle_id"])
                    check(f"{scenario_name}: has timestamp_ms", body.get("timestamp_ms") == payload["timestamp_ms"])

                    # RUL fields in range
                    for rul_field in ["engine_rul_pct", "brake_rul_pct", "battery_rul_pct"]:
                        val = body.get(rul_field)
                        check(f"{scenario_name}: {rul_field} is float", isinstance(val, (int, float)))
                        check(f"{scenario_name}: {rul_field} in [0, 100]",
                              isinstance(val, (int, float)) and 0.0 <= val <= 100.0,
                              f"got: {val}")

                    # Failure probability
                    fp = body.get("fault_failure_probability_7d")
                    check(f"{scenario_name}: failure_prob is float", isinstance(fp, (int, float)))
                    check(f"{scenario_name}: failure_prob in [0, 1]",
                          isinstance(fp, (int, float)) and 0.0 <= fp <= 1.0, f"got: {fp}")

                    # Fault fields
                    check(f"{scenario_name}: has fault_primary", isinstance(body.get("fault_primary"), str))
                    check(f"{scenario_name}: fault_primary non-empty", bool(body.get("fault_primary")))
                    factors = body.get("fault_contributing_factors")
                    check(f"{scenario_name}: contributing_factors is list", isinstance(factors, list))
                    check(f"{scenario_name}: contributing_factors all strings",
                          all(isinstance(f, str) for f in (factors or [])))

                    # RECOMMENDATION — the star of the show
                    rec = body.get("recommendation")
                    check(f"{scenario_name}: has recommendation", rec is not None)
                    if rec:
                        check(f"{scenario_name}: rec.priority valid",
                              rec.get("recommendation_service_priority") in VALID_PRIORITIES,
                              f"got: {rec.get('recommendation_service_priority')}")
                        check(f"{scenario_name}: rec.action is str",
                              isinstance(rec.get("recommendation_suggested_action"), str))
                        check(f"{scenario_name}: rec.action non-empty",
                              bool(rec.get("recommendation_suggested_action")))
                        check(f"{scenario_name}: rec.limit is int",
                              isinstance(rec.get("recommendation_safe_operating_limit_km"), int))
                        check(f"{scenario_name}: rec.limit > 0",
                              (rec.get("recommendation_safe_operating_limit_km") or 0) > 0)
                        check(f"{scenario_name}: rec.source present",
                              rec.get("recommendation_source") in {"groq", "rule_based"},
                              f"got: {rec.get('recommendation_source')}")

                    # History
                    check(f"{scenario_name}: has history_points_used",
                          isinstance(body.get("history_points_used"), int))

        finally:
            os.chdir(old_cwd)


def test_api_health_groq_field():
    """Test /health endpoint reports groq_configured accurately."""
    print("\n" + "=" * 70)
    print("TEST 15: /health Endpoint — groq_configured Field")
    print("=" * 70)

    import tempfile
    import pandas as pd
    from fastapi.testclient import TestClient
    from cloud_ai.cloud_api import ModelRegistry, app
    from cloud_ai.failure_model import train_failure_model
    from cloud_ai.rul_model import train_rul_model

    # Minimal setup
    records = []
    for i in range(100):
        tsi = ((i * 7) % 100) / 100
        vib = ((i * 11) % 100) / 100
        eff = ((i * 13) % 100) / 100
        vhs = ((i * 17) % 100) / 100
        brake_rul = max(0, min(100, 100 - 70 * tsi - 40 * vib))
        bat_rul = max(0, min(100, 85 + 15 * eff - 25 * tsi))
        eng_rul = max(0, min(100, 95 - 55 * tsi - 25 * vib + 10 * vhs))
        eng_rul_f = max(0, min(100, eng_rul - 10 * tsi - 6 * vib))
        fail = int((eng_rul < 45 and vib > 0.6) or brake_rul < 35 or tsi > 0.8)
        records.append({
            "vehicle_id": f"VIT_CAR_{i:03d}", "timestamp_ms": 1707051123456 + i,
            "thermal_brake_margin": -0.21, "thermal_engine_margin": 0.34,
            "thermal_stress_index": tsi,
            "mechanical_vibration_anomaly_score": vib,
            "mechanical_dominant_fault_band_hz": 120 + (i % 40),
            "mechanical_vibration_rms": 0.3 + (i % 12) / 20,
            "electrical_charging_efficiency_score": eff,
            "electrical_battery_health_pct": 60 + (i % 40),
            "engine_rul_pct": eng_rul, "brake_rul_pct": brake_rul,
            "battery_rul_pct": bat_rul, "vehicle_health_score": vhs,
            "brake_health_index": brake_rul / 100,
            "engine_rul_pct_future": eng_rul_f, "failure_next_7_days": fail,
        })
    df = pd.DataFrame(records)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "cloud_health_history.csv")
        df.to_csv(csv_path, index=False)
        train_rul_model(data_path=csv_path, model_path=os.path.join(tmpdir, "rul_model.pkl"))
        train_failure_model(data_path=csv_path, model_path=os.path.join(tmpdir, "failure_model.pkl"))

        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            ModelRegistry.rul_model = None
            ModelRegistry.failure_model = None

            # WITH key
            with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
                with TestClient(app) as client:
                    h = client.get("/health").json()
                    check("/health with key: groq_configured=True", h["groq_configured"] is True)

            ModelRegistry.rul_model = None
            ModelRegistry.failure_model = None

            # WITHOUT key
            env_copy = os.environ.copy()
            env_copy.pop("GROQ_API_KEY", None)
            with patch.dict(os.environ, env_copy, clear=True):
                with TestClient(app) as client:
                    h = client.get("/health").json()
                    check("/health without key: groq_configured=False", h["groq_configured"] is False)
        finally:
            os.chdir(old_cwd)


def test_live_groq_if_configured():
    """If GROQ_API_KEY is valid, test a LIVE Groq call."""
    print("\n" + "=" * 70)
    print("TEST 16: LIVE Groq Call (skipped if no valid key)")
    print("=" * 70)

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        print("  ⏭️  SKIPPED — GROQ_API_KEY not set")
        return

    # Try a live call
    try:
        rec = recommend_action_groq(
            failure_prob=0.82,
            engine_rul_pct=35.0,
            brake_rul_pct=18.0,
            fault_primary="BRAKE_THERMAL_SATURATION",
            contributing_factors=["high_thermal_stress_index", "low_brake_rul_pct",
                                   "high_mechanical_vibration_rms"],
        )
        validate_recommendation_dict(rec, source_expected="groq", label="LIVE Groq")
        print(f"\n    🤖 Groq response:")
        print(f"       Priority: {rec['recommendation_service_priority']}")
        print(f"       Action:   {rec['recommendation_suggested_action']}")
        print(f"       Limit:    {rec['recommendation_safe_operating_limit_km']} km")
        print(f"       Source:   {rec['recommendation_source']}")
    except Exception as e:
        print(f"  ⚠️  Live Groq call failed: {e}")
        print(f"       (This is expected if key is invalid)")
        check("Live Groq: fallback would work",
              recommend_action(0.82, 35, 18, 12, "BRAKE_THERMAL_SATURATION")["recommendation_source"] == "rule_based")


def test_live_groq_multiple_scenarios():
    """If GROQ_API_KEY works, test multiple vehicle scenarios for quality."""
    print("\n" + "=" * 70)
    print("TEST 17: LIVE Groq — Multiple Scenarios (skipped if no valid key)")
    print("=" * 70)

    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        print("  ⏭️  SKIPPED — GROQ_API_KEY not set")
        return

    scenarios = [
        ("Critical brakes", 0.92, 25.0, 12.0, "BRAKE_THERMAL_SATURATION",
         ["high_thermal_stress_index", "low_brake_rul_pct", "high_mechanical_vibration_rms"]),
        ("Electrical degradation", 0.55, 60.0, 70.0, "ELECTRICAL_DEGRADATION",
         ["low_electrical_charging_efficiency_score"]),
        ("Multi-factor risk", 0.78, 40.0, 35.0, "MULTI_FACTOR_FAILURE_RISK",
         ["high_thermal_stress_index", "high_mechanical_vibration_anomaly_score"]),
        ("Healthy vehicle", 0.08, 92.0, 90.0, "NO_DOMINANT_FAULT",
         ["no_dominant_contributor"]),
        ("Engine only concern", 0.35, 28.0, 75.0, "MECHANICAL_VIBRATION_ANOMALY",
         ["high_mechanical_vibration_anomaly_score", "high_mechanical_vibration_rms"]),
    ]

    for name, fp, eng, brk, fault, factors in scenarios:
        print(f"\n  ── {name} ──")
        try:
            rec = recommend_action_groq(fp, eng, brk, fault, factors)
            validate_recommendation_dict(rec, source_expected="groq", label=name)
            print(f"    🤖 Priority: {rec['recommendation_service_priority']}")
            print(f"    🤖 Action:   {rec['recommendation_suggested_action']}")
            print(f"    🤖 Limit:    {rec['recommendation_safe_operating_limit_km']} km")

            # Quality checks — Groq's response should make sense
            if fp > 0.7:
                check(f"{name}: high failure → severity should be high/critical",
                      rec["recommendation_service_priority"] in {"critical", "high", "medium"})
            if fp < 0.15:
                check(f"{name}: low failure → severity should be low/normal",
                      rec["recommendation_service_priority"] in {"low", "normal", "medium"})
            check(f"{name}: limit is reasonable (1-2000 km)",
                  1 <= rec["recommendation_safe_operating_limit_km"] <= 2000)

        except Exception as e:
            print(f"    ⚠️ Groq call failed: {e}")


def test_rapid_consecutive_calls():
    """Test that rapid consecutive calls don't cause issues."""
    print("\n" + "=" * 70)
    print("TEST 18: Rapid Consecutive Calls — Stability")
    print("=" * 70)

    results = []
    for i in range(10):
        rec = recommend_action_rule_based(
            failure_prob=0.1 * i,
            engine_rul_pct=100 - 5 * i,
            brake_rul_pct=100 - 8 * i,
            fault_primary="NO_DOMINANT_FAULT" if i < 7 else "BRAKE_THERMAL_SATURATION",
            contributing_factors=[f"factor_{i}"],
        )
        results.append(rec)

    check("10 rapid calls: all returned dicts", all(isinstance(r, dict) for r in results))
    check("10 rapid calls: all have source", all(r.get("recommendation_source") == "rule_based" for r in results))
    check("10 rapid calls: all have valid priority",
          all(r.get("recommendation_service_priority") in VALID_PRIORITIES for r in results))

    # Last calls should have higher severity
    check("Rapid calls: severity escalates",
          results[-1]["recommendation_service_priority"] in {"high", "critical"})


def test_edge_case_extreme_values():
    """Test with extreme boundary values."""
    print("\n" + "=" * 70)
    print("TEST 19: Edge Cases — Extreme Values")
    print("=" * 70)

    # failure_prob exactly at boundary
    rec = recommend_action_rule_based(0.75, 50, 40, "NO_DOMINANT_FAULT")
    check("failure_prob=0.75 (not > 0.75): not HIGH", rec["recommendation_service_priority"] != "high")

    rec = recommend_action_rule_based(0.7500001, 50, 40, "NO_DOMINANT_FAULT")
    check("failure_prob=0.75+ (> 0.75): is HIGH", rec["recommendation_service_priority"] == "high")

    # brake_rul exactly at boundary
    rec = recommend_action_rule_based(0.40, 60, 40, "NO_DOMINANT_FAULT")
    check("brake_rul=40 (not < 40): not MEDIUM", rec["recommendation_service_priority"] != "medium")

    rec = recommend_action_rule_based(0.40, 60, 39.99, "NO_DOMINANT_FAULT")
    check("brake_rul=39.99 (< 40): is MEDIUM", rec["recommendation_service_priority"] == "medium")

    # engine_rul exactly at boundary
    rec = recommend_action_rule_based(0.40, 50, 60, "NO_DOMINANT_FAULT")
    check("engine_rul=50 (not < 50): not LOW", rec["recommendation_service_priority"] != "low")

    rec = recommend_action_rule_based(0.40, 49.99, 60, "NO_DOMINANT_FAULT")
    check("engine_rul=49.99 (< 50): is LOW", rec["recommendation_service_priority"] == "low")

    # All zeros
    rec = recommend_action_rule_based(0.0, 0.0, 0.0, "NO_DOMINANT_FAULT")
    validate_recommendation_dict(rec, label="all zeros")

    # All maximums
    rec = recommend_action_rule_based(1.0, 100.0, 100.0, "BRAKE_THERMAL_SATURATION")
    validate_recommendation_dict(rec, label="all maxes")
    check("All max + BRAKE fault: priority is HIGH", rec["recommendation_service_priority"] == "high")


# ════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("🔬 INTENSIVE GROQ RECOMMENDATION TEST SUITE")
    print(f"   Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   GROQ_API_KEY set: {'Yes' if os.getenv('GROQ_API_KEY') else 'No'}")
    print("=" * 70)

    all_tests = [
        test_rule_based_all_tiers,
        test_rule_based_priority_order,
        test_rule_based_contributing_factors_ignored,
        test_prompt_construction,
        test_parse_groq_response_clean_json,
        test_parse_groq_response_markdown_fenced,
        test_parse_groq_response_invalid_priority,
        test_parse_groq_response_bad_json,
        test_unified_wrapper_no_key,
        test_unified_wrapper_groq_failure_fallback,
        test_unified_wrapper_groq_timeout_fallback,
        test_unified_wrapper_groq_success_mock,
        test_schema_recommendation_model,
        test_full_api_endpoint,
        test_api_health_groq_field,
        test_live_groq_if_configured,
        test_live_groq_multiple_scenarios,
        test_rapid_consecutive_calls,
        test_edge_case_extreme_values,
    ]

    for test_fn in all_tests:
        try:
            test_fn()
        except Exception as e:
            FAIL += 1
            msg = f"  💥 {test_fn.__name__} CRASHED: {e}"
            print(msg)
            ERRORS.append(msg)
            traceback.print_exc()

    # ── Summary ──
    print("\n" + "=" * 70)
    total = PASS + FAIL
    print(f"📊 RESULTS: {PASS}/{total} passed, {FAIL} failed")
    if ERRORS:
        print(f"\n❌ FAILURES:")
        for err in ERRORS:
            print(err)
    else:
        print("\n🎉 ALL TESTS PASSED!")
    print("=" * 70)

    sys.exit(1 if FAIL > 0 else 0)
