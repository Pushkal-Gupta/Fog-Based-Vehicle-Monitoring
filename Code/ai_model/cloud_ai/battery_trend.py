"""Battery degradation trend classifier from telemetry & history.

Outputs a human-readable trend string:
    "improving"  – battery health metrics trending upward
    "stable"     – no significant change detected
    "degrading"  – health / RUL metrics declining
    "critical"   – severe decline or multiple critical signals

Signals used
------------
Field                                  Signal
----------------------------------------------------------------------
electrical_battery_health_pct          Primary health indicator (0–100)
electrical_charging_efficiency_score   Charging quality (0–1)
battery_rul_pct                        AI-predicted remaining useful life (0–100)
thermal_stress_index                   Elevated heat accelerates degradation (0–1)

History is used to compute a delta (current − historical mean).
If no history is available, thresholds on absolute values are used.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Absolute-value thresholds (no history fallback)
# ---------------------------------------------------------------------------

_BATTERY_HEALTH_CRITICAL  = 60.0   # below this → critical
_BATTERY_HEALTH_LOW       = 75.0   # below this → degrading
_CHARGING_EFF_CRITICAL    = 0.50   # below this → critical
_CHARGING_EFF_LOW         = 0.70   # below this → degrading
_BATTERY_RUL_CRITICAL     = 15.0   # below this → critical
_BATTERY_RUL_LOW          = 35.0   # below this → degrading
_THERMAL_STRESS_HIGH      = 0.80   # sustained heat accelerates battery wear

# ---------------------------------------------------------------------------
# Delta thresholds (when history is available)
# ---------------------------------------------------------------------------

# A positive delta means the metric has INCREASED (health improved)
_HEALTH_DELTA_IMPROVING   = +2.0   # > +2 pct points → improving
_HEALTH_DELTA_DEGRADING   = -2.0   # < –2 pct points → degrading

_RUL_DELTA_IMPROVING      = +3.0   # > +3 pct points → improving
_RUL_DELTA_DEGRADING      = -3.0

_EFF_DELTA_IMPROVING      = +0.05  # > +0.05 → improving
_EFF_DELTA_DEGRADING      = -0.05


def _safe_mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _collect(records: list[dict], field: str) -> list[float]:
    result = []
    for r in records:
        v = r.get(field)
        if isinstance(v, (int, float)):
            result.append(float(v))
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_battery_trend(
    current_record: dict,
    history_records: list[dict] | None = None,
    ai_battery_rul_pct: float | None = None,
) -> dict:
    """Classify battery degradation trend.

    Parameters
    ----------
    current_record:
        The newest raw telemetry record.
    history_records:
        Optional list of recent records (newest first). Skip current record
        (index 0) when computing historical averages.
    ai_battery_rul_pct:
        The battery RUL% already computed by the AI pipeline for the current
        record. If provided, it's used as the primary RUL signal. Otherwise
        falls back to the raw field in current_record.

    Returns
    -------
    dict with key:
        electrical_battery_degradation_trend – one of "improving", "stable",
                                               "degrading", "critical"
    """
    # --- Current values -------------------------------------------------------
    health_cur  = float(current_record.get("electrical_battery_health_pct", 100.0))
    eff_cur     = float(current_record.get("electrical_charging_efficiency_score", 1.0))
    thermal_cur = float(current_record.get("thermal_stress_index", 0.0))
    rul_cur     = float(ai_battery_rul_pct) if ai_battery_rul_pct is not None \
                  else float(current_record.get("battery_rul_pct", 100.0))

    # --- Check for absolute critical state ------------------------------------
    critical_flags = 0
    if health_cur < _BATTERY_HEALTH_CRITICAL:
        critical_flags += 1
    if eff_cur < _CHARGING_EFF_CRITICAL:
        critical_flags += 1
    if rul_cur < _BATTERY_RUL_CRITICAL:
        critical_flags += 1
    if thermal_cur > _THERMAL_STRESS_HIGH and rul_cur < _BATTERY_RUL_LOW:
        critical_flags += 1

    if critical_flags >= 2:
        logger.debug("Battery trend=critical (flags=%d)", critical_flags)
        return {"electrical_battery_degradation_trend": "critical"}

    # --- Use history delta if available ---------------------------------------
    past_records = (history_records or [])[1:]  # exclude current record

    if past_records:
        avg_health  = _safe_mean(_collect(past_records, "electrical_battery_health_pct"))
        avg_eff     = _safe_mean(_collect(past_records, "electrical_charging_efficiency_score"))
        avg_rul     = _safe_mean(_collect(past_records, "battery_rul_pct"))

        health_delta = (health_cur - avg_health) if avg_health is not None else 0.0
        eff_delta    = (eff_cur    - avg_eff)    if avg_eff    is not None else 0.0
        rul_delta    = (rul_cur    - avg_rul)    if avg_rul    is not None else 0.0

        improving_votes = sum([
            health_delta > _HEALTH_DELTA_IMPROVING,
            eff_delta    > _EFF_DELTA_IMPROVING,
            rul_delta    > _RUL_DELTA_IMPROVING,
        ])
        degrading_votes = sum([
            health_delta < _HEALTH_DELTA_DEGRADING,
            eff_delta    < _EFF_DELTA_DEGRADING,
            rul_delta    < _RUL_DELTA_DEGRADING,
        ])

        logger.debug(
            "Battery deltas: health=%.2f eff=%.3f rul=%.2f | votes imp=%d deg=%d",
            health_delta, eff_delta, rul_delta, improving_votes, degrading_votes,
        )

        if improving_votes >= 2:
            trend = "improving"
        elif degrading_votes >= 2:
            trend = "degrading"
        elif degrading_votes == 1 and (
            health_cur < _BATTERY_HEALTH_LOW
            or rul_cur < _BATTERY_RUL_LOW
            or eff_cur < _CHARGING_EFF_LOW
        ):
            trend = "degrading"
        else:
            trend = "stable"

    else:
        # No history — fall back to absolute thresholds only
        if (
            health_cur < _BATTERY_HEALTH_LOW
            or eff_cur < _CHARGING_EFF_LOW
            or rul_cur < _BATTERY_RUL_LOW
        ):
            trend = "degrading"
        else:
            trend = "stable"

    logger.debug("Battery trend=%s", trend)
    return {"electrical_battery_degradation_trend": trend}
