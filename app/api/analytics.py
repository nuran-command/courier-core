"""
app/api/analytics.py — Service Level Agreement (SLA) & ML-Ready monitoring.
One of the key requirements for Member 1 in the Jana Courier challenge.
"""
from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import AssignmentLog, get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/sla", summary="Operational Analytics & SLA Monitoring")
def get_sla_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Calculates operational health for the judges.
    - Total assignments
    - Average solver speed
    - Priority distribution (SLA Awareness)
    """
    total_count = db.query(AssignmentLog).count()
    
    # Priority distribution (SLA)
    priority_stats = (
        db.query(AssignmentLog.order_priority, func.count(AssignmentLog.id))
        .group_by(AssignmentLog.order_priority)
        .all()
    )
    priority_map = {str(p[0]): p[1] for p in priority_stats if p[0] is not None}

    # Avg solve speed
    avg_speed = db.query(func.avg(AssignmentLog.solved_in_ms)).scalar() or 0.0

    return {
        "total_assignments": total_count,
        "avg_solver_speed_ms": round(float(avg_speed), 2),
        "priority_distribution": priority_map,
        "sla_status": "MONITORING",
        "ml_ready_records": total_count
    }
