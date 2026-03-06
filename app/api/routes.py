"""
app/api/routes.py — FastAPI route definitions.

Endpoints:
  GET  /              — Health check
  POST /assign        — Main assignment endpoint
  GET  /history       — Recent assignment log (audit)
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.assignment import solve_assignment
from app.core.filters import filter_available_couriers
from app.crud import get_assignment_history, save_assignment_result
from app.db import AssignmentLog, get_db
from app.models import AssignmentRequest, AssignmentResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

@router.get("/", tags=["Health"])
def health_check():
    """Liveness probe — confirms the service is running."""
    return {"status": "ok", "service": "Courier Core — Smart Assignment Engine"}


# ---------------------------------------------------------------------------
# POST /assign
# ---------------------------------------------------------------------------

@router.post(
    "/assign",
    response_model=AssignmentResponse,
    tags=["Assignment"],
    summary="Assign orders to couriers",
    description=(
        "Accepts a list of couriers and orders, filters out over-capacity "
        "couriers, runs the Smart Assignment Engine (OR-Tools CVRP with "
        "deadline/priority cost, greedy fallback), persists the result, "
        "and returns the assignment map."
    ),
)
def assign_orders(
    body: AssignmentRequest,
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    # 1. Filter couriers by load capacity and availability
    eligible_couriers, rejected = filter_available_couriers(
        body.couriers, body.orders
    )

    if not eligible_couriers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No eligible couriers found. All couriers are either offline, "
                "busy, or at maximum capacity."
            ),
        )

    # 2. Run the solver
    result: AssignmentResponse = solve_assignment(eligible_couriers, body.orders)

    # 3. Persist to DB (incl. priorities and deadlines for ML)
    save_assignment_result(db, result, body.orders)

    return result


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    tags=["Assignment"],
    summary="Recent assignment log",
)
def assignment_history(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return the most recent assignment log entries (for audit / analytics)."""
    rows: List[AssignmentLog] = get_assignment_history(db, limit=min(limit, 200))
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "courier_id": r.courier_id,
            "order_id": r.order_id,
            "distance_km": r.reason_distance_km,
            "solver_status": r.solver_status,
            "solved_in_ms": r.solved_in_ms,
        }
        for r in rows
    ]
