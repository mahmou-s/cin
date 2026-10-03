import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, JSON, Index, Boolean, Enum as SAEnum, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY

class Base(DeclarativeBase): pass

def uid(): return uuid.uuid4()


class ActivityDomain(str, __import__("enum").Enum):
    ECONOMIC = "ECONOMIC"
    AGRICULTURAL = "AGRICULTURAL"
    INDUSTRIAL = "INDUSTRIAL"
    SOCIAL = "SOCIAL"
    CULTURAL = "CULTURAL"
    EDUCATIONAL = "EDUCATIONAL"

class SupportType(str, __import__("enum").Enum):
    GOVERNMENT = "GOVERNMENT"
    FINANCING = "FINANCING"
    MARKETING = "MARKETING"
    CUSTOMS = "CUSTOMS"

class EvidenceKind(str, __import__("enum").Enum):
    GENERAL = "GENERAL"
    EXTERNAL_CONTACT_CHANNEL = "EXTERNAL_CONTACT_CHANNEL"

class OutreachDigestStatus(str, __import__("enum").Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class VerificationStatus(str, __import__("enum").Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class EntityType(str, __import__("enum").Enum):
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"
    GOVERNMENT = "GOVERNMENT"
    SCHOOL = "SCHOOL"
    HOSPITAL = "HOSPITAL"
    OTHER = "OTHER"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    principal_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Community(Base):
    __tablename__ = "communities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, default="EG")
    location: Mapped[str | None] = mapped_column(String(255))
    population: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    principal_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(8), nullable=False, default="EG")
    governorate: Mapped[str | None] = mapped_column(String(120))
    center: Mapped[str | None] = mapped_column(String(120))
    village: Mapped[str | None] = mapped_column(String(120))
    national_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String(255))
    commercial_register: Mapped[str | None] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False, default="INDIVIDUAL")
    activity_domains: Mapped[list[ActivityDomain]] = mapped_column(ARRAY(SAEnum(ActivityDomain, name="activity_domain", native_enum=True)), nullable=False, default=list)
    bio: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    products: Mapped[list["Product"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    ownership_details: Mapped[list["OwnershipDetail"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    investment_requests: Mapped[list["InvestmentSupportRequest"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def ai_confidence(self) -> tuple[float, str]:
        evidence_dicts = []
        for product in self.products:
            score, _ = product.ai_confidence
            if score > 0:
                evidence_dicts.extend([
                    {k: getattr(e, k) for k in ("authority", "directness", "recency", "validation", "consistency", "independence", "completeness")}
                    | {"independence_key": getattr(e, "independence_key", None), "sha256": getattr(e, "sha256", None), "content_url": getattr(e, "content_url", None)}
                    for e in product.evidences if e.validation_status == "VERIFIED"
                ])
        if not evidence_dicts:
            return 0.0, "UNVERIFIED"
        from .services.confidence import calculate_confidence_details
        score, level_name, _, _ = calculate_confidence_details(evidence_dicts)
        return score, level_name

    @property
    def ai_confidence_score(self) -> float:
        return self.ai_confidence[0]

    @property
    def ai_confidence_level(self) -> str:
        return self.ai_confidence[1]


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_domain: Mapped[ActivityDomain] = mapped_column(SAEnum(ActivityDomain, name="activity_domain", native_enum=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    features: Mapped[list] = mapped_column(JSON, default=list)
    additional_services: Mapped[list] = mapped_column(JSON, default=list)
    media: Mapped[list] = mapped_column(JSON, default=list)
    documents: Mapped[list] = mapped_column(JSON, default=list)
    goal: Mapped[str | None] = mapped_column(Text)
    support_types: Mapped[list[SupportType]] = mapped_column(ARRAY(SAEnum(SupportType, name="support_type", native_enum=True)), nullable=False, default=list)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    profile: Mapped["UserProfile"] = relationship(back_populates="products")
    production_capacity: Mapped["ProductionCapacity | None"] = relationship(back_populates="product", uselist=False, cascade="all, delete-orphan")
    ownership: Mapped["OwnershipDetail | None"] = relationship(back_populates="product", uselist=False, cascade="all, delete-orphan")
    evidences: Mapped[list["Evidence"]] = relationship(secondary="product_evidence", back_populates="products")
    capability_assertions: Mapped[list["CapabilityAssertion"]] = relationship(secondary="product_capability_assertions", back_populates="products")
    investment_requests: Mapped[list["InvestmentSupportRequest"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    logistics_profile: Mapped["ProductLogisticsProfile | None"] = relationship(back_populates="product", uselist=False, cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def ai_confidence(self) -> tuple[float, str]:
        from .services.confidence import calculate_confidence_details
        evidence_dicts = [
            {k: getattr(e, k) for k in ("authority", "directness", "recency", "validation", "consistency", "independence", "completeness")}
            | {"independence_key": getattr(e, "independence_key", None), "sha256": getattr(e, "sha256", None), "content_url": getattr(e, "content_url", None)}
            for e in self.evidences if e.validation_status == "VERIFIED"
        ]
        if not evidence_dicts:
            return 0.0, "UNVERIFIED"
        score, level_name, _, _ = calculate_confidence_details(evidence_dicts)
        return score, level_name

    @property
    def ai_confidence_score(self) -> float:
        return self.ai_confidence[0]

    @property
    def ai_confidence_level(self) -> str:
        return self.ai_confidence[1]



class ProductComponent(Base):
    __tablename__ = "product_components"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    component_product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(80))
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="EXTERNAL")
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductComponentEvidence(Base):
    __tablename__ = "product_component_evidence"
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_components.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True)



class ValueChainLink(Base):
    __tablename__ = "value_chain_links"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    from_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    to_profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    from_product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    to_product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    stage_type: Mapped[str] = mapped_column(String(40), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SUPPLIES")
    notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductLogisticsProfile(Base):
    __tablename__ = "product_logistics_profiles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    origin_country: Mapped[str] = mapped_column(String(8), nullable=False)
    origin_region: Mapped[str | None] = mapped_column(String(120))
    origin_location: Mapped[str | None] = mapped_column(String(255))
    destination_country: Mapped[str | None] = mapped_column(String(8))
    destination_location: Mapped[str | None] = mapped_column(String(255))
    transport_modes: Mapped[list] = mapped_column(JSON, default=list)
    storage_requirements: Mapped[list] = mapped_column(JSON, default=list)
    temperature_min_c: Mapped[float | None] = mapped_column(Float)
    temperature_max_c: Mapped[float | None] = mapped_column(Float)
    shelf_life_days: Mapped[int | None] = mapped_column(Integer)
    packaging_requirements: Mapped[str | None] = mapped_column(Text)
    customs_required: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_required: Mapped[bool] = mapped_column(Boolean, default=False)
    tracking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    ready_in_days: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    product: Mapped["Product"] = relationship(back_populates="logistics_profile")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogisticsRoute(Base):
    __tablename__ = "logistics_routes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(40), nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Float)
    estimated_days: Mapped[float | None] = mapped_column(Float)
    capacity_quantity: Mapped[float | None] = mapped_column(Float)
    capacity_unit: Mapped[str | None] = mapped_column(String(80))
    cold_chain: Mapped[bool] = mapped_column(Boolean, default=False)
    customs_support: Mapped[bool] = mapped_column(Boolean, default=False)
    tracking_available: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogisticsRouteEvidence(Base):
    __tablename__ = "logistics_route_evidence"
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("logistics_routes.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True)

class ProductionCapacity(Base):
    __tablename__ = "production_capacities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    quality_description: Mapped[str | None] = mapped_column(Text)
    commitment_volume: Mapped[float | None] = mapped_column(Float)
    commitment_unit: Mapped[str | None] = mapped_column(String(80))
    delivery_days: Mapped[int | None] = mapped_column(Integer)
    delivery_term: Mapped[str | None] = mapped_column(String(120))
    measurement_period: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product: Mapped["Product"] = relationship(back_populates="production_capacity")


class OwnershipDetail(Base):
    __tablename__ = "ownership_details"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    tenure_type: Mapped[str] = mapped_column(String(30), nullable=False)
    area: Mapped[float | None] = mapped_column(Float)
    area_unit: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)
    profile: Mapped["UserProfile"] = relationship(back_populates="ownership_details")
    product: Mapped["Product | None"] = relationship(back_populates="ownership")


class InvestmentSupportRequest(Base):
    __tablename__ = "investment_support_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(40), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    requested_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(12))
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[VerificationStatus] = mapped_column(SAEnum(VerificationStatus, name="verification_status"), nullable=False, default=VerificationStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    profile: Mapped["UserProfile"] = relationship(back_populates="investment_requests")
    product: Mapped["Product"] = relationship(back_populates="investment_requests")

class CapabilityType(Base):
    __tablename__ = "capability_types"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

class CapabilityAssertion(Base):
    __tablename__ = "capability_assertions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id"), nullable=False)
    capability_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_types.id"), nullable=False)
    scope: Mapped[str | None] = mapped_column(String(255))
    scale: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(100))
    measurement_period: Mapped[str | None] = mapped_column(String(100))
    maturity_level: Mapped[str] = mapped_column(String(50), default="EMERGING")
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_level: Mapped[str] = mapped_column(String(30), default="UNVERIFIED")
    conflict_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_raw_score: Mapped[float] = mapped_column(Float, default=0)
    confidence_gate_reasons: Mapped[dict] = mapped_column(JSON, default=dict)
    submitted_by: Mapped[str | None] = mapped_column(String(100), index=True)
    review_note: Mapped[str | None] = mapped_column(Text)
    products: Mapped[list["Product"]] = relationship(secondary="product_capability_assertions", back_populates="capability_assertions")
    capability_type: Mapped["CapabilityType"] = relationship()
    evidences: Mapped[list["Evidence"]] = relationship(secondary="assertion_evidence", back_populates="assertions")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    reviewed_by: Mapped[str | None] = mapped_column(String(100))
    __table_args__ = (Index("ix_assertions_status", "status"),)

class Evidence(Base):
    __tablename__ = "evidences"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_kind: Mapped[EvidenceKind] = mapped_column(SAEnum(EvidenceKind, name="evidence_kind", native_enum=True), nullable=False, default=EvidenceKind.GENERAL)
    external_entity_ref: Mapped[str | None] = mapped_column(String(255), index=True)
    evidence_type: Mapped[str] = mapped_column(String(50), default="document")
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_url: Mapped[str | None] = mapped_column(Text)
    content_text: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(150))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    validation_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    authority: Mapped[float] = mapped_column(Float, default=.5)
    directness: Mapped[float] = mapped_column(Float, default=.5)
    recency: Mapped[float] = mapped_column(Float, default=.5)
    validation: Mapped[float] = mapped_column(Float, default=.5)
    consistency: Mapped[float] = mapped_column(Float, default=.5)
    independence: Mapped[float] = mapped_column(Float, default=.5)
    completeness: Mapped[float] = mapped_column(Float, default=.5)
    independence_key: Mapped[str | None] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    products: Mapped[list["Product"]] = relationship(secondary="product_evidence", back_populates="evidences")
    assertions: Mapped[list["CapabilityAssertion"]] = relationship(secondary="assertion_evidence", back_populates="evidences")


class OutreachSignal(Base):
    __tablename__ = "outreach_signals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_content_ref: Mapped[str] = mapped_column(Text, nullable=False)
    external_entity_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("uq_outreach_signal_user_content", "user_id", "source_content_ref", unique=True),)


class OutreachDigest(Base):
    __tablename__ = "outreach_digests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    external_entity_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[OutreachDigestStatus] = mapped_column(SAEnum(OutreachDigestStatus, name="outreach_digest_status", native_enum=True), nullable=False, default=OutreachDigestStatus.PENDING)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    cooldown_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OutreachDigestSignal(Base):
    __tablename__ = "outreach_digest_signals"
    digest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outreach_digests.id", ondelete="CASCADE"), primary_key=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outreach_signals.id", ondelete="CASCADE"), primary_key=True, unique=True)


class AssertionEvidence(Base):
    __tablename__ = "assertion_evidence"
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True)

class ProductCapabilityAssertion(Base):
    __tablename__ = "product_capability_assertions"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True)

class ProductEvidence(Base):
    __tablename__ = "product_evidence"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True)
    product: Mapped["Product"] = relationship(overlaps="evidences,products")
    evidence: Mapped["Evidence"] = relationship(overlaps="evidences,products")

class EvidenceAssessment(Base):
    __tablename__ = "evidence_assessments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    authority: Mapped[float] = mapped_column(Float, nullable=False)
    directness: Mapped[float] = mapped_column(Float, nullable=False)
    recency: Mapped[float] = mapped_column(Float, nullable=False)
    validation: Mapped[float] = mapped_column(Float, nullable=False)
    consistency: Mapped[float] = mapped_column(Float, nullable=False)
    independence: Mapped[float] = mapped_column(Float, nullable=False)
    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    independence_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (Index("ix_evidence_assessments_assertion_evidence", "assertion_id", "evidence_id"),)


class ValidationEvent(Base):
    __tablename__ = "validation_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SyncEvent(Base):
    __tablename__ = "transactional_outbox"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    aggregate_type: Mapped[str] = mapped_column(String(80), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    __table_args__ = (Index("ix_sync_events_status", "status"),)

class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String(50), default="COMPLEMENTARY_CAPABILITY")
    status: Mapped[str] = mapped_column(String(30), default="PROPOSED")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OpportunityReview(Base):
    __tablename__ = "opportunity_reviews"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="reviewer")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class OpportunityProduct(Base):
    __tablename__ = "opportunity_products"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)

class OpportunityAssertion(Base):
    __tablename__ = "opportunity_assertions"
    opportunity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id", ondelete="CASCADE"), primary_key=True)

class ValueChainLinkEvidence(Base):
    __tablename__ = "value_chain_link_evidence"
    link_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("value_chain_links.id", ondelete="CASCADE"), primary_key=True)
    evidence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evidences.id", ondelete="CASCADE"), primary_key=True)


class ReasoningRun(Base):
    __tablename__ = "reasoning_runs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=True, index=True)
    engine: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED")
    actor: Mapped[str] = mapped_column(String(100), default="system")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    requested_codes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="GENERATED")
    assumptions: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ScenarioStep(Base):
    __tablename__ = "scenario_steps"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    scenario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("capability_assertions.id"), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    support_score: Mapped[float] = mapped_column(Float, default=0)

class ClientSegment(str, __import__('enum').Enum):
    INDIVIDUAL='INDIVIDUAL'; FAMILY_OFFICE='FAMILY_OFFICE'; ASSET_MANAGER='ASSET_MANAGER'; PENSION_FUND='PENSION_FUND'; INSURER='INSURER'; BANK='BANK'; CORPORATION='CORPORATION'; GOVERNMENT='GOVERNMENT'; FOUNDATION='FOUNDATION'; HEALTHCARE='HEALTHCARE'; UNIVERSITY='UNIVERSITY'; FAMILY_BUSINESS='FAMILY_BUSINESS'; SME='SME'; COMMUNITY='COMMUNITY'; OTHER='OTHER'

class ClientIntelligenceProfile(Base):
    __tablename__='client_intelligence_profiles'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid)
    principal_id: Mapped[str]=mapped_column(String(100),unique=True,index=True,nullable=False)
    segment: Mapped[ClientSegment]=mapped_column(SAEnum(ClientSegment,name='client_segment'),nullable=False,default=ClientSegment.OTHER)
    organization_size: Mapped[str|None]=mapped_column(String(40)); strategic_objectives: Mapped[list]=mapped_column(JSON,default=list); constraints: Mapped[list]=mapped_column(JSON,default=list)
    decision_horizon: Mapped[str|None]=mapped_column(String(40)); readiness_level: Mapped[str|None]=mapped_column(String(40)); profile_confidence: Mapped[float]=mapped_column(Float,default=0)
    source: Mapped[str|None]=mapped_column(Text); desired_future: Mapped[str|None]=mapped_column(Text); future_horizon: Mapped[str|None]=mapped_column(String(40)); preferred_scenarios: Mapped[list]=mapped_column(JSON,default=list); readiness_barriers: Mapped[list]=mapped_column(JSON,default=list); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CINQuestion(Base):
    __tablename__='cin_questions'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid); question_key: Mapped[str]=mapped_column(String(160),unique=True,nullable=False); segment: Mapped[ClientSegment]=mapped_column(SAEnum(ClientSegment,name='client_segment'),nullable=False)
    text: Mapped[str]=mapped_column(Text,nullable=False); options: Mapped[list]=mapped_column(JSON,default=list); allow_free_text: Mapped[bool]=mapped_column(Boolean,default=True); status: Mapped[str]=mapped_column(String(20),default='ACTIVE'); priority: Mapped[int]=mapped_column(Integer,default=100); usage_count: Mapped[int]=mapped_column(Integer,default=0); created_from_pattern: Mapped[str|None]=mapped_column(String(255)); reviewed_by: Mapped[str|None]=mapped_column(String(100)); reviewed_at: Mapped[datetime|None]=mapped_column(DateTime); review_note: Mapped[str|None]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CINQuestionSession(Base):
    __tablename__='cin_question_sessions'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid); principal_id: Mapped[str]=mapped_column(String(100),nullable=False,index=True); segment: Mapped[ClientSegment]=mapped_column(SAEnum(ClientSegment,name='client_segment'),nullable=False); current_question_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('cin_questions.id',ondelete='SET NULL')); completed: Mapped[bool]=mapped_column(Boolean,default=False); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CINQuestionAnswer(Base):
    __tablename__='cin_question_answers'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid); session_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_question_sessions.id',ondelete='CASCADE'),nullable=False); question_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False); mode: Mapped[str]=mapped_column(String(20),nullable=False); selected_option: Mapped[str|None]=mapped_column(String(255)); free_text: Mapped[str|None]=mapped_column(Text); extracted_concepts: Mapped[list]=mapped_column(JSON,default=list); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class CINQuestionPattern(Base):
    __tablename__='cin_question_patterns'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid); concept_key: Mapped[str]=mapped_column(String(180),nullable=False); normalized_text: Mapped[str]=mapped_column(Text,nullable=False); segment: Mapped[ClientSegment]=mapped_column(SAEnum(ClientSegment,name='client_segment'),nullable=False); occurrence_count: Mapped[int]=mapped_column(Integer,default=1); candidate_question_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('cin_questions.id',ondelete='SET NULL')); validated: Mapped[bool]=mapped_column(Boolean,default=False); distinct_session_count: Mapped[int]=mapped_column(Integer,default=1); candidate_generated_at: Mapped[datetime|None]=mapped_column(DateTime); created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CINQuestionKnowledgeLink(Base):
    __tablename__='cin_question_knowledge_links'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid)
    question_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False,index=True)
    concept_key: Mapped[str]=mapped_column(String(180),nullable=False,index=True)
    concept_type: Mapped[str]=mapped_column(String(40),nullable=False,default='CONCEPT')
    entity_ref: Mapped[str|None]=mapped_column(String(255))
    evidence_state: Mapped[str]=mapped_column(String(30),nullable=False,default='UNKNOWN')
    relevance_score: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CINFutureIntelligenceSignal(Base):
    __tablename__='cin_future_intelligence_signals'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid)
    question_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False,index=True)
    profile_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('client_intelligence_profiles.id',ondelete='CASCADE'),nullable=False,index=True)
    session_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('cin_question_sessions.id',ondelete='CASCADE'),nullable=True,index=True)
    future_alignment: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    scenario_relevance: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    readiness_gap: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    opportunity_future_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    uncertainty_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    future_intelligence_value: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    reason_codes: Mapped[list]=mapped_column(JSON,nullable=False,default=list)
    context_refs: Mapped[dict]=mapped_column(JSON,nullable=False,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

class CINQuestionIntelligenceSignal(Base):
    __tablename__='cin_question_intelligence_signals'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid)
    question_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False,index=True)
    profile_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('client_intelligence_profiles.id',ondelete='CASCADE'),nullable=False,index=True)
    session_id: Mapped[uuid.UUID|None]=mapped_column(ForeignKey('cin_question_sessions.id',ondelete='CASCADE'),nullable=True,index=True)
    capability_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    evidence_gap_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    opportunity_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    need_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    risk_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    intelligence_value: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    reason_codes: Mapped[list]=mapped_column(JSON,nullable=False,default=list)
    context_refs: Mapped[dict]=mapped_column(JSON,nullable=False,default=dict)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)


class CINQuestionPrioritySignal(Base):
    __tablename__='cin_question_priority_signals'
    id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uid)
    question_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('cin_questions.id',ondelete='CASCADE'),nullable=False)
    profile_id: Mapped[uuid.UUID]=mapped_column(ForeignKey('client_intelligence_profiles.id',ondelete='CASCADE'),nullable=False)
    objective_match: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    constraint_match: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    pattern_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    evidence_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    novelty_signal: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    total_score: Mapped[float]=mapped_column(Float,nullable=False,default=0)
    reason_codes: Mapped[list]=mapped_column(JSON,nullable=False,default=list)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
