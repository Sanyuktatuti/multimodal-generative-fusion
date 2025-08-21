from celery import Celery
import time
import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_BROKER_DB = os.getenv("REDIS_BROKER_DB", "0")
REDIS_BACKEND_DB = os.getenv("REDIS_BACKEND_DB", "1")
REDIS_STATUS_DB = int(os.getenv("REDIS_STATUS_DB", "0"))

broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"
backend_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BACKEND_DB}"

app = Celery("orchestrator", broker=broker_url, backend=backend_url)


@app.task
def run_pipeline(job_id: str, prompt: str) -> None:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_STATUS_DB, decode_responses=True)
    r.set(job_id, "running")
    time.sleep(5)
    r.set(job_id, "done")
