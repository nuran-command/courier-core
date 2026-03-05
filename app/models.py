"""
app/models.py — Pydantic data-transfer models for Orders and Couriers.

These models are the contract between the API consumers and the
Smart Assignment Engine. They enforce strict typing and validation.
"""
from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OrderPriority(IntEnum):
    """1 = lowest, 5 = VIP / highest urgency."""
    LOW = 1
    NORMAL = 2
    MEDIUM = 3
    HIGH = 4
    VIP = 5


class CourierStatus(str):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class Order(BaseModel):
    """A single delivery order."""

    id: str = Field(..., description="Unique order identifier")
    lat: float = Field(..., ge=-90, le=90, description="Pick-up / delivery latitude")
    lon: float = Field(..., ge=-180, le=180, description="Pick-up / delivery longitude")
    weight: float = Field(..., gt=0, description="Package weight in kg")
    priority: OrderPriority = Field(
        OrderPriority.NORMAL,
        description="Order priority 1-5 (5 = VIP)",
    )
    deadline: datetime = Field(
        ...,
        description="Latest acceptable delivery time (UTC ISO-8601)",
    )

    @field_validator("weight")
    @classmethod
    def weight_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("weight must be > 0")
        return round(v, 3)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "order-001",
                "lat": 51.1282,
                "lon": 71.4306,
                "weight": 2.5,
                "priority": 3,
                "deadline": "2026-03-05T18:00:00Z",
            }
        }


class Courier(BaseModel):
    """A courier / driver available for assignment."""

    id: str = Field(..., description="Unique courier identifier")
    lat: float = Field(..., ge=-90, le=90, description="Current latitude")
    lon: float = Field(..., ge=-180, le=180, description="Current longitude")
    capacity: float = Field(..., gt=0, description="Maximum payload in kg")
    current_load: float = Field(0.0, ge=0, description="Current load in kg already assigned")
    status: str = Field("available", description="available | busy | offline")
    rating: float = Field(
        5.0,
        ge=1.0,
        le=5.0,
        description="Courier rating (1-5). Higher = preferred.",
    )

    @model_validator(mode="after")
    def load_must_not_exceed_capacity(self) -> "Courier":
        if self.current_load > self.capacity:
            raise ValueError(
                f"current_load ({self.current_load}) exceeds capacity ({self.capacity})"
            )
        return self

    @property
    def available_capacity(self) -> float:
        return self.capacity - self.current_load

    class Config:
        json_schema_extra = {
            "example": {
                "id": "courier-A1",
                "lat": 51.1300,
                "lon": 71.4200,
                "capacity": 20.0,
                "current_load": 5.0,
                "status": "available",
                "rating": 4.7,
            }
        }


# ---------------------------------------------------------------------------
# Request / Response wrappers
# ---------------------------------------------------------------------------

class AssignmentRequest(BaseModel):
    """Payload for POST /assign."""

    couriers: List[Courier] = Field(..., min_length=1)
    orders: List[Order] = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "couriers": [Courier.Config.json_schema_extra["example"]],
                "orders": [Order.Config.json_schema_extra["example"]],
            }
        }


class CourierAssignment(BaseModel):
    """One courier's assigned order list."""

    courier_id: str
    order_ids: List[str]
    total_weight: float
    estimated_distance_km: float


class AssignmentResponse(BaseModel):
    """Full response from POST /assign."""

    assignments: List[CourierAssignment]
    unassigned_order_ids: List[str] = Field(
        default_factory=list,
        description="Orders that could not be assigned (e.g. all couriers at capacity)",
    )
    solver_status: str = Field(
        description="OR-Tools solver status or 'greedy' if fallback was used"
    )
    solved_in_ms: Optional[float] = None
