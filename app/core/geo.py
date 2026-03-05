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


def osrm_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    base_url: str,
) -> Optional[float]:
    """
    Member 1 Tool: OSRM Routing Engine.
    Queries the road network distance in km.
    """
    try:
        # Format: lon,lat;lon,lat
        url = f"{base_url}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            # OSRM returns distance in meters
            return data["routes"][0]["distance"] / 1000.0
    except Exception:
        pass
    return None


def get_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    osrm_base_url: str = "",
) -> float:
    """
    Smart Distance: Try OSRM first, fall back to Haversine.
    """
    if osrm_base_url:
        road_dist = osrm_distance(lat1, lon1, lat2, lon2, osrm_base_url)
        if road_dist is not None:
            return road_dist
            
    return haversine(lat1, lon1, lat2, lon2)
