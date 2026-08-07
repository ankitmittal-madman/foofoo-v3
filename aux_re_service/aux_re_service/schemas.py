"""Independent wire contracts. Existing-engine payloads remain deliberately opaque."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    dish_categories: list[str] = Field(default_factory=list)
    spice_profiles: list[str] = Field(default_factory=list)
    spice_level: int | None = Field(default=None, ge=1, le=5)
    nutrition_traits: list[str] = Field(default_factory=list)
    seasons: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    substitutes: list[str] = Field(default_factory=list)
    cook_minutes: int | None = Field(default=None, ge=0, le=1440)
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
    leftover_items: list[str] = Field(default_factory=list)
    recent_meals: list[str] = Field(default_factory=list)
    weekly_meals: list[str] = Field(default_factory=list)
    unavailable_ingredients: list[str] = Field(default_factory=list)
    plan_date: date | None = None
    day_type: Literal["weekday", "weekend"] | None = None
    season: str | None = None
    occasion: str | None = None
    preferred_spice_level: int | None = Field(default=None, ge=1, le=5)
    available_cook_minutes: int | None = Field(default=None, ge=0, le=1440)
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


class FeedbackEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    household_id: str = Field(min_length=1, max_length=128)
    dish_id: str = Field(min_length=1, max_length=128)
    event_type: Literal[
        "viewed",
        "saved",
        "planned",
        "cooked",
        "rated",
        "skipped",
        "not_today",
        "never",
        "substituted",
        "household_vote",
        "repeat",
        "rejected",
    ]
    event_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    meal_slot: str | None = None
    member_id: str | None = None
    recommendation_rank: int | None = Field(default=None, ge=1, le=1000)
    feedback_score: int | None = Field(default=None, ge=1, le=5)
    substitute_dish_id: str | None = None
    context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event_details(self) -> FeedbackEvent:
        if self.event_type in {"rated", "household_vote"} and self.feedback_score is None:
            raise ValueError("rated and household_vote events require feedback_score")
        if self.event_type == "household_vote" and not self.member_id:
            raise ValueError("household_vote events require member_id")
        if self.event_type == "substituted" and not self.substitute_dish_id:
            raise ValueError("substituted events require substitute_dish_id")
        return self


class FeedbackReceipt(BaseModel):
    accepted: bool
    stored: bool
    event_id: str
