
from celery import Celery
import json
import redis
from shared.providers.factory import get_provider

app = Celery("env_gen", broker="redis://redis:6379/0", backend="redis://redis:6379/1")
app.conf.task_default_queue = "env"


def set_status(job_id, status, detail=None):
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    payload = {"status": status}
    if detail:
        payload["detail"] = detail
    r.set(job_id, json.dumps(payload))


@app.task(queue="env")
def run_env(job_id, plan_path, provider_name="sdxl_triposr", version="0.1.0"):
    from shared.schemas.scene_plan import ScenePlan
    with open(plan_path) as f:
        raw = json.load(f)
    plan = ScenePlan(**raw)

    provider = get_provider("env", provider_name, version)
    result = provider.generate(plan.model_dump())

    out_path = result["artifacts"]["scene_glb"]
    prov = result["provenance"]

    set_status(job_id, "env_done", {"scene_glb": out_path, "prov": prov})
    return out_path
