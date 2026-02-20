import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from app.main import app


@pytest.mark.asyncio
async def test_insert_vehicle_data():
    payload = {
        "vehicle_id": "TEST_CAR_001",
        "timestamp_ms": 1707051123456,
        "thermal_brake_margin": -0.21,
        "thermal_engine_margin": 0.34,
        "thermal_stress_index": 0.82,
        "mechanical_vibration_anomaly_score": 0.77,
        "mechanical_dominant_fault_band_hz": 142,
        "mechanical_vibration_rms": 0.84,
        "electrical_charging_efficiency_score": 0.81,
        "electrical_battery_health_pct": 87,
        "engine_rul_pct": 62,
        "brake_rul_pct": 28,
        "battery_rul_pct": 74,
        "vehicle_health_score": 0.64
    }

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            response = await ac.post("/api/intelligence/insert", json=payload)

    assert response.status_code == 201
    assert "inserted_id" in response.json()


@pytest.mark.asyncio
async def test_get_unprocessed():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            response = await ac.get("/api/intelligence/data/unprocessed?limit=5")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_all_data():
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test"
        ) as ac:
            response = await ac.get("/api/intelligence/data/all?limit=5")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
