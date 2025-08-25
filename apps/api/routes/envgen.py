from fastapi import APIRouter
from pydantic import BaseModel
import os
import uuid
import json
import boto3


router = APIRouter(prefix="/v1/generations", tags=["envgen"])

S3_BUCKET = os.getenv("S3_BUCKET", "s3://multimodal-fusion-models-sanyuktatuti").replace("s3://", "").split("/", 1)[0]


class GenReq(BaseModel):
    prompt: str


@router.post("")
def submit(req: GenReq):
    job_id = f"envgen-{uuid.uuid4().hex[:8]}"
    
    # Direct SageMaker submission (cloud deployment)
    try:
        # Normalize out_bucket to the bucket root 
        out_bucket = os.getenv("S3_BUCKET", "")
        if out_bucket.startswith("s3://"):
            bucket_part = out_bucket.replace("s3://", "", 1)
            bucket_name = bucket_part.split("/", 1)[0]
            out_bucket = f"s3://{bucket_name}"
        
        payload = {"prompt": req.prompt, "out_bucket": out_bucket, "job_id": job_id}
        
        sm = boto3.client("sagemaker", region_name=os.getenv("AWS_REGION", "us-east-1"))
        sm.create_processing_job(
            ProcessingJobName=job_id,
            RoleArn=os.getenv("SAGEMAKER_ROLE_ARN"),
            AppSpecification={"ImageUri": os.getenv("ECR_IMAGE_URI")},
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
        return {"task_id": job_id, "job_id": job_id, "status": "submitted"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get("/{task_id}/status")
def status(task_id: str):
    # Cloud deployment: check SageMaker job status directly
    try:
        sm = boto3.client("sagemaker", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = sm.describe_processing_job(ProcessingJobName=task_id)
        status = response["ProcessingJobStatus"]
        return {
            "state": "SUCCESS" if status == "Completed" else "PENDING" if status == "InProgress" else "FAILURE",
            "job_id": task_id,
            "sagemaker_status": status
        }
    except Exception as e:
        return {"state": "UNKNOWN", "job_id": task_id, "error": str(e)}


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


