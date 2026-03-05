"""
app/simulate.py — Benchmarking SmartAssigner vs Greedy
"""
import time
from datetime import datetime, timezone, timedelta
from typing import List

from app.models import Courier, Order
from app.core.engine import SmartAssigner
from app.core.assignment import solve_assignment as greedy_solve

import random

# Seed for reproducible benchmark
random.seed(42)

def generate_mock_data(num_couriers: int, num_orders: int) -> tuple[List[Courier], List[Order]]:
    couriers = []
    for i in range(num_couriers):
        couriers.append(
            Courier(
                id=f"c-{i}",
                lat=51.1 + random.uniform(0, 0.05),
                lon=71.4 + random.uniform(0, 0.05),
                capacity=random.uniform(10.0, 30.0),
                current_load=0.0,
                status="available",
                rating=5.0
            )
        )
        
    orders = []
    now = datetime.now(timezone.utc)
    for i in range(num_orders):
        # 20% are VIP
        is_vip = random.random() < 0.2
        priority = 5 if is_vip else random.randint(1, 3)
        # 10% are urgent (1 hour left), others have 3-5 hours
        hours_left = random.uniform(0.5, 1.5) if random.random() < 0.1 else random.uniform(2.0, 5.0)
        
        orders.append(
            Order(
                id=f"o-{i}",
                lat=51.1 + random.uniform(0, 0.05),
                lon=71.4 + random.uniform(0, 0.05),
                weight=random.uniform(1.0, 5.0),
                priority=priority,
                deadline=now + timedelta(hours=hours_left)
            )
        )
        
    return couriers, orders


def run_benchmark():
    print("Generating Mock Data for 10 couriers and 40 orders...")
    couriers, orders = generate_mock_data(10, 40)
    
    # Run Greedy (Legacy)
    print("\n--- Running Legacy Greedy Assignment ---")
    t0 = time.perf_counter()
    greedy_res = greedy_solve(couriers, orders)
    t_greedy = time.perf_counter() - t0
    
    greedy_distance = sum(a.estimated_distance_km for a in greedy_res.assignments)
    greedy_unassigned = len(greedy_res.unassigned_order_ids)
    
    print(f"Time: {t_greedy*1000:.2f} ms")
    print(f"Unassigned Orders (Violations/Drops): {greedy_unassigned}")
    print(f"Total Distance (Naive sum): {greedy_distance:.2f} km")
    
    # Run SmartAssigner (OR-Tools)
    print("\n--- Running AI SmartAssigner (OR-Tools) ---")
    assigner = SmartAssigner(couriers, orders)
    t0 = time.perf_counter()
    smart_res = assigner.solve()
    t_smart = time.perf_counter() - t0
    
    smart_distance = sum(a.estimated_distance_km for a in smart_res.assignments)
    smart_unassigned = len(smart_res.unassigned_order_ids)
    
    print(f"Time: {t_smart*1000:.2f} ms")
    print(f"Unassigned Orders (Violations/Drops): {smart_unassigned}")
    print(f"Total Distance (Optimal sum): {smart_distance:.2f} km")
    
    # Metrics
    if greedy_distance > 0:
        dist_savings = (greedy_distance - smart_distance) / greedy_distance * 100
    else:
        dist_savings = 0.0
        
    print("\n=== Benchmark Results ===")
    print(f"Distance Savings: {dist_savings:.1f}%")
    print(f"SLA Violation / Drop improvements: {greedy_unassigned - smart_unassigned} orders saved!")

if __name__ == "__main__":
    run_benchmark()
