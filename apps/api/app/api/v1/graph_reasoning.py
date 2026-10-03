from fastapi import APIRouter, Depends
from ...auth import Principal, require_steward
from ...services.graph_reasoning import project_capability_relations

router = APIRouter()

@router.post('/graph/reasoning/project')
async def project(principal: Principal = Depends(require_steward)):
    count = await project_capability_relations()
    return {'projected_relations': count}
