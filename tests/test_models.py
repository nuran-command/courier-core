"""
tests/test_models.py — Pydantic model validation tests.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.models import Order, Courier, OrderPriority, AssignmentRequest


DEADLINE = datetime.now(timezone.utc) + timedelta(hours=2)


class TestOrderModel:
    def test_valid_order(self):
        o = Order(
            id="ord-1",
            lat=51.1282,
            lon=71.4306,
            weight=3.5,
            priority=OrderPriority.VIP,
            deadline=DEADLINE,
        )
        assert o.id == "ord-1"
        assert o.priority == 5

    def test_weight_must_be_positive(self):
        with pytest.raises(Exception):
            Order(id="x", lat=51.0, lon=71.0, weight=0, priority=1, deadline=DEADLINE)

    def test_lat_out_of_range(self):
        with pytest.raises(Exception):
            Order(id="x", lat=200, lon=71.0, weight=1, priority=1, deadline=DEADLINE)

    def test_lon_out_of_range(self):
        with pytest.raises(Exception):
            Order(id="x", lat=51.0, lon=200.0, weight=1, priority=1, deadline=DEADLINE)


class TestCourierModel:
    def test_valid_courier(self):
        c = Courier(id="c-1", lat=51.13, lon=71.42, capacity=20, current_load=5)
        assert c.available_capacity == pytest.approx(15.0)

    def test_overloaded_courier_rejected(self):
        with pytest.raises(Exception):
            Courier(id="c-1", lat=51.13, lon=71.42, capacity=10, current_load=15)

    def test_rating_bounds(self):
        with pytest.raises(Exception):
            Courier(id="c-1", lat=51.13, lon=71.42, capacity=10, rating=6.0)


class TestAssignmentRequest:
    def test_empty_couriers_rejected(self):
        with pytest.raises(Exception):
            AssignmentRequest(couriers=[], orders=[
                Order(id="o1", lat=51.0, lon=71.0, weight=1, priority=1, deadline=DEADLINE)
            ])

    def test_empty_orders_rejected(self):
        with pytest.raises(Exception):
            AssignmentRequest(
                couriers=[Courier(id="c1", lat=51.0, lon=71.0, capacity=10)],
                orders=[],
            )
