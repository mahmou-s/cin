from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import CapabilityAssertion, CapabilityType, Community, Opportunity, OpportunityAssertion, ReasoningRun

PATTERN_TEXT = {
    frozenset({'C01','C03'}): 'قدرة الإنتاج قد تتكامل مع قدرة التصدير لبناء مسار محتمل للوصول إلى الأسواق.',
    frozenset({'C01','C06'}): 'قدرة الإنتاج قد تتكامل مع التكنولوجيا لتحسين العملية أو نقل تقنية.',
    frozenset({'C01','C02'}): 'قدرة الإنتاج قد تتكامل مع السوق لبناء مسار محتمل من الإنتاج إلى السوق.',
    frozenset({'C04','C05'}): 'رأس المال البشري والمعرفة قد يدعمان تدريبًا أو نقل معرفة متبادلًا.',
    frozenset({'C05','C07'}): 'المعرفة والابتكار قد يتكاملان في مسار بحث وتطوير محتمل.',
    frozenset({'C06','C07'}): 'التكنولوجيا والابتكار قد يتكاملان في تطوير حل أو منتج جديد.',
    frozenset({'C08','C09'}): 'القدرة المؤسسية والتعاون قد يدعمان تنسيقًا مؤسسيًا مشتركًا.',
    frozenset({'C09','C10'}): 'التعاون والاتصال الخارجي قد يدعمان ربطًا عابرًا للمجتمعات.',
}

def _bounded(x: float) -> float:
    return max(0.0, min(1.0, round(x, 4)))

async def analyze_opportunity(db: AsyncSession, opportunity_id: UUID, actor: str = 'system'):
    opp = await db.get(Opportunity, opportunity_id)
    if not opp:
        raise ValueError('OPPORTUNITY_NOT_FOUND')
    rows = await db.execute(
        select(CapabilityAssertion, CapabilityType, Community)
        .join(OpportunityAssertion, OpportunityAssertion.assertion_id == CapabilityAssertion.id)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(OpportunityAssertion.opportunity_id == opportunity_id)
    )
    records = rows.all()
    if len(records) < 2:
        raise ValueError('INSUFFICIENT_ASSERTIONS')

    a1,t1,c1 = records[0]
    a2,t2,c2 = records[1]
    pattern = PATTERN_TEXT.get(frozenset({t1.code,t2.code}), 'لم يتم تعريف نمط تكامل مسبق لهذه المجموعة.')
    confidence = _bounded((a1.confidence_score + a2.confidence_score) / 2)
    same_country = c1.country_code == c2.country_code
    same_location = bool(c1.location and c2.location and c1.location.strip().lower() == c2.location.strip().lower())
    maturity_bonus = 0.05 if a1.maturity_level in {'ESTABLISHED','ADVANCED','SPECIALIZED'} and a2.maturity_level in {'ESTABLISHED','ADVANCED','SPECIALIZED'} else 0.0
    context_bonus = 0.05 if same_location else (0.02 if same_country else 0.0)
    reasoning_confidence = _bounded(confidence + maturity_bonus + context_bonus)

    finding = {
        'hypothesis': pattern,
        'evidence_assertions': [str(a1.id), str(a2.id)],
        'capabilities': [t1.code, t2.code],
        'communities': [str(c1.id), str(c2.id)],
        'confidence': reasoning_confidence,
        'factors': {
            'verified_capability_support': confidence,
            'maturity_context_bonus': maturity_bonus,
            'geographic_context_bonus': context_bonus,
            'same_country': same_country,
            'same_location': same_location,
        },
        'limitations': [
            'النتيجة فرضية تحليلية وليست إثباتًا لجدوى المشروع.',
            'لا يوجد حكم على قيمة أي مجتمع أو ترتيبه.',
            'لم يتم استخدام بيانات سرية أو استنتاجات غير موثقة.',
        ],
    }
    run = ReasoningRun(opportunity_id=opp.id, engine='CIN-Explainable-Reasoner-v0.6', status='COMPLETED', actor=actor, result=finding)
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run
