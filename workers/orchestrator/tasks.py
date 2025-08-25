from celery import Celery
import time
import os
import json
import asyncio
import redis
from dotenv import load_dotenv
from shared.schemas.scene_plan import ScenePlan
# Planner service not implemented yet - using fallback
PlannerOrchestrator = None
PlannerProviderError = Exception
# Lazy import to avoid circular dependencies
# from workers.env_gen.tasks import run_env

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", "0")
REDIS_BACKEND_DB = os.getenv("REDIS_BACKEND_DB", "1")
REDIS_STATUS_DB = int(os.getenv("REDIS_STATUS_DB", "0"))

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"
backend_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}"

app = Celery("orchestrator", broker=broker_url, backend=backend_url)
app.conf.task_default_queue = "orchestrator"


def _set_status(r: redis.Redis, job_id: str, status: str, detail: dict | None = None) -> None:
    payload = {"status": status}
    if detail:
        payload["detail"] = detail
    r.set(job_id, json.dumps(payload))


@app.task(queue="orchestrator")
def run_pipeline(job_id: str, prompt: str) -> None:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_STATUS_DB, decode_responses=True)
    _set_status(r, job_id, "planning")
    # Fallback to naive plan if no providers configured or provider failure
    def _naive_plan_from_prompt(text: str) -> dict:
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
        low = text.lower()
        if "day" in low:
            base["environment"]["time_of_day"] = "day"
        if "fog" in low:
            base["environment"]["weather"] = "fog"
        if "orbit" in low:
            base["camera"]["path"] = "orbit"
        return base

    try:
        plan = ScenePlan(**_naive_plan_from_prompt(prompt))
    except Exception as e:
        _set_status(r, job_id, "error", detail={"stage": "planning", "message": str(e)})
        return
    base_tmp_dir = os.getenv("JOB_TMP_DIR", "/app/tmp")
    try:
        os.makedirs(base_tmp_dir, exist_ok=True)
    except Exception:
        pass
    plan_path = f"{base_tmp_dir}/{job_id}_plan.json"
    with open(plan_path, "w") as f:
        f.write(plan.json())
    _set_status(r, job_id, "planned", detail={"plan_path": plan_path})
    _set_status(r, job_id, "env_gen", detail={"plan_path": plan_path})
    try:
        # Lazy import to avoid circular dependencies
        from workers.env_gen.tasks import run_env
        async_result = run_env.delay(job_id, plan_path, "stub", "0.1.0")
        # Do not block within task; env worker will update status to env_done
        _set_status(r, job_id, "env_queued", detail={"task_id": async_result.id})
    except Exception as e:
        _set_status(r, job_id, "error", detail={"stage": "env_gen", "message": str(e)})
        return
