from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import Principal, require_authenticated, require_submitter
from ...db import get_db
from ...models import (
    Product, ProductLogisticsProfile, LogisticsRoute, LogisticsRouteEvidence, Evidence,
)
from ...schemas import LogisticsProfileCreate, LogisticsProfileOut, LogisticsRouteCreate, LogisticsRouteOut

router = APIRouter()


def _profile_out(item: ProductLogisticsProfile) -> LogisticsProfileOut:
    return LogisticsProfileOut.model_validate(item)


@router.get("/logistics/products/{product_id}", response_model=LogisticsProfileOut | None)
async def get_product_logistics(product_id: UUID, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    item = await db.scalar(select(ProductLogisticsProfile).where(ProductLogisticsProfile.product_id == product_id))
    if item is None:
        return None
    return _profile_out(item)


@router.post("/logistics/products/{product_id}", response_model=LogisticsProfileOut)
async def upsert_product_logistics(product_id: UUID, data: LogisticsProfileCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    product = await db.scalar(
        select(Product).where(Product.id == product_id).options(selectinload(Product.profile))
    )
    if product is None:
        raise HTTPException(404, "PRODUCT_NOT_FOUND")
    if product.profile.principal_id != principal.subject:
        raise HTTPException(403, "PRODUCT_NOT_OWNED")

    item = await db.scalar(select(ProductLogisticsProfile).where(ProductLogisticsProfile.product_id == product_id))
    values = data.model_dump()
    if item is None:
        item = ProductLogisticsProfile(product_id=product_id, **values)
        db.add(item)
    else:
        for key, value in values.items():
            setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return _profile_out(item)


@router.get("/logistics/routes", response_model=list[LogisticsRouteOut])
async def list_logistics_routes(
    origin: str | None = Query(None, max_length=255),
    destination: str | None = Query(None, max_length=255),
    mode: str | None = Query(None, max_length=40),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(require_authenticated),
):
    stmt = select(LogisticsRoute).where(LogisticsRoute.verification_status == "VERIFIED").order_by(LogisticsRoute.created_at.desc()).limit(limit)
    if origin:
        stmt = stmt.where(LogisticsRoute.origin.ilike(f"%{origin}%"))
    if destination:
        stmt = stmt.where(LogisticsRoute.destination.ilike(f"%{destination}%"))
    if mode:
        stmt = stmt.where(LogisticsRoute.mode == mode)
    return [LogisticsRouteOut.model_validate(x) for x in (await db.scalars(stmt)).all()]


@router.post("/logistics/routes", response_model=LogisticsRouteOut)
async def create_logistics_route(data: LogisticsRouteCreate, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_submitter)):
    route = LogisticsRoute(**data.model_dump(exclude={"evidence_ids"}))
    if data.evidence_ids:
        evidences = list((await db.scalars(select(Evidence).where(Evidence.id.in_(data.evidence_ids)))).all())
        if len(evidences) != len(set(data.evidence_ids)):
            raise HTTPException(422, "UNKNOWN_EVIDENCE_ID")
        db.add(route)
        await db.flush()
        db.add_all([LogisticsRouteEvidence(route_id=route.id, evidence_id=e.id) for e in evidences])
    else:
        db.add(route)
    await db.commit()
    await db.refresh(route)
    return LogisticsRouteOut.model_validate(route)
