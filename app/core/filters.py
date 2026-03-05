"""
app/core/filters.py — Pre-solver courier eligibility filters.

Before handing couriers to the OR-Tools solver, we remove those that:
  1. Are not 'available'
  2. Have no remaining capacity for even the lightest order
  3. Are overloaded (current_load >= capacity)
"""
from __future__ import annotations

from typing import List

from app.models import Courier, Order


def filter_available_couriers(
    couriers: List[Courier],
    orders: List[Order],
) -> tuple[List[Courier], List[Courier]]:
    """
    Split couriers into (eligible, rejected) based on capacity and status.

    A courier is eligible if:
      - status == 'available'
      - available_capacity > 0 (i.e. current_load < capacity)
      - available_capacity >= the weight of the lightest pending order

    Returns:
        eligible   — couriers that may receive new assignments
        rejected   — couriers filtered out (logged, not passed to solver)
    """
    if not orders:
        return [], couriers

    min_order_weight = min(o.weight for o in orders)

    eligible: List[Courier] = []
    rejected: List[Courier] = []

    for courier in couriers:
        if courier.status != "available":
            rejected.append(courier)
            continue
        if courier.available_capacity < min_order_weight:
            rejected.append(courier)
            continue
        eligible.append(courier)

    return eligible, rejected
