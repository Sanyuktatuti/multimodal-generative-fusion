from fastapi import APIRouter
from pydantic import BaseModel
import os
import uuid
from workers.env_gen.tasks import run_env_cloud, app as env_app


router = APIRouter(prefix="/v1/generations", tags=["envgen"])

S3_BUCKET = os.getenv("S3_BUCKET", "s3://multimodal-fusion-models-sanyuktatuti").replace("s3://", "").split("/", 1)[0]


class GenReq(BaseModel):
    prompt: str


@router.post("")
def submit(req: GenReq):
    job_id = f"envgen-{uuid.uuid4().hex[:8]}"
    r = run_env_cloud.delay(req.prompt, job_id)
    return {"task_id": r.id, "job_id": job_id}


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
    # Try multiple possible S3 key patterns
    patterns = [
        f"jobs/{job_id}/",  # Standard path
        f"jobs/jobs/{job_id}/",  # Double jobs prefix
        f"{job_id}/",  # Direct job_id path (current)
    ]
    
    key_m = key_g = None
    for pattern in patterns:
        try:
            test_m = f"{pattern}manifest.json"
            test_g = f"{pattern}scene.glb"
            s3.head_object(Bucket=S3_BUCKET, Key=test_m)
            s3.head_object(Bucket=S3_BUCKET, Key=test_g)
            key_m, key_g = test_m, test_g
            break
        except Exception:
            continue
    
    if not key_m:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Artifacts not found for job_id")
    return {
        "manifest_url": s3.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key_m}, ExpiresIn=3600
        ),
        "scene_url": s3.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": key_g}, ExpiresIn=3600
        ),
    }


