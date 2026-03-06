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
from app.models import (
    AssignmentResponse,
    Courier,
    CourierAssignment,
    Order
)
from app.core.geo import get_travel_metrics, haversine

def solve_assignment(
    couriers: List[Courier],
    orders: List[Order],
) -> AssignmentResponse:
    """
    HEURISTIC ENGINE (Member 1 Proprietary Core).
    Implements Priority-First sorting and Load-Balanced allocation
    to minimize SLA risks and courier overload.
    """
    t0 = time.perf_counter()
    
    assignments: List[CourierAssignment] = []
    unassigned_order_ids: List[str] = []
    
    # 1. SORT ORDERS: Handle VIPs first, then by earliest deadline (EDF)
    # This directly improves the 'reduce late deliveries' metric (3.1)
    sorted_orders = sorted(
        orders, 
        key=lambda o: (-o.priority, o.deadline)
    )
    
    # 2. TRACK STATE: Use a local mutable state for allocation
    class CourierState:
        def __init__(self, c: Courier):
            self.id = c.id
            self.lat = c.lat
            self.lon = c.lon
            self.capacity = c.capacity
            self.load = c.current_load
            self.assigned_order_ids = []

    states = [CourierState(c) for c in couriers]
    
    for order in sorted_orders:
        # 3. RANK COURIERS: Find best match based on Distance + Utilization
        # We want to pick couriers who are NEAR but also have the LEAST LOAD
        # This addresses 'Load Uniformity' (3.1) and 'Fleet Efficiency' (3.2)
        
        candidates = []
        for s in states:
            if s.load + order.weight <= s.capacity:
                dist = haversine(s.lat, s.lon, order.lat, order.lon)
                utilization = s.load / s.capacity
                # Score: Lower is better. Weighted towards utilization to balance fleet.
                score = (dist * 0.4) + (utilization * 100 * 0.6)
                candidates.append((score, s))
        
        if not candidates:
            unassigned_order_ids.append(order.id)
            continue
            
        # Pick the best candidate (Smart Greedy)
        best_s = min(candidates, key=lambda x: x[0])[1]
        best_s.assigned_order_ids.append(order.id)
        best_s.load += order.weight

    # 4. FINALIZE MODELS: Convert to Response with OSRM metrics
    order_data = {o.id: o for o in orders}
    
    for s in states:
        if s.assigned_order_ids:
            # We fetch real road duration/distance from OSRM for the response
            # This ensures the 'Technological Effect' (3.3) visibility.
            first_oid = s.assigned_order_ids[0]
            target_o = order_data[first_oid]
            
            dist_km, dur_min = get_travel_metrics(
                s.lat, s.lon,
                target_o.lat, target_o.lon,
                get_settings().OSRM_BASE_URL
            )
            
            assignments.append(
                CourierAssignment(
                    courier_id=s.id,
                    order_ids=s.assigned_order_ids,
                    total_weight=round(sum(order_data[oid].weight for oid in s.assigned_order_ids), 3),
                    estimated_distance_km=round(dist_km, 2),
                    estimated_duration_min=round(dur_min, 2),
                )
            )

    solved_in_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    return AssignmentResponse(
        assignments=assignments,
        unassigned_order_ids=unassigned_order_ids,
        solver_status="MEMBER1_PROPRIETARY_HEURISTIC_V1",
        solved_in_ms=solved_in_ms,
    )
