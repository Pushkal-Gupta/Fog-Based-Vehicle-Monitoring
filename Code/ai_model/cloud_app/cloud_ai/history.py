"""Historical data access and feature aggregation for cloud advisory inference."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class HistoryProvider(Protocol):
    """Abstract provider for fetching recent Section-6 cloud records."""

    def fetch_recent(self, vehicle_id: str, limit: int) -> list[dict]:
        """Return recent records for a vehicle sorted by recency (newest first)."""

    def save_record(self, record: dict) -> None:
        """Persist a Section-6 style record for future historical inference."""


class NoopHistoryProvider:
    """Default provider when no history backend is configured."""

    def fetch_recent(self, vehicle_id: str, limit: int) -> list[dict]:
        return []

    def save_record(self, record: dict) -> None:
        return None




class InMemoryHistoryProvider:
    """Simple in-process store, useful for local testing without MongoDB."""

    def __init__(self) -> None:
        self._records: list[dict] = []

    def fetch_recent(self, vehicle_id: str, limit: int) -> list[dict]:
        filtered = [r for r in self._records if r.get("vehicle_id") == vehicle_id]
        filtered.sort(key=lambda row: row.get("timestamp_ms", 0), reverse=True)
        return filtered[:limit]

    def save_record(self, record: dict) -> None:
        self._records.append(dict(record))


class MongoHistoryProvider:
    """MongoDB-backed history provider for Section-6 cloud records."""

    def __init__(
        self,
        uri: str,
        database: str,
        collection: str,
        timeout_ms: int = 2000,
    ) -> None:
        from pymongo import MongoClient

        self.client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        self.collection = self.client[database][collection]

    def fetch_recent(self, vehicle_id: str, limit: int) -> list[dict]:
        cursor = self.collection.find({"vehicle_id": vehicle_id}).sort("timestamp_ms", -1).limit(limit)
        return list(cursor)

    def save_record(self, record: dict) -> None:
        self.collection.insert_one(record)


@dataclass
class HistoricalSnapshot:
    points_used: int
    avg_thermal_stress_index: float | None = None
    avg_vibration_anomaly_score: float | None = None
    avg_charging_efficiency: float | None = None
    avg_vehicle_health_score: float | None = None
    avg_engine_rul_pct: float | None = None
    avg_brake_rul_pct: float | None = None
    avg_battery_rul_pct: float | None = None


def build_history_provider_from_env() -> HistoryProvider:
    """Build history provider from environment settings."""

    backend = os.getenv("CLOUD_HISTORY_BACKEND", "mongo").strip().lower()
    if backend == "memory":
        return InMemoryHistoryProvider()

    uri = os.getenv("CLOUD_MONGO_URI", "").strip()
    if not uri:
        return NoopHistoryProvider()

    database = os.getenv("CLOUD_MONGO_DB", "cloud_ai")
    collection = os.getenv("CLOUD_MONGO_COLLECTION", "section6_history")

    try:
        provider = MongoHistoryProvider(uri=uri, database=database, collection=collection)
        provider.client.admin.command("ping")
        return provider
    except Exception:
        return NoopHistoryProvider()


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def summarize_history(records: list[dict]) -> HistoricalSnapshot:
    """Create aggregate snapshot from recent Section-6 historical records."""

    def collect(field: str) -> list[float]:
        result: list[float] = []
        for row in records:
            value = row.get(field)
            if isinstance(value, (int, float)):
                result.append(float(value))
        return result

    return HistoricalSnapshot(
        points_used=len(records),
        avg_thermal_stress_index=_safe_mean(collect("thermal_stress_index")),
        avg_vibration_anomaly_score=_safe_mean(collect("mechanical_vibration_anomaly_score")),
        avg_charging_efficiency=_safe_mean(collect("electrical_charging_efficiency_score")),
        avg_vehicle_health_score=_safe_mean(collect("vehicle_health_score")),
        avg_engine_rul_pct=_safe_mean(collect("engine_rul_pct")),
        avg_brake_rul_pct=_safe_mean(collect("brake_rul_pct")),
        avg_battery_rul_pct=_safe_mean(collect("battery_rul_pct")),
    )


def blend(current: float, historical: float | None, current_weight: float = 0.7) -> float:
    """Blend current observation with historical aggregate when available."""

    if historical is None:
        return current
    historical_weight = 1.0 - current_weight
    return (current_weight * current) + (historical_weight * historical)
