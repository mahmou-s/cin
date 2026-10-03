from sqlalchemy import select
from .db import SessionLocal
from .models import CapabilityType

CAPS=[
("C01","Production Capability"),("C02","Economic & Market Capability"),("C03","Export Capability"),("C04","Human Capital Capability"),("C05","Knowledge Capability"),("C06","Technology Capability"),("C07","Innovation Capability"),("C08","Institutional Capability"),("C09","Cooperation Capability"),("C10","External Connectivity Capability"),("C11","Logistics Capability")]
async def seed_capabilities():
    async with SessionLocal() as db:
        for code,name in CAPS:
            if not await db.scalar(select(CapabilityType).where(CapabilityType.code==code)):
                db.add(CapabilityType(code=code,domain=name,name=name))
        await db.commit()
