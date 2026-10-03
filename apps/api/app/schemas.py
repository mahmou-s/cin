from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator
from enum import Enum
from .models import ActivityDomain, SupportType, VerificationStatus

class CommunityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    country_code: str = Field("EG", min_length=2, max_length=8)
    location: str | None = None
    population: int | None = Field(None, ge=0)
    description: str | None = None

class EvidenceInput(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    evidence_type: str = "document"
    original_filename: str | None = None
    content_text: str | None = None
    content_url: str | None = None
    sha256: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = Field(None, ge=0)
    authority: float = Field(.5, ge=0, le=1)
    directness: float = Field(.5, ge=0, le=1)
    recency: float = Field(.5, ge=0, le=1)
    validation: float = Field(.5, ge=0, le=1)
    consistency: float = Field(.5, ge=0, le=1)
    independence: float = Field(.5, ge=0, le=1)
    completeness: float = Field(.5, ge=0, le=1)

class AssertionSubmit(BaseModel):
    community: CommunityCreate
    capability_type_id: UUID
    scope: str | None = None
    scale: str | None = None
    quantity: float | None = None
    unit: str | None = None
    measurement_period: str | None = None
    maturity_level: str = "EMERGING"
    evidence: list[EvidenceInput] = Field(min_length=1)

class EvidenceReviewAssessment(BaseModel):
    evidence_id: UUID
    authority: float = Field(..., ge=0, le=1)
    directness: float = Field(..., ge=0, le=1)
    recency: float = Field(..., ge=0, le=1)
    validation: float = Field(..., ge=0, le=1)
    consistency: float = Field(..., ge=0, le=1)
    independence: float = Field(..., ge=0, le=1)
    completeness: float = Field(..., ge=0, le=1)
    independence_key: str | None = Field(None, min_length=1, max_length=255)
    confirm_derived_independence: bool = False


class AssertionReview(BaseModel):
    decision: str = Field(pattern="^(VERIFY|REJECT|CONFLICT)$")
    note: str | None = None
    contradiction_score: float = Field(0.0, ge=0, le=1)
    evidence_assessments: list[EvidenceReviewAssessment] = Field(min_length=1)

class CapabilityOut(BaseModel):
    id: UUID
    code: str
    domain: str
    name: str
    description: str | None = None

class AssertionOut(BaseModel):
    id: UUID
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence_score: float
    confidence_raw_score: float
    confidence_gate_reasons: dict
    confidence_level: str
    status: str
    conflict_flag: bool
    outbox_event_id: UUID | None = None
    outbox_status: str | None = None

class PendingEvidenceOut(BaseModel):
    id: UUID
    derived_independence_key: str
    canonical_independence_key: str

class PendingAssertionOut(BaseModel):
    id: UUID
    evidence_ids: list[UUID] = Field(default_factory=list)
    evidence: list[PendingEvidenceOut] = Field(default_factory=list)
    community_name: str
    capability_code: str
    capability_name: str
    confidence_score: float
    confidence_raw_score: float
    confidence_gate_reasons: dict
    confidence_level: str
    status: str
    created_at: str

class UserProfileCreate(BaseModel):
    principal_id: str = Field(min_length=2, max_length=100)
    country_code: str = Field("EG", min_length=2, max_length=8)
    governorate: str | None = Field(None, max_length=120)
    center: str | None = Field(None, max_length=120)
    village: str | None = Field(None, max_length=120)
    national_id: str | None = Field(None, min_length=4, max_length=64)
    display_name: str = Field(min_length=2, max_length=255)
    organization_name: str | None = Field(None, max_length=255)
    commercial_register: str | None = Field(None, max_length=120)
    entity_type: str = Field("INDIVIDUAL", pattern="^(INDIVIDUAL|COMPANY|GOVERNMENT|SCHOOL|HOSPITAL|OTHER)$")
    activity_domains: list[ActivityDomain] = Field(min_length=1)
    bio: str | None = None

class UserProfileUpdate(BaseModel):
    country_code: str | None = Field(None, min_length=2, max_length=8)
    governorate: str | None = Field(None, max_length=120)
    center: str | None = Field(None, max_length=120)
    village: str | None = Field(None, max_length=120)
    national_id: str | None = Field(None, min_length=4, max_length=64)
    display_name: str | None = Field(None, min_length=2, max_length=255)
    organization_name: str | None = Field(None, max_length=255)
    commercial_register: str | None = Field(None, max_length=120)
    entity_type: str | None = Field(None, pattern="^(INDIVIDUAL|COMPANY|GOVERNMENT|SCHOOL|HOSPITAL|OTHER)$")
    activity_domains: list[ActivityDomain] | None = None
    bio: str | None = None

class ProductionCapacityInput(BaseModel):
    quantity: float = Field(..., ge=0)
    unit: str = Field(min_length=1, max_length=80)
    quality_description: str | None = None
    commitment_volume: float | None = Field(None, ge=0)
    commitment_unit: str | None = Field(None, max_length=80)
    delivery_days: int | None = Field(None, ge=0)
    delivery_term: str | None = Field(None, max_length=120)
    measurement_period: str | None = Field(None, max_length=80)

class OwnershipDetailInput(BaseModel):
    asset_type: str = Field(min_length=2, max_length=50)
    tenure_type: str = Field(pattern="^(OWNED|LEASED|OTHER)$")
    area: float | None = Field(None, ge=0)
    area_unit: str | None = Field(None, max_length=40)
    notes: str | None = None

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=80)
    activity_domain: ActivityDomain
    description: str | None = None
    features: list[str] = Field(default_factory=list)
    additional_services: list[str] = Field(default_factory=list)
    media: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    capability_assertion_ids: list[UUID] = Field(default_factory=list)
    production_capacity: ProductionCapacityInput
    goal: str | None = None
    support_types: list[SupportType] = Field(default_factory=list)
    ownership: OwnershipDetailInput | None = None

    @model_validator(mode="after")
    def validate_activity_ownership(self):
        if self.activity_domain == ActivityDomain.AGRICULTURAL:
            if self.ownership is None or self.ownership.area is None or not self.ownership.area_unit:
                raise ValueError("Agricultural products require ownership tenure, land area, and area unit")
        if self.activity_domain == ActivityDomain.INDUSTRIAL:
            if self.ownership is None or self.ownership.tenure_type not in {"OWNED", "LEASED"}:
                raise ValueError("Industrial products require factory/workshop ownership tenure")
        return self

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    category: str | None = Field(None, min_length=2, max_length=80)
    activity_domain: ActivityDomain | None = None
    description: str | None = None
    features: list[str] | None = None
    additional_services: list[str] | None = None
    media: list[str] | None = None
    documents: list[str] | None = None
    evidence_ids: list[UUID] | None = None
    capability_assertion_ids: list[UUID] | None = None
    production_capacity: ProductionCapacityInput | None = None
    goal: str | None = None
    support_types: list[SupportType] | None = None
    ownership: OwnershipDetailInput | None = None

    @model_validator(mode="after")
    def validate_partial_activity_ownership(self):
        if self.activity_domain == ActivityDomain.AGRICULTURAL and self.ownership is not None and (self.ownership.area is None or not self.ownership.area_unit):
            raise ValueError("Agricultural ownership updates require land area and area unit")
        if self.activity_domain == ActivityDomain.INDUSTRIAL and self.ownership is not None and self.ownership.tenure_type not in {"OWNED", "LEASED"}:
            raise ValueError("Industrial ownership requires OWNED or LEASED tenure")
        return self

class ProductionCapacityOut(ProductionCapacityInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID

class OwnershipDetailOut(OwnershipDetailInput):
    model_config = ConfigDict(from_attributes=True)
    id: UUID

class InvestmentSupportRequestCreate(BaseModel):
    request_type: str = Field(min_length=2, max_length=40)
    goal: str = Field(min_length=2)
    requested_amount: float | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=12)
    details: str | None = None

class InvestmentSupportRequestOut(InvestmentSupportRequestCreate):
    id: UUID
    product_id: UUID
    profile_id: UUID
    status: VerificationStatus

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    profile_id: UUID
    name: str
    category: str
    activity_domain: ActivityDomain
    description: str | None = None
    features: list[str] = Field(default_factory=list)
    additional_services: list[str] = Field(default_factory=list)
    media: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)
    capability_assertion_ids: list[UUID] = Field(default_factory=list)
    production_capacity: ProductionCapacityOut
    goal: str | None = None
    support_types: list[SupportType] = Field(default_factory=list)
    ownership: OwnershipDetailOut | None = None
    verification_status: VerificationStatus
    ai_confidence_score: float = Field(0, ge=0, le=1)
    ai_confidence_level: str = "UNVERIFIED"

class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    principal_id: str
    country_code: str
    governorate: str | None = None
    center: str | None = None
    village: str | None = None
    national_id: str | None = None
    display_name: str
    organization_name: str | None = None
    commercial_register: str | None = None
    entity_type: str
    activity_domains: list[ActivityDomain]
    bio: str | None = None
    verification_status: VerificationStatus
    products: list[ProductOut] = Field(default_factory=list)
    ai_confidence_score: float = Field(0, ge=0, le=1)
    ai_confidence_level: str = "UNVERIFIED"



class LogisticsProfileCreate(BaseModel):
    origin_country: str = Field(min_length=2, max_length=8)
    origin_region: str | None = Field(None, max_length=120)
    origin_location: str | None = Field(None, max_length=255)
    destination_country: str | None = Field(None, max_length=8)
    destination_location: str | None = Field(None, max_length=255)
    transport_modes: list[str] = Field(default_factory=list)
    storage_requirements: list[str] = Field(default_factory=list)
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    shelf_life_days: int | None = Field(None, ge=0)
    packaging_requirements: str | None = None
    customs_required: bool = False
    insurance_required: bool = False
    tracking_required: bool = False
    ready_in_days: int | None = Field(None, ge=0)
    notes: str | None = None

class LogisticsProfileOut(LogisticsProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    verification_status: VerificationStatus

class LogisticsRouteCreate(BaseModel):
    origin: str = Field(min_length=2, max_length=255)
    destination: str = Field(min_length=2, max_length=255)
    mode: str = Field(min_length=2, max_length=40)
    distance_km: float | None = Field(None, ge=0)
    estimated_days: float | None = Field(None, ge=0)
    capacity_quantity: float | None = Field(None, ge=0)
    capacity_unit: str | None = Field(None, max_length=80)
    cold_chain: bool = False
    customs_support: bool = False
    tracking_available: bool = False
    evidence_ids: list[UUID] = Field(default_factory=list)

class LogisticsRouteOut(LogisticsRouteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    verification_status: VerificationStatus

class ProductComponentCreate(BaseModel):
    component_product_id: UUID
    quantity: float | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=80)
    source_type: str = Field("EXTERNAL", pattern="^(INTERNAL|EXTERNAL)$")
    required: bool = True
    notes: str | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)

class ProductComponentOut(ProductComponentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    verification_status: VerificationStatus

class ValueChainLinkCreate(BaseModel):
    from_profile_id: UUID
    to_profile_id: UUID
    from_product_id: UUID | None = None
    to_product_id: UUID | None = None
    stage_type: str = Field(min_length=2, max_length=40)
    sequence_order: int = Field(1, ge=1)
    relationship_type: str = Field("SUPPLIES", min_length=2, max_length=50)
    notes: str | None = None
    evidence_ids: list[UUID] = Field(default_factory=list)

class ValueChainLinkOut(ValueChainLinkCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    verification_status: VerificationStatus

class ValueChainOut(BaseModel):
    product_id: UUID
    components: list[ProductComponentOut] = Field(default_factory=list)
    links: list[ValueChainLinkOut] = Field(default_factory=list)


class OutreachSignalCreate(BaseModel):
    source_content_ref: str = Field(min_length=1, max_length=2000)
    external_entity_ref: str = Field(min_length=1, max_length=255)

class OutreachSignalOut(BaseModel):
    id: UUID
    source_content_ref: str
    external_entity_ref: str
    created_at: datetime
    idempotent: bool = False

class ClientIntelligenceProfileCreate(BaseModel):
    segment: str = 'OTHER'
    organization_size: str | None = None
    strategic_objectives: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    decision_horizon: str | None = None
    readiness_level: str | None = None
    desired_future: str | None = None
    future_horizon: str | None = None
    preferred_scenarios: list[str] = Field(default_factory=list)
    readiness_barriers: list[str] = Field(default_factory=list)

class ClientIntelligenceProfileOut(ClientIntelligenceProfileCreate):
    id: UUID; principal_id: str; profile_confidence: float
    model_config = ConfigDict(from_attributes=True)

class CINQuestionOut(BaseModel):
    id: UUID; question_key: str; segment: str; text: str; options: list[str]; allow_free_text: bool
    model_config = ConfigDict(from_attributes=True)

class QuestionSessionStart(BaseModel):
    segment: str = 'OTHER'

class QuestionAnswerIn(BaseModel):
    mode: str = Field(pattern='^(CHOICE|FREE_TEXT|OTHER)$')
    selected_option: str | None = None
    free_text: str | None = None

class QuestionAnswerOut(BaseModel):
    answer_id: UUID; concepts: list[str]; next_question: CINQuestionOut | None; completed: bool
