"""Driver aggression scoring from raw vehicle telemetry fields.

Computes two values:
  usage_driver_aggression_score     → float [0.0, 1.0]
  usage_stress_amplification_factor → float [1.0, 2.0]

No ML models, no external calls, no state. Pure deterministic rules
applied to fields that are present in every fog-node telemetry record.

Signals used
------------
Field                               Aggression signal
----------------------------------------------------------------------
trigger_brake_temp_rise_rate        Positive → hard / panic braking
trigger_measured_brake_temp_c       Sustained high temp → repeated hard stops
mechanical_vibration_rms            High RMS → rough driving / cornering
mechanical_vibration_anomaly_score  0–1 anomaly flag from fog node
thermal_stress_index                0–1 composite thermal load
fog_decision_critical_class         2 = critical fog event
fog_decision_actuation_triggered    1 = fog control system had to intervene

Weights total 1.0.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Brake temp rise rate: anything above this is "hard braking"
_BRAKE_RISE_RATE_MAX = 30.0   # °C/s — clamped at this for score = 1.0
_BRAKE_RISE_RATE_MIN = 0.0    # negative values (cooling) → 0 aggression

# Measured brake temperature thresholds
_BRAKE_TEMP_COOL  = 80.0    # °C — normal operating, score = 0
_BRAKE_TEMP_HOT   = 300.0   # °C — fully saturated, score = 1

# Vibration RMS thresholds
_VIB_RMS_LOW  = 0.2   # smooth driving
_VIB_RMS_HIGH = 1.2   # extreme vibration

# Signal weights — must sum to 1.0
_WEIGHTS = {
    "brake_rise_rate":      0.30,   # strongest single signal for hard braking
    "brake_temp":           0.20,   # sustained thermal load from repeated stops
    "vibration_rms":        0.15,   # ride roughness
    "vibration_anomaly":    0.15,   # fog-node anomaly flag
    "thermal_stress":       0.10,   # composite engine + brake thermal pressure
    "fog_critical_class":   0.05,   # driving aggressively in critical fog
    "fog_actuation":        0.05,   # fog system had to intervene
}


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _norm_brake_rise_rate(rate: float) -> float:
    """Normalise brake temp rise rate to [0, 1]. Only positive (rising) counts."""
    if rate <= _BRAKE_RISE_RATE_MIN:
        return 0.0
    return _clamp(rate / _BRAKE_RISE_RATE_MAX)


def _norm_brake_temp(temp_c: float) -> float:
    """Normalise measured brake temperature to [0, 1]."""
    if temp_c <= _BRAKE_TEMP_COOL:
        return 0.0
    return _clamp((temp_c - _BRAKE_TEMP_COOL) / (_BRAKE_TEMP_HOT - _BRAKE_TEMP_COOL))


def _norm_vibration_rms(rms: float) -> float:
    """Normalise mechanical vibration RMS to [0, 1]."""
    if rms <= _VIB_RMS_LOW:
        return 0.0
    return _clamp((rms - _VIB_RMS_LOW) / (_VIB_RMS_HIGH - _VIB_RMS_LOW))


# ---------------------------------------------------------------------------
# Per-record scorer
# ---------------------------------------------------------------------------

def _score_single_record(record: dict) -> float:
    """Compute aggression score [0, 1] for one telemetry record."""

    brake_rise   = float(record.get("trigger_brake_temp_rise_rate", 0.0))
    brake_temp   = float(record.get("trigger_measured_brake_temp_c", 0.0))
    vib_rms      = float(record.get("mechanical_vibration_rms", 0.0))
    vib_anomaly  = float(record.get("mechanical_vibration_anomaly_score", 0.0))
    thermal      = float(record.get("thermal_stress_index", 0.0))
    fog_class    = float(record.get("fog_decision_critical_class", 1.0))
    fog_act      = float(record.get("fog_decision_actuation_triggered", 0.0))

    # Normalise each signal 0–1
    s_brake_rise  = _norm_brake_rise_rate(brake_rise)
    s_brake_temp  = _norm_brake_temp(brake_temp)
    s_vib_rms     = _norm_vibration_rms(vib_rms)
    s_vib_anomaly = _clamp(vib_anomaly)           # already 0–1
    s_thermal     = _clamp(thermal)               # already 0–1
    s_fog_class   = 1.0 if fog_class >= 2 else 0.0  # critical = 2
    s_fog_act     = 1.0 if fog_act >= 1 else 0.0

    score = (
        _WEIGHTS["brake_rise_rate"]   * s_brake_rise  +
        _WEIGHTS["brake_temp"]        * s_brake_temp  +
        _WEIGHTS["vibration_rms"]     * s_vib_rms     +
        _WEIGHTS["vibration_anomaly"] * s_vib_anomaly +
        _WEIGHTS["thermal_stress"]    * s_thermal     +
        _WEIGHTS["fog_critical_class"]* s_fog_class   +
        _WEIGHTS["fog_actuation"]     * s_fog_act
    )

    return _clamp(score)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_aggression(
    current_record: dict,
    history_records: list[dict] | None = None,
) -> dict:
    """Compute driver aggression score from telemetry data.

    Parameters
    ----------
    current_record:
        The newest telemetry record (dict from the fog-node API).
    history_records:
        Optional list of recent records (newest first). When provided, the
        final score is a weighted blend: 70% current, 30% historical mean.

    Returns
    -------
    dict with keys:
        usage_driver_aggression_score     – float [0.0, 1.0]
        usage_stress_amplification_factor – float [1.0, 2.0]
    """
    current_score = _score_single_record(current_record)

    if history_records and len(history_records) > 1:
        historical_scores = [_score_single_record(r) for r in history_records[1:]]
        historical_mean = sum(historical_scores) / len(historical_scores)
        blended_score = 0.70 * current_score + 0.30 * historical_mean
    else:
        blended_score = current_score

    aggression = round(_clamp(blended_score), 4)
    stress_factor = round(1.0 + aggression, 4)  # maps [0.0, 1.0] → [1.0, 2.0]

    logger.debug(
        "Driver aggression: current=%.3f blended=%.3f stress_factor=%.3f",
        current_score,
        aggression,
        stress_factor,
    )

    return {
        "usage_driver_aggression_score": aggression,
        "usage_stress_amplification_factor": stress_factor,
    }
