from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import redis
from dotenv import load_dotenv
from workers.orchestrator.tasks import run_pipeline

load_dotenv()

app = FastAPI(title="Multimodal Fusion API", version="0.1.0")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_STATUS_DB", "0"))

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
)

# Enable CORS for local dev and viewer (adjust origins as needed)
ALLOWED_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobRequest(BaseModel):
    prompt: str


@app.post("/v1/generations")
def create_generation(req: JobRequest):
    job_id = str(uuid.uuid4())
    redis_client.set(job_id, "queued")
    run_pipeline.delay(job_id, req.prompt)
    return {"job_id": job_id, "status": "queued"}


@app.get("/v1/generations/{job_id}/status")
def get_status(job_id: str):
    status = redis_client.get(job_id)
    return {"job_id": job_id, "status": status or "unknown"}
