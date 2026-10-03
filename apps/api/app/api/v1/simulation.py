from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from ...db import get_db
from ...services.simulation import compare_scenarios, load_scenario, simulate_chain
from ...auth import Principal, require_authenticated

router = APIRouter()

class CompareRequest(BaseModel):
    scenario_ids: list[UUID] = Field(min_length=2, max_length=10)
    assumptions_by_scenario: dict[str, dict[str, float]] = Field(default_factory=dict)

    @field_validator("assumptions_by_scenario")
    @classmethod
    def validate_factors(cls, value):
        for sid, factors in value.items():
            for code, factor in factors.items():
                if not (0.0 <= factor <= 1.0):
                    raise ValueError(f"availability factor for {code} must be between 0 and 1")
        return value

class SimulateRequest(BaseModel):
    assumptions: dict[str, float] = Field(default_factory=dict)

@router.post("/scenarios/compare")
async def compare(payload: CompareRequest, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    try:
        return {"count": len(payload.scenario_ids), "items": await compare_scenarios(db, payload.scenario_ids, payload.assumptions_by_scenario)}
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/scenarios/{scenario_id}/simulate")
async def simulate(scenario_id: UUID, payload: SimulateRequest, db: AsyncSession = Depends(get_db), principal: Principal = Depends(require_authenticated)):
    try:
        scenario, rows = await load_scenario(db, scenario_id)
        result = simulate_chain(rows, payload.assumptions)
        return {
            "scenario_id": str(scenario.id),
            "goal": scenario.goal,
            "assumptions": payload.assumptions,
            "result": result,
            "interpretation": "تحليل حساسية للفرضيات؛ لا يمثل توقعًا لنتيجة مستقبلية ولا يثبت الجدوى الاقتصادية.",
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
