from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...models import Community, CapabilityType, CapabilityAssertion

router = APIRouter()

RELATIONS = {
    ('C01','C06'): ('ENABLES', 'الإنتاج يمكن أن يستفيد من التكنولوجيا لتحسين الكفاءة أو الجودة.'),
    ('C06','C07'): ('ENABLES', 'التكنولوجيا يمكن أن تفتح مجالًا للتطبيق والابتكار.'),
    ('C07','C03'): ('ENABLES', 'الابتكار قد يدعم تطوير منتجات أو عمليات قابلة للتصدير.'),
    ('C01','C02'): ('COMPLEMENTS', 'القدرة الإنتاجية تتكامل مع القدرة الاقتصادية والسوقية.'),
    ('C02','C03'): ('ENABLES', 'المعرفة بالسوق قد تدعم الوصول إلى أسواق التصدير.'),
    ('C03','C10'): ('ENABLES', 'التصدير يرتبط بالاتصال الخارجي والأسواق والشبكات.'),
    ('C05','C07'): ('ENABLES', 'المعرفة يمكن أن تدعم البحث والتطوير والابتكار.'),
    ('C04','C05'): ('ENABLES', 'رأس المال البشري يمكن أن يدعم إنتاج المعرفة وتطبيقها.'),
    ('C08','C09'): ('ENABLES', 'المؤسسات الفعالة يمكن أن تسهل آليات التعاون.'),
    ('C09','C10'): ('ENABLES', 'التعاون يمكن أن يتحول إلى اتصال خارجي مستمر.'),
}

@router.get('/relations/communities')
async def community_relations(
    community_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Find potential complementarity between communities using VERIFIED capabilities only.
    This is an analytical relation map, not a ranking or a recommendation engine.
    """
    stmt = (
        select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.status == 'VERIFIED')
    )
    if community_id:
        stmt = stmt.where(CapabilityAssertion.community_id == community_id)
    rows = (await db.execute(stmt)).all()

    by_code = {}
    for assertion, cap, community in rows:
        by_code.setdefault(cap.code, []).append((assertion, cap, community))

    relations = []
    for (source_code, target_code), (relation_type, rationale) in RELATIONS.items():
        for a, source_cap, source_community in by_code.get(source_code, []):
            for b, target_cap, target_community in by_code.get(target_code, []):
                if source_community.id == target_community.id:
                    continue
                relations.append({
                    'source_community': {'id': str(source_community.id), 'name': source_community.name},
                    'target_community': {'id': str(target_community.id), 'name': target_community.name},
                    'source_capability': {'code': source_cap.code, 'name': source_cap.name},
                    'target_capability': {'code': target_cap.code, 'name': target_cap.name},
                    'relation_type': relation_type,
                    'rationale': rationale,
                    'support': {
                        'source_confidence': a.confidence_score,
                        'target_confidence': b.confidence_score,
                    },
                    'principle': 'هذه علاقة تكاملية محتملة مبنية على قدرات موثقة، وليست ترتيبًا للمجتمعات ولا إثباتًا لجدوى الشراكة.'
                })
                if len(relations) >= limit:
                    return {'items': relations, 'count': len(relations), 'relation_model': 'capability_complementarity'}
    return {'items': relations, 'count': len(relations), 'relation_model': 'capability_complementarity'}
