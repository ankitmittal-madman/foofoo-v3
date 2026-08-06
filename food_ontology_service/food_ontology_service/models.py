from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
import unicodedata
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReviewStatus(StrEnum):
    provisional = "provisional"
    accepted = "accepted"
    rejected = "rejected"


class PlanningRole(StrEnum):
    primary = "primary"
    addon = "addon"
    combo_component = "combo_component"


class RelationshipType(StrEnum):
    same_as = "same_as"
    variant_of = "variant_of"
    parent_of = "parent_of"
    sibling_of = "sibling_of"
    similar_to = "similar_to"
    substitute_for = "substitute_for"


class EvidenceRef(BaseModel):
    source_code: str = Field(min_length=2, max_length=80)
    source_record_id: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=2048)
    source_version: str | None = Field(default=None, max_length=100)
    extraction_method: str = Field(min_length=2, max_length=80)


class FieldValue(BaseModel):
    value: Any
    confidence: float = Field(ge=0, le=1)
    review_status: ReviewStatus = ReviewStatus.provisional
    evidence: list[EvidenceRef] = Field(min_length=1)
    last_verified_at: datetime = Field(default_factory=utcnow)


class AliasInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    language: str = Field(default="en", min_length=2, max_length=20)
    region_code: str | None = Field(default=None, max_length=80)
    alias_type: str = Field(default="synonym", max_length=40)
    confidence: float = Field(ge=0, le=1)
    evidence: list[EvidenceRef] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", value).split())


class ClassMembershipInput(BaseModel):
    class_code: str = Field(min_length=2, max_length=80)
    slot: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    role: PlanningRole
    confidence: float = Field(ge=0, le=1)
    review_status: ReviewStatus = ReviewStatus.provisional
    evidence: list[EvidenceRef] = Field(min_length=1)


class DishCreate(BaseModel):
    canonical_name: str = Field(min_length=2, max_length=160)
    locale: str = Field(default="en-IN", min_length=2, max_length=20)
    description: FieldValue | None = None
    aliases: list[AliasInput] = Field(default_factory=list, max_length=100)
    class_memberships: list[ClassMembershipInput] = Field(default_factory=list, max_length=50)
    fields: dict[str, FieldValue] = Field(default_factory=dict)

    @field_validator("canonical_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(unicodedata.normalize("NFKC", value).split())


class DishPatch(BaseModel):
    canonical_name: str | None = Field(default=None, min_length=2, max_length=160)
    description: FieldValue | None = None
    aliases: list[AliasInput] | None = Field(default=None, max_length=100)
    class_memberships: list[ClassMembershipInput] | None = Field(default=None, max_length=50)
    fields: dict[str, FieldValue] | None = None


class SimilarityInput(BaseModel):
    target_dish_id: UUID
    relationship: RelationshipType
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    explanation_features: list[str] = Field(default_factory=list, max_length=20)
    evidence: list[EvidenceRef] = Field(min_length=1)


class FeedbackInput(BaseModel):
    field_path: str = Field(min_length=1, max_length=160)
    proposed_value: Any
    reason: str = Field(min_length=2, max_length=1000)
    actor_reference: str | None = Field(default=None, max_length=160)


class EnrichmentRequest(BaseModel):
    fields: list[str] = Field(default_factory=list, max_length=100)
    priority: int = Field(default=50, ge=0, le=100)
    force: bool = False


class ImageRef(BaseModel):
    cloudinary_public_id: str = Field(min_length=2, max_length=500)
    cloudinary_asset_id: str | None = Field(default=None, max_length=200)
    cloudinary_version: int | None = Field(default=None, ge=1)
    secure_url: str = Field(pattern="^https://")
    checksum_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    source_type: str = Field(pattern="^(licensed_source|ai_generated|human_upload)$")
    licence_code: str | None = Field(default=None, max_length=80)
    attribution: str | None = Field(default=None, max_length=500)
    review_status: ReviewStatus
    is_primary: bool = False

    @model_validator(mode="after")
    def sourced_images_need_licence(self):
        if self.source_type == "licensed_source" and not self.licence_code:
            raise ValueError("licensed_source images require licence_code")
        return self


class DishRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    canonical_name: str
    normalized_name: str
    locale: str
    status: str = "draft"
    description: FieldValue | None = None
    aliases: list[AliasInput] = Field(default_factory=list)
    class_memberships: list[ClassMembershipInput] = Field(default_factory=list)
    fields: dict[str, FieldValue] = Field(default_factory=dict)
    relationships: list[SimilarityInput] = Field(default_factory=list)
    images: list[ImageRef] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
