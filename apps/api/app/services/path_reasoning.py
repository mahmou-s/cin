from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import CapabilityAssertion, CapabilityType, Community, ReasoningRun
from .chain_definitions import PATH_TRANSITIONS, PATH_LABELS, aggregate_support


async def verified_capabilities(db: AsyncSession):
    rows = await db.execute(
        select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.status == "VERIFIED")
    )
    return rows.all()


def _find_paths(records, max_hops=4):
    by_code = {}
    for assertion, cap, community in records:
        by_code.setdefault(cap.code, []).append((assertion, cap, community))
    paths = []
    for start in sorted(by_code):
        def walk(code, chain):
            if len(chain) >= 3:
                codes = tuple(x[1].code for x in chain)
                if codes in PATH_LABELS:
                    paths.append(chain[:])
            if len(chain) >= max_hops:
                return
            for nxt in sorted(PATH_TRANSITIONS.get(code, set())):
                for rec in by_code.get(nxt, []):
                    if rec[0].id in {x[0].id for x in chain}:
                        continue
                    walk(nxt, chain + [rec])
        for rec in by_code[start]:
            walk(start, [rec])
    unique = {}
    for chain in paths:
        unique[tuple(str(x[0].id) for x in chain)] = chain
    return list(unique.values())


def _support(chain):
    return aggregate_support([x[0].confidence_score for x in chain])


def _score(chain):
    """Single scalar used for ranking scenario candidate paths."""
    return float(aggregate_support([x[0].confidence_score for x in chain])["weakest_link"])


async def discover_paths(db: AsyncSession, limit=50):
    records = await verified_capabilities(db)
    paths = _find_paths(records)
    output = []
    for chain in paths[:limit]:
        codes = tuple(x[1].code for x in chain)
        support = _support(chain)
        output.append({
            "path": PATH_LABELS[codes],
            "capability_codes": list(codes),
            "assertions": [str(x[0].id) for x in chain],
            "communities": [{"id": str(x[2].id), "name": x[2].name} for x in chain],
            "support_score": support["weakest_link"],
            "support_weakest_link": support["weakest_link"],
            "support_average": support["average"],
            "interpretation": "مسار تكاملي محتمل مبني على قدرات موثقة؛ لا يمثل ترتيبًا أو حكمًا على المجتمعات.",
        })
    return output


async def analyze_path(db: AsyncSession, assertion_ids: list[UUID], actor="system"):
    records = await db.execute(
        select(CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(CapabilityAssertion.id.in_(assertion_ids), CapabilityAssertion.status == "VERIFIED")
    )
    rows = records.all()
    by_id = {r[0].id: r for r in rows}
    if len(by_id) != len(assertion_ids):
        raise ValueError("ALL_ASSERTIONS_MUST_BE_VERIFIED")
    chain = [by_id[x] for x in assertion_ids]
    codes = tuple(x[1].code for x in chain)
    valid = all(codes[i + 1] in PATH_TRANSITIONS.get(codes[i], set()) for i in range(len(codes) - 1))
    if not valid:
        raise ValueError("INVALID_CAPABILITY_PATH")
    support = _support(chain)
    result = {
        "path": PATH_LABELS.get(codes, " → ".join(codes)),
        "capability_codes": list(codes),
        "assertions": [str(x[0].id) for x in chain],
        "communities": [{"id": str(x[2].id), "name": x[2].name} for x in chain],
        "support_score": support["weakest_link"],
        "support_weakest_link": support["weakest_link"],
        "support_average": support["average"],
        "logic": [f"{codes[i]} enables or complements {codes[i+1]}" for i in range(len(codes)-1)],
        "limitations": [
            "المسار استدلال تحليلي وليس إثباتًا لجدوى مشروع.",
            "لا يمثل ترتيبًا أو تقييمًا للمجتمعات.",
            "التحليل يعتمد على القدرات الموثقة المتاحة فقط.",
        ],
    }
    return result
