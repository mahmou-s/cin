from pathlib import Path
from uuid import uuid4
import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from ...auth import Principal, require_submitter
from ...db import get_db
from ...models import Evidence, Product, UserProfile
from ...config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router=APIRouter()
MAX_BYTES = 25 * 1024 * 1024
ALLOWED = {"application/pdf", "image/jpeg", "image/png", "text/plain", "text/csv"}

@router.post('/evidence/upload')
async def upload_evidence(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    product_id: str | None = Form(None),
    principal: Principal = Depends(require_submitter),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename: raise HTTPException(400,'EMPTY_FILENAME')
    if file.content_type and file.content_type not in ALLOWED:
        raise HTTPException(415, 'UNSUPPORTED_EVIDENCE_TYPE')
    root=Path(settings.evidence_dir); root.mkdir(parents=True,exist_ok=True)
    stored=f'{uuid4()}{Path(file.filename).suffix[:12]}'
    target=root/stored
    size=0; digest=hashlib.sha256()
    try:
        with target.open('wb') as out:
            while True:
                chunk=await file.read(1024*1024)
                if not chunk: break
                size += len(chunk)
                if size > MAX_BYTES:
                    target.unlink(missing_ok=True)
                    raise HTTPException(413,'EVIDENCE_TOO_LARGE')
                digest.update(chunk); out.write(chunk)
    except HTTPException: raise
    except Exception:
        target.unlink(missing_ok=True)
        raise HTTPException(500,'EVIDENCE_UPLOAD_FAILED')
    evidence = Evidence(
        title=title or file.filename,
        evidence_type='document',
        original_filename=file.filename,
        content_url=f'/evidence/{stored}',
        sha256=digest.hexdigest(),
        mime_type=file.content_type,
        size_bytes=size,
        validation_status='PENDING',
        independence_key='__unknown_source__',
    )
    if product_id:
        product = await db.scalar(
            select(Product).join(UserProfile, UserProfile.id == Product.profile_id)
            .where(Product.id == product_id, UserProfile.principal_id == principal.subject)
        )
        if product is None:
            target.unlink(missing_ok=True)
            raise HTTPException(404, 'PRODUCT_NOT_FOUND')
        product.evidences.append(evidence)
    db.add(evidence)
    await db.commit()
    return {'id': evidence.id, 'filename':file.filename,'stored_name':stored,'sha256':digest.hexdigest(),'size_bytes':size,'mime_type':file.content_type,'content_url':f'/evidence/{stored}','validation_status':evidence.validation_status}
