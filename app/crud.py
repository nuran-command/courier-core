"""
app/crud.py — Database read/write helpers for assignment logs.
"""
from sqlalchemy.orm import Session

from app.db import AssignmentLog
from app.models import AssignmentResponse


def save_assignment_result(
    db: Session,
    response: AssignmentResponse,
) -> None:
    """Persist each (courier, order) pairing from an AssignmentResponse."""
    for assignment in response.assignments:
        for order_id in assignment.order_ids:
            log_entry = AssignmentLog(
                courier_id=assignment.courier_id,
                order_id=order_id,
                reason_distance_km=assignment.estimated_distance_km,
                solver_status=response.solver_status,
                solved_in_ms=response.solved_in_ms,
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
