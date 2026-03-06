"""
app/core/engine.py — Advanced Smart Assignment Engine using OR-Tools (Member 2)

Upgraded from simple assignment to full Vehicle Routing Problem (VRP) optimization.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
import numpy as np

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from app.models import (
    AssignmentResponse,
    Courier,
    CourierAssignment,
    Order,
)
from app.core.filters import filter_available_couriers
from app.core.distances import compute_distance_matrix, get_distance_km

class SmartAssigner:
    """
    Advanced Optimization Engine using OR-Tools Routing Model (VRP).
    Optimizes the delivery sequence for each courier.
    """

    def __init__(self, couriers: List[Courier], orders: List[Order], osrm_base_url: str = ""):
        self.all_couriers = couriers
        self.all_orders = orders
        self.osrm_base_url = osrm_base_url
        self.now = datetime.now(timezone.utc)
        
        # Pre-filter couriers
        self.eligible_couriers, self.rejected_couriers = filter_available_couriers(
            self.all_couriers, self.all_orders
        )

    def compute_data_model(self):
        """Prepares the distance matrix and constraints for VRP."""
        # The routing model needs a single distance matrix where index 0 is the 'depot'
        # or we model each courier as a start node.
        # For simplicity in this VRP version, we treat each courier's position as a starting point.
        
        num_couriers = len(self.eligible_couriers)
        num_orders = len(self.all_orders)
        
        # Matrix size: num_couriers (starts) + num_orders
        total_locations = num_couriers + num_orders
        distance_matrix = np.zeros((total_locations, total_locations))
        
        # Indices 0 to num_couriers-1 are courier starting positions
        # Indices num_couriers to total_locations-1 are order locations
        
        # 1. Fill Distance Matrix
        # Courier -> Order distances
        dist_map = compute_distance_matrix(self.eligible_couriers, self.all_orders, self.osrm_base_url)
        for i, c in enumerate(self.eligible_couriers):
            for j, o in enumerate(self.all_orders):
                d = dist_map[c.id][o.id]
                distance_matrix[i][num_couriers + j] = int(d * 1000) # Convert to meters for integer solver
                distance_matrix[num_couriers + j][i] = int(d * 1000)
                
        # Order -> Order distances
        for j1, o1 in enumerate(self.all_orders):
            for j2, o2 in enumerate(self.all_orders):
                if j1 == j2: continue
                d = get_distance_km(o1.lat, o1.lon, o2.lat, o2.lon, self.osrm_base_url)
                distance_matrix[num_couriers + j1][num_couriers + j2] = int(d * 1000)

        # Scale weights to integers
        demands = [0] * num_couriers + [int(o.weight * 100) for o in self.all_orders]
        capacities = [int(c.available_capacity * 100) for c in self.eligible_couriers]
        
        return {
            'distance_matrix': distance_matrix.tolist(),
            'demands': demands,
            'vehicle_capacities': capacities,
            'num_vehicles': num_couriers,
            'starts': list(range(num_couriers)),
            'ends': [0] * num_couriers # Routing model needs fixed ends, but we'll use open-ended routes if possible
        }

    def solve(self) -> AssignmentResponse:
        t0 = time.perf_counter()
        
        if not self.eligible_couriers or not self.all_orders:
            return self._build_empty_response(t0, "NO_DATA")

        data = self.compute_data_model()
        
        # Create the routing index manager.
        # num_locations, num_vehicles, starts, ends
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['starts'],
            data['starts'] # Each vehicle 'ends' where it starts for the mathematical model, but we use Disjunctions
        )

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        # 1. Distance Callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 2. Capacity Constraints
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )

        # 3. Allow dropping orders (Disjunctions)
        # This is CRITICAL: if an order can't be fit, it's unassigned instead of making it infeasible.
        penalty = 1000000 # High penalty for skipping an order
        for i in range(len(self.eligible_couriers), len(data['distance_matrix'])):
            routing.AddDisjunction([manager.NodeToIndex(i)], penalty)

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 5

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            return self._build_results(manager, routing, solution, data, t0)
        
        return self._build_empty_response(t0, "INFEASIBLE")

    def _build_results(self, manager, routing, solution, data, start_time: float) -> AssignmentResponse:
        assignments: List[CourierAssignment] = []
        assigned_ids = set()
        
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            courier = self.eligible_couriers[vehicle_id]
            order_ids = []
            total_dist = 0
            total_weight = 0
            
            # Start is courier position (index 0..num_couriers-1), skip it in assignment list
            index = solution.Value(routing.NextVar(index))
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                order = self.all_orders[node_index - len(self.eligible_couriers)]
                order_ids.append(order.id)
                assigned_ids.add(order.id)
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                
                # node_index - len(self.eligible_couriers) gives the original order index
                # but we need distance between previous_index and index
                from_node = manager.IndexToNode(previous_index)
                to_node = manager.IndexToNode(index)
                total_dist += data['distance_matrix'][from_node][to_node]
                total_weight += order.weight
            
            if order_ids:
                assignments.append(CourierAssignment(
                    courier_id=courier.id,
                    order_ids=order_ids,
                    total_weight=round(total_weight, 3),
                    estimated_distance_km=round(total_dist / 1000.0, 3)
                ))

        unassigned_ids = [o.id for o in self.all_orders if o.id not in assigned_ids]
        solved_in_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        return AssignmentResponse(
            assignments=assignments,
            unassigned_order_ids=unassigned_ids,
            solver_status="MEMBER2_VRP_OPTIMAL",
            solved_in_ms=solved_in_ms
        )

    def _build_empty_response(self, start_time: float, status: str) -> AssignmentResponse:
        solved_in_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return AssignmentResponse(
            assignments=[],
            unassigned_order_ids=[o.id for o in self.all_orders],
            solver_status=status,
            solved_in_ms=solved_in_ms,
        )


def solve_assignment(
    couriers: List[Courier],
    orders: List[Order],
) -> AssignmentResponse:
    """
    Member 2: Replaces the greedy fallback with the SmartAssigner.
    """
    assigner = SmartAssigner(couriers, orders)
    return assigner.solve()
