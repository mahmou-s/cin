from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Scenario, ScenarioStep, CapabilityAssertion, CapabilityType, Community
from .path_reasoning import PATH_TRANSITIONS, _score

GOAL_HINTS = {
    "production": {"C01"}, "manufacturing": {"C01"}, "industry": {"C01"},
    "technology": {"C06"}, "innovation": {"C07"}, "export": {"C03"},
    "market": {"C02"}, "knowledge": {"C05"}, "education": {"C05", "C04"},
    "human": {"C04"}, "cooperation": {"C09"}, "institution": {"C08"},
    "connectivity": {"C10"}, "external": {"C10"},
    "إنتاج": {"C01"}, "تصنيع": {"C01"}, "صناعة": {"C01"}, "تكنولوجيا": {"C06"},
    "ابتكار": {"C07"}, "تصدير": {"C03"}, "سوق": {"C02"}, "معرفة": {"C05"},
    "تعليم": {"C05", "C04"}, "موارد بشرية": {"C04"}, "تعاون": {"C09"},
    "مؤسسات": {"C08"}, "اتصال": {"C10"}, "خارجي": {"C10"},
}

async def _verified(db):
    rows = await db.execute(select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.status == "VERIFIED"))
    return rows.all()

def _goal_codes(goal: str):
    text = goal.lower()
    codes = set()
    for hint, values in GOAL_HINTS.items():
        if hint.lower() in text:
            codes.update(values)
    return codes

def _candidate_paths(records, starts, max_hops=5):
    by_code = {}
    for a,t,c in records: by_code.setdefault(t.code, []).append((a,t,c))
    found=[]
    def walk(code, chain, used):
        if len(chain) >= 2 and (not starts or any(x[1].code in starts for x in chain)):
            found.append(chain[:])
        if len(chain) >= max_hops: return
        for nxt in sorted(PATH_TRANSITIONS.get(code, set())):
            for rec in by_code.get(nxt, []):
                if rec[0].id in used: continue
                walk(nxt, chain+[rec], used|{rec[0].id})
    for code in sorted(by_code):
        for rec in by_code[code]: walk(code,[rec],{rec[0].id})
    unique={}
    for chain in found:
        key=tuple(str(x[0].id) for x in chain)
        unique[key]=chain
    return sorted(unique.values(), key=lambda c: (_score(c), len(c)), reverse=True)

async def generate_scenario(db: AsyncSession, goal: str, requested_codes=None, limit=5):
    requested_codes = requested_codes or []
    records = await _verified(db)
    if not records: raise ValueError("NO_VERIFIED_CAPABILITIES")
    starts=set(requested_codes) | _goal_codes(goal)
    paths=_candidate_paths(records, starts, 5)
    if not paths: raise ValueError("NO_SUPPORTED_SCENARIO_PATH")
    selected=paths[:limit]
    scenarios=[]
    for chain in selected:
        codes=[x[1].code for x in chain]
        score=_score(chain)
        assumptions=[
            "القدرات المستخدمة موثقة بحالة VERIFIED.",
            "وجود القدرات لا يثبت نجاح مشروع أو جدوى اقتصادية.",
            "العلاقات بين القدرات تمثل مسارًا تحليليًا محتملًا وليست قرارًا آليًا.",
        ]
        if len({x[2].id for x in chain}) > 1:
            assumptions.append("المسار يفترض إمكانية التنسيق بين أكثر من مجتمع؛ لم يتم إثبات رغبة الشراكة.")
        scenario=Scenario(goal=goal, requested_codes=list(requested_codes), assumptions=assumptions,
                          result={"capability_codes":codes,"support_score":score,"community_count":len({str(x[2].id) for x in chain})})
        db.add(scenario); await db.flush()
        for i,x in enumerate(chain,1):
            rationale=(f"{x[1].code} — {x[1].name} يساهم في المسار عند الخطوة {i}؛ "
                       + ("قدرة البداية/الهدف المباشر." if i==1 else f"يرتبط بالخطوة السابقة عبر علاقة تكامل تحليلية."))
            db.add(ScenarioStep(scenario_id=scenario.id,step_order=i,assertion_id=x[0].id,rationale=rationale,support_score=x[0].confidence_score))
        await db.flush()
        scenarios.append((scenario,chain))
    await db.commit()
    return scenarios

async def serialize_scenario(db, scenario_id):
    s=await db.get(Scenario, scenario_id)
    if not s: raise ValueError("SCENARIO_NOT_FOUND")
    rows=await db.execute(select(ScenarioStep,CapabilityAssertion,CapabilityType,Community)
      .join(CapabilityAssertion,CapabilityAssertion.id==ScenarioStep.assertion_id)
      .join(CapabilityType,CapabilityType.id==CapabilityAssertion.capability_type_id)
      .join(Community,Community.id==CapabilityAssertion.community_id)
      .where(ScenarioStep.scenario_id==scenario_id).order_by(ScenarioStep.step_order))
    steps=[]
    for st,a,t,c in rows.all():
        steps.append({"order":st.step_order,"assertion_id":str(a.id),"code":t.code,"capability":t.name,"community_id":str(c.id),"community":c.name,"confidence":a.confidence_score,"rationale":st.rationale})
    return {"id":str(s.id),"goal":s.goal,"requested_codes":s.requested_codes,"status":s.status,"assumptions":s.assumptions,"result":s.result,"steps":steps,"created_at":s.created_at.isoformat()}
