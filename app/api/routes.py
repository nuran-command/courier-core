"""
app/api/routes.py — FastAPI route definitions.

Endpoints:
  GET  /              — Health check
  POST /assign        — Main assignment endpoint (Protected)
  GET  /history       — Recent assignment log (Protected)
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.assignment import solve_assignment
from app.core.filters import filter_available_couriers
from app.crud import get_assignment_history, save_assignment_result
from app.db import AssignmentLog, get_db
from app.models import AssignmentRequest, AssignmentResponse

settings = get_settings()
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Architect's Shield: Simple API Key Authentication."""
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key (Architect's Shield Active)",
        )
    return api_key

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
    dependencies=[Depends(get_api_key)],
    summary="Assign orders to couriers",
    description=(
        "Accepts a list of couriers and orders, filters out over-capacity "
        "couriers, runs the Smart Assignment Engine, persists the result, "
        "and returns the assignment map. Protected by Architect's Shield."
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
    dependencies=[Depends(get_api_key)],
    summary="Recent assignment log",
)
def assignment_history(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return the most recent assignment log entries. Protected by Architect's Shield."""
    rows: List[AssignmentLog] = get_assignment_history(db, limit=min(limit, 200))
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "courier_id": r.courier_id,
            "order_id": r.order_id,
            "distance_km": r.reason_distance_km,
            "duration_min": r.reason_duration_min,
            "solver_status": r.solver_status,
            "solved_in_ms": r.solved_in_ms,
        }
        for r in rows
    ]
