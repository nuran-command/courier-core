"""
tests/test_geo.py — Unit tests for Geographic & Routing utilities (Member 1).
"""
import pytest
from app.core.geo import haversine, get_travel_metrics

class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine(51.1282, 71.4306, 51.1282, 71.4306) == pytest.approx(0.0)

    def test_known_distance_astana_almaty(self):
        # Astana → Almaty: straight-line ≈ 970 km
        d = haversine(51.128, 71.430, 43.238, 76.945)
        assert 900 < d < 1100, f"Expected ~970 km, got {d:.1f}"

    def test_symmetry(self):
        d1 = haversine(51.0, 71.0, 52.0, 72.0)
        d2 = haversine(52.0, 72.0, 51.0, 71.0)
        assert d1 == pytest.approx(d2, rel=1e-9)


class TestTravelMetrics:
    def test_fallback_metrics(self):
        """When OSRM is not provided, should return haversine + 30km/h estimation."""
        lat1, lon1 = 51.1282, 71.4306
        lat2, lon2 = 51.1370, 71.4306 # ~1km away north
        
        dist, dur = get_travel_metrics(lat1, lon1, lat2, lon2)
        
        assert dist > 0.8 and dist < 1.2
        # 1km at 30km/h = 2 minutes
        assert dur > 1.5 and dur < 2.5
