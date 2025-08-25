from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
from dotenv import load_dotenv
from apps.api.routes.planning import router as planning_router
from apps.api.routes import envgen as envgen_router

load_dotenv()

app = FastAPI(title="Multimodal Fusion API", version="0.1.0")
app.include_router(planning_router)
app.include_router(envgen_router.router)

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
    # Cloud API delegates to envgen router which handles SageMaker submission
    return {"message": "Use /v1/generations endpoint from envgen router"}


@app.get("/")
def root():
    return {"message": "Multimodal Fusion API", "version": "0.1.0", "endpoints": ["/docs", "/v1/generations"]}
