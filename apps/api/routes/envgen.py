from fastapi import APIRouter
from pydantic import BaseModel
import os
from workers.env_gen.tasks import run_env_cloud, app as env_app


router = APIRouter(prefix="/v1/generations", tags=["envgen"])

S3_BUCKET = os.getenv("S3_BUCKET", "s3://multimodal-fusion-models-sanyuktatuti").replace("s3://", "").split("/", 1)[0]


class GenReq(BaseModel):
    prompt: str


@router.post("")
def submit(req: GenReq):
    r = run_env_cloud.delay(req.prompt)
    return {"task_id": r.id}


@router.get("/{task_id}/status")
def status(task_id: str):
    from celery.result import AsyncResult
    ar = env_app.AsyncResult(task_id)
    # In containers we may have a disabled result backend; only return state
    resp = {"state": ar.state}
    try:
        res = ar.result
        if isinstance(res, dict):
            resp.update(res)
    except Exception:
        pass
    return resp


@router.get("/{job_id}/presigned")
def presign(job_id: str):
    import boto3
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
    key_m = f"jobs/{job_id}/manifest.json"
    key_g = f"jobs/{job_id}/scene.glb"
    return {
        "manifest_url": s3.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key_m}, ExpiresIn=3600
        ),
        "scene_url": s3.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key_g}, ExpiresIn=3600
        ),
    }


