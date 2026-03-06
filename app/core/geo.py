"""
app/core/geo.py — Member 1 Utility: Road Distances & Math.

Tool 1: OSRM (Primary) — Calculating distances via road networks.
Tool 2: Haversine (Fallback) — Straight-line math for robustness.
"""
from __future__ import annotations

import math
import requests
from typing import Optional

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Fast fallback: straight-line distance (km).
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def osrm_metrics(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    base_url: str,
) -> Optional[tuple[float, float]]:
    """
    Member 1 Tool: OSRM Routing Engine.
    Queries the road network for distance (km) and duration (minutes).
    """
    try:
        # Format: lon,lat;lon,lat
        url = f"{base_url}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            # OSRM returns distance in meters and duration in seconds
            route = data["routes"][0]
            dist_km = route["distance"] / 1000.0
            dur_min = route["duration"] / 60.0
            return dist_km, dur_min
    except Exception:
        pass
    return None


def get_travel_metrics(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    osrm_base_url: str = "",
) -> tuple[float, float]:
    """
    Smart Metrics: Try OSRM first, fall back to Haversine + avg speed.
    Returns: (distance_km, duration_min)
    """
    if osrm_base_url:
        metrics = osrm_metrics(lat1, lon1, lat2, lon2, osrm_base_url)
        if metrics is not None:
            return metrics
            
    # Fallback: Haversine distance and 30km/h average city speed
    dist_km = haversine(lat1, lon1, lat2, lon2)
    dur_min = (dist_km / 30.0) * 60.0 # simple estimation
    return dist_km, dur_min
