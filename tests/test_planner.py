
from shared.schemas.scene_plan import ScenePlan
from apps.api.routes.planning import naive_plan_from_prompt

def test_naive_plan_valid():
    raw = naive_plan_from_prompt("misty cyberpunk alley at night, light rain, dolly camera")
    plan = ScenePlan(**raw)
    assert plan.environment.time_of_day in ("day","golden_hour","night")
    assert 2 <= plan.camera.duration_s <= 30
