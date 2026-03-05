"""
app/core/engine.py — Smart Assignment Engine using OR-Tools (Member 2)

Replaces `app/core/assignment.py` greedy logic with mathematical optimization.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
import numpy as np

from ortools.linear_solver import pywraplp

from app.models import (
    AssignmentResponse,
    Courier,
    CourierAssignment,
    Order,
)
from app.core.filters import filter_available_couriers
from app.core.distances import compute_distance_matrix, compute_objective_score


class SmartAssigner:
    """
    Core Optimization Engine using Google OR-Tools.
    Models the problem as a Generalized Assignment Problem (MIP).
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
        
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
    def prepare_data(self) -> bool:
        """
        Precomputes the distance and cost matrices.
        Returns True if we have valid data to solve, False otherwise.
        """
        if not self.eligible_couriers or not self.all_orders:
            return False
            
        # Distance matrix [courier_id][order_id] -> float
        self.dist_matrix = compute_distance_matrix(
            self.eligible_couriers, self.all_orders, self.osrm_base_url
        )
        
        # We need integer indices for OR-Tools
        self.num_couriers = len(self.eligible_couriers)
        self.num_orders = len(self.all_orders)
        
        # Cost matrix: cost[i][j] = objective score to assign courier i to order j
        self.costs = np.zeros((self.num_couriers, self.num_orders))
        
        for i, c in enumerate(self.eligible_couriers):
            for j, o in enumerate(self.all_orders):
                dist_km = self.dist_matrix[c.id][o.id]
                score = compute_objective_score(dist_km, o, current_time=self.now)
                self.costs[i][j] = score
                
        # Courier capacities and order weights
        self.courier_capacities = [c.available_capacity for c in self.eligible_couriers]
        self.order_weights = [o.weight for o in self.all_orders]
        
        return True

    def build_model(self):
        """
        Sets up variables, constraints, and the objective function.
        """
        # x[i, j] is 1 if courier i is assigned to order j, else 0
        self.x = {}
        for i in range(self.num_couriers):
            for j in range(self.num_orders):
                self.x[i, j] = self.solver.IntVar(0, 1, f'x_{i}_{j}')
                
        # y[j] is 1 if order j is UNASSIGNED, else 0
        # This allows the solver to drop orders if capacity is exceeded, 
        # but penalizes doing so heavily.
        self.y = {}
        for j in range(self.num_orders):
            self.y[j] = self.solver.IntVar(0, 1, f'y_{j}')

        # Constraint 1: Each order is assigned to at most 1 courier, OR it is unassigned (y=1)
        for j in range(self.num_orders):
            self.solver.Add(sum(self.x[i, j] for i in range(self.num_couriers)) + self.y[j] == 1)

        # Constraint 2: Courier Capacity Constraint
        for i in range(self.num_couriers):
            self.solver.Add(
                sum(self.x[i, j] * self.order_weights[j] for j in range(self.num_orders)) <= self.courier_capacities[i]
            )
            
        # Objective function
        # Minimize the total cost of assignments PLUS huge penalties for unassigned orders.
        # Penalty depends on the priority and SLA of the order, effectively ensuring that
        # VIP and urgent orders are the LAST to be dropped.
        objective_terms = []
        
        # Sum of standard assignment costs + Load Balancing factor
        # To balance load, we can add a penalty for assigning an order to a courier 
        # who already has a high current_load relative to their capacity or simply
        # penalizing variance. Since this is a linear model, we add a cost 
        # proportional to the courier's *existing* load or a small baseline penalty
        # per assignment to spread out orders.
        # `c.current_load` / `c.capacity` gives the utilization %.
        
        for i, c in enumerate(self.eligible_couriers):
            # Load balancing penalty: The fuller the courier already is, the more it costs to give them another order.
            # This encourages giving orders to couriers with lower utilization.
            utilization = c.current_load / c.capacity if c.capacity > 0 else 1.0
            lb_penalty = 10.0 * utilization  
            
            for j in range(self.num_orders):
                # Total edge cost = Distance_cost + Load_balancing_penalty
                edge_cost = self.costs[i][j] + lb_penalty
                objective_terms.append(edge_cost * self.x[i, j])
                
        # Unassigned Penalties
        for j, o in enumerate(self.all_orders):
            # Calculate a massive penalty for not assigning this order.
            # Orders with a large Priority_Weight / Time_left should have astronomical drop penalties.
            penalty = 100000.0 * (compute_objective_score(10.0, o, current_time=self.now))
            # Just some large multiplier ensuring it prefers any assignment over no assignment.
            objective_terms.append(penalty * self.y[j])
            
        self.solver.Minimize(self.solver.Sum(objective_terms))
        
        # Time limit
        self.solver.set_time_limit(5000) # 5 seconds max

    def solve(self) -> AssignmentResponse:
        t0 = time.perf_counter()
        
        if not self.prepare_data():
            # Nothing to solve (e.g. no couriers available)
            return self._build_empty_response(t0, "MEMBER2_NO_DATA")
            
        self.build_model()
        
        status = self.solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
            return self._build_results(status, t0)
        else:
            return self._build_empty_response(t0, "MEMBER2_INFEASIBLE")

    def _build_results(self, status, start_time: float) -> AssignmentResponse:
        assignments: List[CourierAssignment] = []
        unassigned_order_ids: List[str] = []
        
        for j in range(self.num_orders):
            # Check if order j was unassigned
            if self.y[j].solution_value() > 0.5:
                unassigned_order_ids.append(self.all_orders[j].id)
                
        for i in range(self.num_couriers):
            assigned_orders = []
            total_w = 0.0
            total_dist = 0.0
            
            for j in range(self.num_orders):
                if self.x[i, j].solution_value() > 0.5:
                    o = self.all_orders[j]
                    assigned_orders.append(o.id)
                    total_w += o.weight
                    total_dist += self.dist_matrix[self.eligible_couriers[i].id][o.id]
                    
            if assigned_orders:
                assignments.append(CourierAssignment(
                    courier_id=self.eligible_couriers[i].id,
                    order_ids=assigned_orders,
                    total_weight=round(total_w, 3),
                    estimated_distance_km=round(total_dist, 3)
                ))
                
        solved_in_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status_str = "MEMBER2_OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "MEMBER2_FEASIBLE"
        
        return AssignmentResponse(
            assignments=assignments,
            unassigned_order_ids=unassigned_order_ids + [o.id for o in self.all_orders if o.id in unassigned_order_ids], # In case
            solver_status=status_str,
            solved_in_ms=solved_in_ms,
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
