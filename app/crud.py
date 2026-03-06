"""
app/crud.py — Database read/write helpers for assignment logs.
"""
from sqlalchemy.orm import Session

from app.db import AssignmentLog
from app.models import AssignmentResponse, Order


def save_assignment_result(
    db: Session,
    response: AssignmentResponse,
    orders: list[Order],
) -> None:
    """Persist each (courier, order) pairing from an AssignmentResponse."""
    # Build a metadata lookup for faster retrieval during the loop
    order_meta = {o.id: (o.priority, o.deadline) for o in orders}

    for assignment in response.assignments:
        for order_id in assignment.order_ids:
            priority, deadline = order_meta.get(order_id, (None, None))
            
            log_entry = AssignmentLog(
                courier_id=assignment.courier_id,
                order_id=order_id,
                reason_distance_km=assignment.estimated_distance_km,
                reason_duration_min=assignment.estimated_duration_min,
                solver_status=response.solver_status,
                solved_in_ms=response.solved_in_ms,
                order_priority=int(priority) if priority else None,
                order_deadline=deadline,
            )
            db.add(log_entry)
    db.commit()


def get_assignment_history(db: Session, limit: int = 100) -> list[AssignmentLog]:
    """Return the most recent assignment log entries."""
    return (
        db.query(AssignmentLog)
        .order_by(AssignmentLog.created_at.desc())
        .limit(limit)
        .all()
    )
