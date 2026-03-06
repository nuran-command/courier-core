"""
app/core/assignment.py — Assignment Engine Skeleton (Member 1)

This module acts as the bridge between the API and the optimization algorithm.
As Member 1 (Architect), this file provides the structure and a basic 
placeholder algorithm. The complex optimization logic (OR-Tools, VRP) 
is to be implemented by Member 2.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List

from app.config import get_settings
from app.core.geo import get_travel_metrics
from app.models import (
    AssignmentResponse,
    Courier,
    CourierAssignment,
    Order,
)

settings = get_settings()


def solve_assignment(
    couriers: List[Courier],
    orders: List[Order],
) -> AssignmentResponse:
    """
    Member 1 Placeholder: Simple Greedy Assignment.
    
    This fulfills the API contract while waiting for Member 2 to 
    provide the high-performance 'Brain'.
    """
    t0 = time.perf_counter()
    
    # Track assigned state
    assignments: List[CourierAssignment] = []
    unassigned_order_ids: List[str] = []
    
    # Simple logic: Assign each order to the first courier with enough capacity
    # (Note: Member 1's job is infrastructure; this is just to make the API work)
    
    # We'll use a local copy of courier loads to avoid mutating the request objects
    current_loads = {c.id: c.current_load for c in couriers}
    courier_map = {c.id: [] for c in couriers}
    courier_weights = {c.id: 0.0 for c in couriers}

    for order in orders:
        assigned = False
        for courier in couriers:
            if current_loads[courier.id] + order.weight <= courier.capacity:
                courier_map[courier.id].append(order.id)
                current_loads[courier.id] += order.weight
                courier_weights[courier.id] += order.weight
                assigned = True
                break
        
        if not assigned:
            unassigned_order_ids.append(order.id)

    # Convert to response models
    courier_data = {c.id: c for c in couriers}
    order_data = {o.id: o for o in orders}

    for cid, o_ids in courier_map.items():
        if o_ids:
            # Calculate metrics for the first assigned order as a proxy (simplified for skeleton)
            first_order = order_data[o_ids[0]]
            courier = courier_data[cid]
            dist_km, dur_min = get_travel_metrics(
                courier.lat, courier.lon,
                first_order.lat, first_order.lon,
                settings.OSRM_BASE_URL
            )
            
            assignments.append(
                CourierAssignment(
                    courier_id=cid,
                    order_ids=o_ids,
                    total_weight=round(courier_weights[cid], 3),
                    estimated_distance_km=round(dist_km, 2),
                    estimated_duration_min=round(dur_min, 2),
                )
            )

    solved_in_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    return AssignmentResponse(
        assignments=assignments,
        unassigned_order_ids=unassigned_order_ids,
        solver_status="MEMBER1_SKELETON_GREEDY",
        solved_in_ms=solved_in_ms,
    )
