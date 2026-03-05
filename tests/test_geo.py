"""
tests/test_geo.py — Unit tests for Haversine distance calculation.
"""
import pytest
from app.core.geo import haversine, build_distance_matrix


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine(51.1282, 71.4306, 51.1282, 71.4306) == pytest.approx(0.0)

    def test_known_distance_astana_almaty(self):
        # Astana (51.128, 71.430) → Almaty (43.238, 76.945): straight-line ≈ 970 km
        d = haversine(51.128, 71.430, 43.238, 76.945)
        assert 900 < d < 1100, f"Expected ~970 km, got {d:.1f}"

    def test_short_distance_within_astana(self):
        # Two points ~1 km apart within Astana
        d = haversine(51.128, 71.430, 51.137, 71.430)
        assert 0.5 < d < 2.0, f"Expected ~1 km, got {d:.3f}"

    def test_symmetry(self):
        d1 = haversine(51.0, 71.0, 52.0, 72.0)
        d2 = haversine(52.0, 72.0, 51.0, 71.0)
        assert d1 == pytest.approx(d2, rel=1e-9)


class TestDistanceMatrix:
    def test_matrix_diagonal_is_zero(self):
        locs = [(51.128, 71.430), (51.137, 71.445), (51.120, 71.410)]
        matrix = build_distance_matrix(locs)
        for i in range(len(locs)):
            assert matrix[i][i] == 0.0

    def test_matrix_symmetric(self):
        locs = [(51.128, 71.430), (51.137, 71.445), (51.120, 71.410)]
        matrix = build_distance_matrix(locs)
        for i in range(len(locs)):
            for j in range(len(locs)):
                assert matrix[i][j] == pytest.approx(matrix[j][i], rel=1e-9)
