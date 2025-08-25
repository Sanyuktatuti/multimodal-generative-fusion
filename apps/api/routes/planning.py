
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
# Planner service not implemented yet - using fallback
PlannerOrchestrator = None
PlannerProviderError = Exception

router = APIRouter()

# Minimal fallback if no providers configured
def _naive_plan_from_prompt(prompt: str) -> dict:
    base = {
        "environment": {"theme": "alley", "weather": "light_rain", "time_of_day": "night"},
        "objects": [
            {"type": "alley_buildings", "instances": 2, "tags": ["wet_concrete"]},
            {"type": "neon_sign", "instances": 4, "tags": ["pink", "blue"], "text_overlays": ["ラーメン", "探偵社"]},
        ],
        "character": {"archetype": "sleuth", "rig": "humanoid", "motion_text": "walk cautiously"},
        "camera": {"path": "dolly", "duration_s": 8},
        "audio": {"tempo": 80, "mood": ["lofi", "minor"], "sfx": ["rain", "footsteps", "neon_buzz"]},
    }
    low = prompt.lower()
    if "day" in low:
        base["environment"]["time_of_day"] = "day"
    if "fog" in low:
        base["environment"]["weather"] = "fog"
    if "orbit" in low:
        base["camera"]["path"] = "orbit"
    return base

class PlanRequest(BaseModel):
    prompt: str
    seed: int = 42

@router.post("/v1/plan")
async def create_plan(req: PlanRequest):
    # Fallback to naive planner for now
    from shared.schemas.scene_plan import ScenePlan
    plan = ScenePlan(**_naive_plan_from_prompt(req.prompt))
    return {"scene_plan": json.loads(plan.json())}
