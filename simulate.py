"""
simulate.py — Test client: generates 50 random orders near Astana
and sends them to the running API, then prints the assignment result.

Usage:
    python simulate.py              # targets http://localhost:8000
    python simulate.py --url http://localhost:8000
    python simulate.py --couriers 10 --orders 50
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Astana city centre
# ---------------------------------------------------------------------------
ASTANA_LAT = 51.1282
ASTANA_LON = 71.4306
RADIUS_KM = 15          # spread orders/couriers within 15 km of centre


def random_point(centre_lat: float, centre_lon: float, radius_km: float):
    """Return a random (lat, lon) within radius_km of the centre."""
    # Uniform in a disc (reject sampling)
    while True:
        dlat = random.uniform(-radius_km, radius_km) / 110.574
        dlon = random.uniform(-radius_km, radius_km) / (
            111.320 * math.cos(math.radians(centre_lat))
        )
        if math.sqrt((dlat * 110.574) ** 2 + (dlon * 111.320) ** 2) <= radius_km:
            return round(centre_lat + dlat, 6), round(centre_lon + dlon, 6)


def generate_orders(n: int) -> list[dict[str, Any]]:
    orders = []
    for i in range(n):
        lat, lon = random_point(ASTANA_LAT, ASTANA_LON, RADIUS_KM)
        deadline_offset_hours = random.choice([1, 2, 3, 4, 6])
        deadline = (
            datetime.now(timezone.utc) + timedelta(hours=deadline_offset_hours)
        ).isoformat()
        orders.append({
            "id": f"SIM-ORD-{i+1:04d}",
            "lat": lat,
            "lon": lon,
            "weight": round(random.uniform(0.5, 10.0), 2),
            "priority": random.randint(1, 5),
            "deadline": deadline,
        })
    return orders


def generate_couriers(n: int) -> list[dict[str, Any]]:
    couriers = []
    for i in range(n):
        lat, lon = random_point(ASTANA_LAT, ASTANA_LON, RADIUS_KM)
        capacity = random.choice([10.0, 15.0, 20.0, 25.0, 30.0])
        current_load = round(random.uniform(0, capacity * 0.3), 2)
        couriers.append({
            "id": f"SIM-COU-{i+1:02d}",
            "lat": lat,
            "lon": lon,
            "capacity": capacity,
            "current_load": current_load,
            "status": "available",
            "rating": round(random.uniform(3.5, 5.0), 1),
        })
    return couriers


def post_json(url: str, data: dict) -> dict:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def print_result(result: dict, n_orders: int, n_couriers: int) -> None:
    assignments = result.get("assignments", [])
    unassigned = result.get("unassigned_order_ids", [])
    solver_status = result.get("solver_status", "?")
    solved_ms = result.get("solved_in_ms", "?")

    total_assigned = sum(len(a["order_ids"]) for a in assignments)

    print("\n" + "=" * 60)
    print("  SMART ASSIGNMENT ENGINE — Simulation Results")
    print("=" * 60)
    print(f"  Input : {n_orders} orders | {n_couriers} couriers")
    print(f"  Solver: {solver_status}  ({solved_ms} ms)")
    print(f"  Assigned  : {total_assigned}/{n_orders}")
    print(f"  Unassigned: {len(unassigned)}")
    print("-" * 60)

    for a in assignments:
        print(
            f"  [{a['courier_id']}]  "
            f"{len(a['order_ids'])} orders | "
            f"{a['total_weight']:.1f} kg | "
            f"~{a['estimated_distance_km']:.1f} km"
        )
        for oid in a["order_ids"]:
            print(f"      → {oid}")

    if unassigned:
        print("\n  ⚠  Unassigned orders:")
        for oid in unassigned:
            print(f"      {oid}")

    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate 50 random Astana orders → Courier Core API"
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="API base URL"
    )
    parser.add_argument("--orders", type=int, default=50)
    parser.add_argument("--couriers", type=int, default=10)
    args = parser.parse_args()

    print(f"\nGenerating {args.orders} orders and {args.couriers} couriers…")
    orders = generate_orders(args.orders)
    couriers = generate_couriers(args.couriers)

    payload = {"orders": orders, "couriers": couriers}

    endpoint = args.url.rstrip("/") + "/assign"
    print(f"Sending POST {endpoint} …")

    try:
        result = post_json(endpoint, payload)
    except urllib.error.URLError as e:
        print(f"\n  Could not reach {endpoint}: {e}")
        print("   Make sure the server is running:  uvicorn app.main:app --reload")
        sys.exit(1)

    print_result(result, args.orders, args.couriers)

    # Fetch Analytics
    analytics_url = args.url.rstrip("/") + "/analytics/sla"
    print(f"Fetching Analytics from {analytics_url} …")
    try:
        with urllib.request.urlopen(analytics_url) as resp:
            stats = json.loads(resp.read())
            print("\n  SLA & OPERATIONAL ANALYTICS")
            print(f"    Total Successful Assignments: {stats['total_assignments']}")
            print(f"    Avg Solver Speed:             {stats['avg_solver_speed_ms']} ms")
            print(f"    Priority Dist (SLA Alertness): {stats['priority_distribution']}")
            print(f"    ML Ready Data Count:         {stats['ml_ready_records']}")
            print("=" * 60 + "\n")
    except Exception as e:
        print(f"Could not fetch analytics: {e}")


if __name__ == "__main__":
    main()
