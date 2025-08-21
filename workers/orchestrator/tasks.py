from celery import Celery
import time
import os
import json
import redis
from dotenv import load_dotenv
from shared.schemas.scene_plan import ScenePlan
try:
    # Reuse the naive planner for Sprint 1
    from apps.api.routes.planning import naive_plan_from_prompt
except Exception:  # pragma: no cover - fallback in case of import context
    def naive_plan_from_prompt(prompt: str) -> dict:
        return {
            "environment": {"theme": "alley","weather":"light_rain","time_of_day":"night"},
            "objects": [],
            "character": {"archetype":"generic","rig":"humanoid","motion_text":"walk"},
            "camera": {"path":"dolly","duration_s":8},
            "audio": {"tempo":80,"mood":["lofi","minor"],"sfx":["ambience"]}
        }

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", "0")
REDIS_BACKEND_DB = os.getenv("REDIS_BACKEND_DB", "1")
REDIS_STATUS_DB = int(os.getenv("REDIS_STATUS_DB", "0"))

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"
backend_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}"

app = Celery("orchestrator", broker=broker_url, backend=backend_url)


def _set_status(r: redis.Redis, job_id: str, status: str, detail: dict | None = None) -> None:
    payload = {"status": status}
    if detail:
        payload["detail"] = detail
    r.set(job_id, json.dumps(payload))


@app.task
def run_pipeline(job_id: str, prompt: str) -> None:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_STATUS_DB, decode_responses=True)
    _set_status(r, job_id, "planning")
    plan_raw = naive_plan_from_prompt(prompt)
    plan = ScenePlan(**plan_raw)
    plan_path = f"/tmp/{job_id}_plan.json"
    with open(plan_path, "w") as f:
        f.write(plan.model_dump_json())
    _set_status(r, job_id, "planned", detail={"plan_path": plan_path})
    # Next sprint: call env generator here; for Sprint 1, mark done
    _set_status(r, job_id, "done")
