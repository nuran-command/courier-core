"""
tests/test_assign.py — Integration tests for the /assign endpoint.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.db import create_tables
from app.main import app

# Ensure tables exist for tests
create_tables()

client = TestClient(app)

# Architect's Shield Credentials
HEADERS = {"X-API-KEY": "JANA_COURIER_2026"}
DEADLINE = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()


def _make_payload(n_orders: int = 3, n_couriers: int = 2) -> dict:
    """Generate a minimal valid assignment payload."""
    orders = [
        {
            "id": f"ord-{i}",
            "lat": 51.1282 + i * 0.005,
            "lon": 71.4306 + i * 0.005,
            "weight": 2.0,
            "priority": (i % 5) + 1,
            "deadline": DEADLINE,
        }
        for i in range(n_orders)
    ]
    couriers = [
        {
            "id": f"courier-{i}",
            "lat": 51.125 + i * 0.01,
            "lon": 71.425 + i * 0.01,
            "capacity": 20.0,
            "current_load": 0.0,
            "status": "available",
            "rating": 4.5,
        }
        for i in range(n_couriers)
    ]
    return {"orders": orders, "couriers": couriers}


class TestHealthEndpoint:
    def test_health_ok(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAssignEndpoint:
    def test_basic_assignment_returns_200(self):
        payload = _make_payload(n_orders=5, n_couriers=2)
        resp = client.post("/assign", json=payload, headers=HEADERS)
        assert resp.status_code == 200

    def test_missing_api_key_returns_403(self):
        payload = _make_payload(n_orders=1, n_couriers=1)
        resp = client.post("/assign", json=payload) # no headers
        assert resp.status_code == 403

    def test_response_has_expected_fields(self):
        payload = _make_payload(n_orders=3, n_couriers=2)
        data = client.post("/assign", json=payload, headers=HEADERS).json()
        assert "assignments" in data
        assert "unassigned_order_ids" in data
        assert "solver_status" in data

    def test_all_orders_covered(self):
        """Every order should be either assigned or in unassigned list."""
        payload = _make_payload(n_orders=4, n_couriers=3)
        data = client.post("/assign", json=payload, headers=HEADERS).json()
        assigned = {
            oid
            for a in data["assignments"]
            for oid in a["order_ids"]
        }
        unassigned = set(data["unassigned_order_ids"])
        all_order_ids = {o["id"] for o in payload["orders"]}
        assert assigned | unassigned == all_order_ids

    def test_no_eligible_couriers_returns_422(self):
        """All couriers offline → 422."""
        payload = _make_payload(n_orders=2, n_couriers=1)
        payload["couriers"][0]["status"] = "offline"
        resp = client.post("/assign", json=payload, headers=HEADERS)
        assert resp.status_code == 422


class TestHistoryEndpoint:
    def test_history_returns_list(self):
        # Seed some data first
        client.post("/assign", json=_make_payload(n_orders=2, n_couriers=1), headers=HEADERS)

        resp = client.get("/history?limit=10", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAnalyticsEndpoint:
    def test_analytics_returns_stats(self):
        resp = client.get("/analytics/sla")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_assignments" in data
        assert "avg_distance_km" in data
