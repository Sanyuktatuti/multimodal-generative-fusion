
from celery import Celery
import json
import redis
from shared.providers.factory import get_provider

import os
import uuid
import boto3
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", "0")
REDIS_BACKEND_DB = os.getenv("REDIS_BACKEND_DB", "1")
REDIS_STATUS_DB = int(os.getenv("REDIS_STATUS_DB", "0"))

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"
backend_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}"

print(f"DEBUG: REDIS_HOST={REDIS_HOST}, broker_url={broker_url}")

app = Celery("env_gen")
app.conf.update(
    broker_url=broker_url,
    result_backend=backend_url,
    task_default_queue="env",
    broker_connection_retry_on_startup=True,
)


def set_status(job_id, status, detail=None):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_STATUS_DB, decode_responses=True)
    payload = {"status": status}
    if detail:
        payload["detail"] = detail
    r.set(job_id, json.dumps(payload))


@app.task(queue="env")
def run_env(job_id, plan_path, provider_name="stub", version="0.1.0"):
    from shared.schemas.scene_plan import ScenePlan
    with open(plan_path) as f:
        raw = json.load(f)
    plan = ScenePlan(**raw)

    provider = get_provider("env", provider_name, version)
    result = provider.generate(plan.dict())

    out_path = result["artifacts"]["scene_glb"]
    prov = result["provenance"]

    set_status(job_id, "env_done", {"scene_glb": out_path, "prov": prov})
    return out_path


# Cloud submission via SageMaker Processing
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
ECR_IMAGE_URI = os.getenv("ECR_IMAGE_URI")
S3_BUCKET = os.getenv("S3_BUCKET")  # e.g., s3://bucket or s3://bucket/prefix
ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN", "arn:aws:iam::398341427473:role/SageMakerProcessingRole")


@app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3, queue="env")
def run_env_cloud(self, prompt: str, job_id: str | None = None) -> dict:
    job_id = job_id or f"envgen-{uuid.uuid4().hex[:8]}"
    # Normalize out_bucket to the bucket root (strip any suffix like /jobs or other prefixes)
    out_bucket = S3_BUCKET or ""
    if out_bucket.startswith("s3://"):
        bucket_part = out_bucket.replace("s3://", "", 1)
        bucket_name = bucket_part.split("/", 1)[0]
        out_bucket = f"s3://{bucket_name}"
    payload = {"prompt": prompt, "out_bucket": out_bucket, "job_id": job_id}
    sm = boto3.client("sagemaker", region_name=AWS_REGION)
    sm.create_processing_job(
        ProcessingJobName=job_id,
        RoleArn=ROLE_ARN,
        AppSpecification={"ImageUri": ECR_IMAGE_URI},
        Environment={
            "PROMPT_JSON": json.dumps(payload),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        },
        ProcessingResources={
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": os.getenv("SM_INSTANCE_TYPE", "ml.m5.xlarge"),
                "VolumeSizeInGB": int(os.getenv("SM_VOL_GB", "50")),
            }
        },
        StoppingCondition={"MaxRuntimeInSeconds": int(os.getenv("SM_MAX_SEC", "1800"))},
    )
    return {"job_id": job_id, "status": "submitted"}
