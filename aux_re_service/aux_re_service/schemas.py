"""Independent wire contracts. Existing-engine payloads remain deliberately opaque."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Candidate(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    ingredients: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    diet_types: list[str] = Field(default_factory=list)
    cuisines: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    meal_slots: list[str] = Field(default_factory=list)
    pantry_match: float = Field(0.0, ge=0.0, le=1.0)
    nutrition_fit: float = Field(0.5, ge=0.0, le=1.0)
    freshness: float = Field(0.5, ge=0.0, le=1.0)
    collaborative_score: float = Field(0.5, ge=0.0, le=1.0)
    popularity: float = Field(0.0, ge=0.0, le=1.0)


class HouseholdMember(BaseModel):
    model_config = ConfigDict(extra="allow")

    member_id: str | None = None
    preferences: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: str
    household_id: str
    meal_slot: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    locale: str = "en-IN"
    region: str | None = None
    preferences: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    household_members: list[HouseholdMember] = Field(default_factory=list)
    pantry_items: list[str] = Field(default_factory=list)
    recent_meals: list[str] = Field(default_factory=list)
    unavailable_ingredients: list[str] = Field(default_factory=list)
    candidate_limit: int = Field(10, ge=1, le=100)
    debug: bool = False
    existing_result: dict[str, Any]
    candidates: list[Candidate] = Field(default_factory=list)


class ConstraintCheck(BaseModel):
    passed: bool
    reasons: list[str] = Field(default_factory=list)


class RecommendationSet(BaseModel):
    items: list[dict[str, Any]]
    quality_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    diversity_score: float = Field(ge=0.0, le=1.0)
    safety_score: float = Field(ge=0.0, le=1.0)
    alignment_score: float = Field(ge=0.0, le=1.0)


class RecommendationResponse(BaseModel):
    trace_id: str
    existing_result: dict[str, Any]
    auxiliary_result: RecommendationSet | None
    selected_result: dict[str, Any]
    decision: str
    decision_reason: str
    scores: dict[str, float]
    constraint_checks: ConstraintCheck
    model_metadata: dict[str, Any]
    timings_ms: dict[str, float]
    debug_trace: dict[str, Any] | None = None
