from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import Principal, require_submitter
from ...db import get_db
from ...models import (
    UserProfile, Product, ProductionCapacity, OwnershipDetail,
    Evidence, InvestmentSupportRequest, ProductEvidence, CapabilityAssertion, ProductCapabilityAssertion,
)
from ...schemas import (
    UserProfileCreate, UserProfileUpdate, UserProfileOut,
    ProductCreate, ProductUpdate, ProductOut,
    InvestmentSupportRequestCreate, InvestmentSupportRequestOut,
)

router = APIRouter()


def _product_loads():
    return (
        selectinload(Product.production_capacity),
        selectinload(Product.ownership),
        selectinload(Product.evidences),
        selectinload(Product.capability_assertions),
        selectinload(Product.investment_requests),
    )


def _product_out(product: Product) -> ProductOut:
    evidence_ids = [e.id for e in product.evidences]
    capability_assertion_ids = [a.id for a in product.capability_assertions]
    capacity = product.production_capacity
    if capacity is None:
        raise HTTPException(500, "PRODUCT_CAPACITY_MISSING")
    return ProductOut(
        id=product.id,
        profile_id=product.profile_id,
        name=product.name,
        category=product.category,
        activity_domain=product.activity_domain,
        description=product.description,
        features=product.features or [],
        additional_services=product.additional_services or [],
        media=product.media or [],
        documents=product.documents or [],
        evidence_ids=evidence_ids,
        capability_assertion_ids=capability_assertion_ids,
        production_capacity=capacity,
        goal=product.goal,
        support_types=product.support_types or [],
        ownership=product.ownership,
        verification_status=product.verification_status,
        ai_confidence_score=product.ai_confidence_score,
        ai_confidence_level=product.ai_confidence_level,
    )


def _profile_out(profile: UserProfile) -> UserProfileOut:
    return UserProfileOut(
        id=profile.id,
        principal_id=profile.principal_id,
        country_code=profile.country_code,
        governorate=profile.governorate,
        center=profile.center,
        village=profile.village,
        national_id=profile.national_id,
        display_name=profile.display_name,
        organization_name=profile.organization_name,
        commercial_register=profile.commercial_register,
        entity_type=profile.entity_type,
        activity_domains=profile.activity_domains or [],
        bio=profile.bio,
        verification_status=profile.verification_status,
        products=[_product_out(p) for p in profile.products],
        ai_confidence_score=profile.ai_confidence_score,
        ai_confidence_level=profile.ai_confidence_level,
    )


async def _owned_profile(db: AsyncSession, principal: Principal) -> UserProfile | None:
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.principal_id == principal.subject)
        .options(selectinload(UserProfile.products).options(*_product_loads()))
    )
    return result.scalar_one_or_none()


@router.get("/profiles/me", response_model=UserProfileOut)
async def get_my_profile(db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    profile = await _owned_profile(db, principal)
    if profile is None:
        raise HTTPException(404, "PROFILE_NOT_FOUND")
    return _profile_out(profile)


@router.post("/profiles/me", response_model=UserProfileOut, status_code=201)
async def create_my_profile(data: UserProfileCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    if data.principal_id != principal.subject:
        raise HTTPException(403, "PROFILE_PRINCIPAL_MISMATCH")
    existing = await _owned_profile(db, principal)
    if existing is not None:
        raise HTTPException(409, "PROFILE_ALREADY_EXISTS")
    profile = UserProfile(**data.model_dump())
    db.add(profile)
    await db.commit()
    profile = await _owned_profile(db, principal)
    return _profile_out(profile)


@router.patch("/profiles/me", response_model=UserProfileOut)
async def update_my_profile(data: UserProfileUpdate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    profile = await _owned_profile(db, principal)
    if profile is None:
        raise HTTPException(404, "PROFILE_NOT_FOUND")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    profile = await _owned_profile(db, principal)
    return _profile_out(profile)


@router.post("/profiles/me/products", response_model=ProductOut, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    profile = await _owned_profile(db, principal)
    if profile is None:
        raise HTTPException(404, "PROFILE_NOT_FOUND")
    product = Product(
        profile_id=profile.id,
        name=data.name,
        category=data.category,
        activity_domain=data.activity_domain,
        description=data.description,
        features=data.features,
        additional_services=data.additional_services,
        media=data.media,
        documents=data.documents,
        goal=data.goal,
        support_types=data.support_types,
    )
    product.production_capacity = ProductionCapacity(**data.production_capacity.model_dump())
    if data.ownership:
        product.ownership = OwnershipDetail(profile_id=profile.id, **data.ownership.model_dump())
    if data.evidence_ids:
        evidences = list((await db.scalars(select(Evidence).where(Evidence.id.in_(data.evidence_ids)))).all())
        if len(evidences) != len(set(data.evidence_ids)):
            raise HTTPException(422, "UNKNOWN_EVIDENCE_ID")
        product.evidences = evidences
    if data.capability_assertion_ids:
        assertions = list((await db.scalars(select(CapabilityAssertion).where(CapabilityAssertion.id.in_(data.capability_assertion_ids), CapabilityAssertion.status == "VERIFIED", CapabilityAssertion.submitted_by == principal.subject))).all())
        if len(assertions) != len(set(data.capability_assertion_ids)):
            raise HTTPException(422, "UNKNOWN_OR_UNVERIFIED_CAPABILITY_ASSERTION_ID")
        product.capability_assertions = assertions
    db.add(product)
    await db.commit()
    result = await db.execute(select(Product).where(Product.id == product.id).options(*_product_loads()))
    return _product_out(result.scalar_one())


@router.patch("/profiles/me/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    profile = await _owned_profile(db, principal)
    if profile is None:
        raise HTTPException(404, "PROFILE_NOT_FOUND")
    result = await db.execute(select(Product).where(Product.id == product_id, Product.profile_id == profile.id).options(*_product_loads()))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(404, "PRODUCT_NOT_FOUND")
    values = data.model_dump(exclude_unset=True, exclude={"production_capacity", "ownership", "evidence_ids", "capability_assertion_ids"})
    for key, value in values.items():
        setattr(product, key, value)
    if data.production_capacity is not None:
        if product.production_capacity is None:
            product.production_capacity = ProductionCapacity(**data.production_capacity.model_dump())
        else:
            for key, value in data.production_capacity.model_dump().items():
                setattr(product.production_capacity, key, value)
    if data.ownership is not None:
        if product.ownership is None:
            product.ownership = OwnershipDetail(profile_id=profile.id, **data.ownership.model_dump())
        else:
            for key, value in data.ownership.model_dump().items():
                setattr(product.ownership, key, value)
    if data.evidence_ids is not None:
        evidences = list((await db.scalars(select(Evidence).where(Evidence.id.in_(data.evidence_ids)))).all())
        if len(evidences) != len(set(data.evidence_ids)):
            raise HTTPException(422, "UNKNOWN_EVIDENCE_ID")
        product.evidences = evidences
    if data.capability_assertion_ids is not None:
        assertions = list((await db.scalars(select(CapabilityAssertion).where(CapabilityAssertion.id.in_(data.capability_assertion_ids), CapabilityAssertion.status == "VERIFIED", CapabilityAssertion.submitted_by == principal.subject))).all())
        if len(assertions) != len(set(data.capability_assertion_ids)):
            raise HTTPException(422, "UNKNOWN_OR_UNVERIFIED_CAPABILITY_ASSERTION_ID")
        product.capability_assertions = assertions
    await db.commit()
    result = await db.execute(select(Product).where(Product.id == product.id).options(*_product_loads()))
    return _product_out(result.scalar_one())


@router.post("/profiles/me/products/{product_id}/investment-requests", response_model=InvestmentSupportRequestOut, status_code=201)
async def create_investment_request(product_id: UUID, data: InvestmentSupportRequestCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    profile = await _owned_profile(db, principal)
    if profile is None:
        raise HTTPException(404, "PROFILE_NOT_FOUND")
    product = await db.scalar(select(Product).where(Product.id == product_id, Product.profile_id == profile.id))
    if product is None:
        raise HTTPException(404, "PRODUCT_NOT_FOUND")
    request = InvestmentSupportRequest(profile_id=profile.id, product_id=product.id, **data.model_dump())
    db.add(request)
    await db.commit()
    return request
