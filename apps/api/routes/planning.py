
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from apps.api.services.planner_client import PlannerOrchestrator, PlannerProviderError

router = APIRouter()
planner = PlannerOrchestrator()

class PlanRequest(BaseModel):
    prompt: str
    seed: int = 42

@router.post("/v1/plan")
async def create_plan(req: PlanRequest):
    try:
        scene_plan = await planner.plan(req.prompt)
        return {"scene_plan": json.loads(scene_plan.model_dump_json())}
    except PlannerProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
