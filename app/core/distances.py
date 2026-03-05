import math
from datetime import datetime, timezone
from typing import List, Dict

from app.models import Courier, Order
from app.core.geo import get_distance_km

# Weight coefficient for priority in the objective function
PRIORITY_WEIGHTS = {
    1: 1.0,  # LOW
    2: 2.0,  # NORMAL
    3: 5.0,  # MEDIUM
    4: 15.0, # HIGH
    5: 50.0, # VIP - extremely high weight to mandate fast delivery
}


def compute_distance_matrix(
    couriers: List[Courier], 
    orders: List[Order], 
    osrm_base_url: str = ""
) -> Dict[str, Dict[str, float]]:
    """
    Computes a distance matrix between all couriers and all orders.
    
    Returns a nested dictionary where:
        matrix[courier_id][order_id] = distance in km
    """
    matrix: Dict[str, Dict[str, float]] = {}
    
    for courier in couriers:
        matrix[courier.id] = {}
        for order in orders:
            dist = get_distance_km(
                lat1=courier.lat,
                lon1=courier.lon,
                lat2=order.lat,
                lon2=order.lon,
                osrm_base_url=osrm_base_url
            )
            matrix[courier.id][order.id] = dist
            
    return matrix


def compute_objective_score(
    distance_km: float, 
    order: Order, 
    current_time: datetime = None
) -> float:
    """
    Computes the 'cost' of assigning this order to a given courier at this distance.
    Lower score is better.
    
    Score = Distance_KM + Penalty_For_Deadline
    
    Penalty_For_Deadline considers Order Priority and Time Left until SLA deadline.
    If the deadline is close or priority is high, the cost of NOT assigning is huge.
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)
        
    # Time left in hours till deadline
    time_left_td = order.deadline - current_time
    time_left_hours = time_left_td.total_seconds() / 3600.0
    
    # Base penalty weight from priority
    priority_num = order.priority.value if hasattr(order.priority, 'value') else int(order.priority)
    p_weight = PRIORITY_WEIGHTS.get(priority_num, 1.0)
    
    # If deadline is already passed, penalize heavily
    if time_left_hours <= 0:
        penalty = 10000.0 * p_weight * abs(time_left_hours - 1.0) # Escalates the later it is
    else:
        # Inverse relation to time left. Less time = higher penalty if delayed.
        # But we actually want to *minimize* the score.
        # A high priority order with low time left should have a very LOW score 
        # so the solver picks it. Wait, standard Objective is to MINIMIZE cost.
        # Cost of servicing = distance - reward.
        # Alternatively, Cost = distance. But we MUST service VIPs.
        # So we can subtract their priority score from the objective, 
        # or we penalize UNASSIGNED orders heavily.
        
        # Actually, in generic VRP, the cost of an edge is distance. 
        # To prioritize orders, it's better to assign a huge PENALTY for dropping them,
        # or reduce the "cost" of the edge going to high priority orders.
        
        # Let's say: Score = Distance - (Priority_Weight / Time_Left). 
        # But it could go negative. 
        # Let's keep it simple: 
        # Score = Distance 
        # We will handle Priority/SLA by adding huge penalties for unassigned nodes in OR-Tools.
        
        # If we need a combined heuristic score for greedy or cost matrix:
        penalty = - (p_weight / (time_left_hours + 0.1)) * 10.0
        
    # To prevent negative costs (which some solvers dislike), we could just return distance
    # and handle SLA/Priority via specific constraints and drop penalties in the OR-Tools model.
    # But as per requirements: Score = Distance + (Priority_Weight / Time_Left_To_SLA)
    # Actually, the requirement says "Score = Distance + (Priority_Weight / Time_Left_To_SLA)". 
    # Wait, if Score is MINIMIZED, then adding Priority/TimeLeft makes the score HIGHER for VIPs?
    # No, if Time_Left is small, (Priority_Weight / Time_Left) is LARGE.
    # If we want to MINIMIZE score, this makes VIPs the *worst* to pick?
    # Let me re-read the requirement. "Чем меньше Score, тем лучше кандидат".
    # If priority is high, we want a SMALLER score.
    # So it should be Score = Distance - (Priority_Weight * K / Time_Left), or we just use Distance 
    # and add penalty to UNASSIGNED.
    # Let's formulate a strictly positive cost but discounted.
    pass

    
    # Implementing the prompt's explicit formula but ensuring it makes mathematical sense for minimization
    # Prompt says: "Пример: Score = Distance + (Priority_Weight / Time_Left_To_SLA). Чем меньше Score, тем лучше кандидат."
    # Wait, if `Time_Left_To_SLA` is large (plenty of time), fraction is small. Score is small (good).
    # If `Time_Left_To_SLA` is small (urgent), fraction is LARGE. Score is LARGE (bad candidate??).
    # That means the math in the prompt example discourages picking urgent orders if we minimize score.
    # To fix this logical bug in the prompt's example:
    # A courier is a good candidate for an URGENT (small time_left) order if we MINIMIZE cost.
    # We should REDUCE the cost to incentivize the solver.
    # Let's use: Score = Distance - (Priority_Weight * 10 / max(0.1, time_left_hours))
    # To keep it positive (some solvers require positive weights), we can shift it or just use it as a heuristic weight.
    
    score = distance_km - (p_weight * 5.0 / max(0.1, time_left_hours))
    
    # Ensure score is not negative if used directly in distance arrays that require uint
    # But for a basic heuristic, float is fine.
    # For OR-Tools, we typically scale to integers. Let's return just the distance, 
    # and we will handle the actual objective function inside engine.py (Phase 2).
    # The prompt explicitly asks to "Сформулировать формулу «веса» назначения." inside `distances.py`.
    
    return max(0.0, score + 1000) # Shifted to keep positive
