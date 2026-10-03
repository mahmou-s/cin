from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...auth import Principal, require_authenticated, require_submitter
from ...db import get_db
from ...models import Product, ProductComponent, ProductComponentEvidence, ValueChainLink, ValueChainLinkEvidence, UserProfile, Evidence
from ...schemas import ProductComponentCreate, ProductComponentOut, ValueChainLinkCreate, ValueChainLinkOut, ValueChainOut

router = APIRouter()

async def _owned_product(db, product_id: UUID, principal: Principal):
    product = await db.scalar(select(Product).join(UserProfile, UserProfile.id == Product.profile_id).where(Product.id == product_id))
    if product is None:
        raise HTTPException(404, "PRODUCT_NOT_FOUND")
    profile = await db.scalar(select(UserProfile).where(UserProfile.id == product.profile_id))
    if profile.principal_id != principal.subject:
        raise HTTPException(403, "PRODUCT_NOT_OWNED")
    return product

async def _validate_evidence(db, evidence_ids):
    if not evidence_ids:
        return
    rows = list((await db.scalars(select(Evidence).where(Evidence.id.in_(evidence_ids)))).all())
    if len(rows) != len(set(evidence_ids)):
        raise HTTPException(422, "UNKNOWN_EVIDENCE_ID")

@router.get("/value-chain/products/{product_id}", response_model=ValueChainOut)
async def get_value_chain(product_id: UUID, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    product = await db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(404, "PRODUCT_NOT_FOUND")
    components = (await db.scalars(select(ProductComponent).where(ProductComponent.product_id == product_id).order_by(ProductComponent.created_at))).all()
    links = (await db.scalars(select(ValueChainLink).where(ValueChainLink.product_id == product_id).order_by(ValueChainLink.sequence_order, ValueChainLink.created_at))).all()
    return ValueChainOut(product_id=product_id, components=[ProductComponentOut.model_validate(x) for x in components], links=[ValueChainLinkOut.model_validate(x) for x in links])

@router.post("/value-chain/products/{product_id}/components", response_model=ProductComponentOut)
async def add_component(product_id: UUID, data: ProductComponentCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    await _owned_product(db, product_id, principal)
    component = await db.scalar(select(Product).where(Product.id == data.component_product_id))
    if component is None:
        raise HTTPException(404, "COMPONENT_PRODUCT_NOT_FOUND")
    if component.id == product_id:
        raise HTTPException(422, "PRODUCT_CANNOT_COMPONENT_ITSELF")
    await _validate_evidence(db, data.evidence_ids)
    item = ProductComponent(product_id=product_id, **data.model_dump(exclude={"evidence_ids"}))
    db.add(item)
    await db.flush()
    if data.evidence_ids:
        db.add_all([ProductComponentEvidence(component_id=item.id, evidence_id=eid) for eid in data.evidence_ids])
    await db.commit(); await db.refresh(item)
    return ProductComponentOut.model_validate(item)

@router.post("/value-chain/products/{product_id}/links", response_model=ValueChainLinkOut)
async def add_value_chain_link(product_id: UUID, data: ValueChainLinkCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    await _owned_product(db, product_id, principal)
    for pid in (data.from_profile_id, data.to_profile_id):
        if await db.scalar(select(UserProfile.id).where(UserProfile.id == pid)) is None:
            raise HTTPException(404, "PROFILE_NOT_FOUND")
    for pid in (data.from_product_id, data.to_product_id):
        if pid is not None and await db.scalar(select(Product.id).where(Product.id == pid)) is None:
            raise HTTPException(404, "CHAIN_PRODUCT_NOT_FOUND")
    if data.from_product_id is not None:
        from_product = await db.scalar(select(Product).where(Product.id == data.from_product_id))
        if from_product.profile_id != data.from_profile_id:
            raise HTTPException(422, "FROM_PRODUCT_PROFILE_MISMATCH")
    if data.to_product_id is not None:
        to_product = await db.scalar(select(Product).where(Product.id == data.to_product_id))
        if to_product.profile_id != data.to_profile_id:
            raise HTTPException(422, "TO_PRODUCT_PROFILE_MISMATCH")
    await _validate_evidence(db, data.evidence_ids)
    item = ValueChainLink(product_id=product_id, **data.model_dump(exclude={"evidence_ids"}))
    db.add(item)
    await db.flush()
    if data.evidence_ids:
        db.add_all([ValueChainLinkEvidence(link_id=item.id, evidence_id=eid) for eid in data.evidence_ids])
    await db.commit(); await db.refresh(item)
    return ValueChainLinkOut.model_validate(item)
