"""Maintenance recommendation engine with Groq LLM primary and rule-based fallback."""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rule-based fallback (original logic, always available)
# ---------------------------------------------------------------------------

def recommend_action_rule_based(
    failure_prob: float,
    engine_rul_pct: float,
    brake_rul_pct: float,
    battery_rul_pct: float,
    fault_primary: str,
    contributing_factors: list[str] | None = None,
) -> dict[str, str | int]:
    # High risk or specific critical fault
    if failure_prob > 0.75 or fault_primary == "BRAKE_THERMAL_SATURATION":
        return {
            "recommendation_service_priority": "high",
            "recommendation_suggested_action": "Brake inspection and pad replacement",
            "recommendation_safe_operating_limit_km": 120,
            "recommendation_source": "rule_based",
        }

    # Low brake RUL
    if brake_rul_pct < 20:
        return {
            "recommendation_service_priority": "high",
            "recommendation_suggested_action": "Immediate brake service required. Do not delay.",
            "recommendation_safe_operating_limit_km": 50,
            "recommendation_source": "rule_based",
        }
    elif brake_rul_pct < 40:
        return {
            "recommendation_service_priority": "medium",
            "recommendation_suggested_action": "Schedule brake maintenance within 2 weeks",
            "recommendation_safe_operating_limit_km": 300,
            "recommendation_source": "rule_based",
        }

    # Low engine RUL
    if engine_rul_pct < 20:
        return {
            "recommendation_service_priority": "high",
            "recommendation_suggested_action": "Engine health critical. Immediate diagnostic recommended.",
            "recommendation_safe_operating_limit_km": 100,
            "recommendation_source": "rule_based",
        }
    elif engine_rul_pct < 50:
        return {
            "recommendation_service_priority": "low",
            "recommendation_suggested_action": "Monitor engine health trend and service soon",
            "recommendation_safe_operating_limit_km": 600,
            "recommendation_source": "rule_based",
        }

    # Low battery RUL
    if battery_rul_pct < 20:
        return {
            "recommendation_service_priority": "medium",
            "recommendation_suggested_action": "Battery nearing end of life. Plan replacement soon.",
            "recommendation_safe_operating_limit_km": 200,
            "recommendation_source": "rule_based",
        }
    elif battery_rul_pct < 40:
        return {
            "recommendation_service_priority": "low",
            "recommendation_suggested_action": "Battery health declining. Monitor and prepare for replacement.",
            "recommendation_safe_operating_limit_km": 400,
            "recommendation_source": "rule_based",
        }

    # Moderate risk
    if failure_prob > 0.3:
        return {
            "recommendation_service_priority": "medium",
            "recommendation_suggested_action": "Increased risk detected. Schedule comprehensive checkup.",
            "recommendation_safe_operating_limit_km": 300,
            "recommendation_source": "rule_based",
        }

    # Default: healthy
    return {
        "recommendation_service_priority": "normal",
        "recommendation_suggested_action": "No immediate maintenance required",
        "recommendation_safe_operating_limit_km": 1000,
        "recommendation_source": "rule_based",
    }


# ---------------------------------------------------------------------------
# Groq LLM-powered recommendation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a vehicle maintenance advisory AI. Given vehicle diagnostics data, \
produce a JSON maintenance recommendation.

RULES:
- Respond ONLY with a valid JSON object, no markdown, no explanation.
- The JSON must have exactly these keys:
  "recommendation_service_priority": one of "critical", "high", "medium", "low", "normal"
  "recommendation_suggested_action": a clear, actionable maintenance instruction (1-2 sentences)
  "recommendation_safe_operating_limit_km": integer, estimated safe driving distance before service

Base your recommendation on failure probability, remaining useful life of components, \
the primary fault, and contributing factors. Be specific about which component needs \
attention and why."""


def _build_user_prompt(
    failure_prob: float,
    engine_rul_pct: float,
    brake_rul_pct: float,
    battery_rul_pct: float,
    fault_primary: str,
    contributing_factors: list[str] | None = None,
) -> str:
    factors = contributing_factors or []
    return (
        f"Vehicle Diagnostics Snapshot:\n"
        f"- Failure probability (next 7 days): {failure_prob:.0%}\n"
        f"- Engine remaining useful life: {engine_rul_pct:.1f}%\n"
        f"- Brake remaining useful life: {brake_rul_pct:.1f}%\n"
        f"- Battery remaining useful life: {battery_rul_pct:.1f}%\n"
        f"- Primary fault: {fault_primary}\n"
        f"- Contributing factors: {', '.join(factors) if factors else 'none'}\n\n"
        f"Produce the JSON recommendation."
    )


def _parse_groq_response(raw: str) -> dict[str, str | int]:
    """Extract JSON from Groq response, stripping any markdown fencing."""
    text = raw.strip()
    # Strip ```json ... ``` wrapping if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    data = json.loads(text)

    priority = str(data["recommendation_service_priority"]).lower()
    valid_priorities = {"critical", "high", "medium", "low", "normal"}
    if priority not in valid_priorities:
        priority = "medium"

    return {
        "recommendation_service_priority": priority,
        "recommendation_suggested_action": str(data["recommendation_suggested_action"]),
        "recommendation_safe_operating_limit_km": int(data["recommendation_safe_operating_limit_km"]),
        "recommendation_source": "groq",
    }


def recommend_action_groq(
    failure_prob: float,
    engine_rul_pct: float,
    brake_rul_pct: float,
    battery_rul_pct: float,
    fault_primary: str,
    contributing_factors: list[str] | None = None,
) -> dict[str, str | int]:
    """Call Groq API for an LLM-generated recommendation. Raises on failure."""
    from groq import Groq  # lazy import so the package is optional

    api_key = os.getenv("GROQ_API_KEY", "")
    client = Groq(api_key=api_key)

    user_msg = _build_user_prompt(
        failure_prob, engine_rul_pct, brake_rul_pct, battery_rul_pct, fault_primary, contributing_factors,
    )

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=300,
        timeout=5.0,
    )

    raw_text = response.choices[0].message.content
    return _parse_groq_response(raw_text)


# ---------------------------------------------------------------------------
# Unified entry point: Groq first → rule-based fallback
# ---------------------------------------------------------------------------

def recommend_action(
    failure_prob: float,
    engine_rul_pct: float,
    brake_rul_pct: float,
    battery_rul_pct: float,
    fault_primary: str,
    contributing_factors: list[str] | None = None,
) -> dict[str, str | int]:
    """Generate a maintenance recommendation.

    Tries Groq LLM first (if GROQ_API_KEY is set).
    Falls back to deterministic rule-based engine on any error.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return recommend_action_rule_based(
            failure_prob, engine_rul_pct, brake_rul_pct, battery_rul_pct, fault_primary, contributing_factors,
        )

    try:
        return recommend_action_groq(
            failure_prob, engine_rul_pct, brake_rul_pct, battery_rul_pct, fault_primary, contributing_factors,
        )
    except Exception as exc:
        logger.warning("Groq recommendation failed (%s), using rule-based fallback.", exc)
        return recommend_action_rule_based(
            failure_prob, engine_rul_pct, brake_rul_pct, battery_rul_pct, fault_primary, contributing_factors,
        )
