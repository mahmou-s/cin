from statistics import geometric_mean
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Scenario, ScenarioStep, CapabilityAssertion, CapabilityType, Community

DEFAULT_ASSUMPTIONS = {
    "C01": 1.0, "C02": 1.0, "C03": 1.0, "C04": 1.0, "C05": 1.0,
    "C06": 1.0, "C07": 1.0, "C08": 1.0, "C09": 1.0, "C10": 1.0,
}

async def load_scenario(db: AsyncSession, scenario_id):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise ValueError("SCENARIO_NOT_FOUND")
    rows = await db.execute(
        select(ScenarioStep, CapabilityAssertion, CapabilityType, Community)
        .join(CapabilityAssertion, CapabilityAssertion.id == ScenarioStep.assertion_id)
        .join(CapabilityType, CapabilityType.id == CapabilityAssertion.capability_type_id)
        .join(Community, Community.id == CapabilityAssertion.community_id)
        .where(ScenarioStep.scenario_id == scenario_id)
        .order_by(ScenarioStep.step_order)
    )
    return scenario, rows.all()

def simulate_chain(rows, assumptions=None):
    assumptions = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    steps = []
    factors = []
    for st, assertion, ctype, community in rows:
        availability = max(0.0, min(1.0, float(assumptions.get(ctype.code, 1.0))))
        base = max(0.0, min(1.0, float(assertion.confidence_score)))
        effective = base * availability
        factors.append(max(effective, 0.000001))
        steps.append({
            "order": st.step_order,
            "code": ctype.code,
            "capability": ctype.name,
            "community_id": str(community.id),
            "community": community.name,
            "base_confidence": round(base, 4),
            "availability_factor": round(availability, 4),
            "effective_support": round(effective, 4),
            "rationale": st.rationale,
        })
    score = geometric_mean(factors) if factors else 0.0
    return {"support_score": round(score, 4), "steps": steps}

async def compare_scenarios(db: AsyncSession, scenario_ids, assumptions_by_scenario=None):
    assumptions_by_scenario = assumptions_by_scenario or {}
    results = []
    for sid in scenario_ids:
        scenario, rows = await load_scenario(db, sid)
        sim = simulate_chain(rows, assumptions_by_scenario.get(str(sid), {}))
        results.append({
            "scenario_id": str(scenario.id),
            "goal": scenario.goal,
            **sim,
        })
    return sorted(results, key=lambda x: x["support_score"], reverse=True)
