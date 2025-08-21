
from pydantic import BaseModel
from typing import Optional, Dict

class Artifact(BaseModel):
    path: str  # local path or URL
    type: str  # e.g., "scene_glb", "splat"
    format: str  # e.g., "glb", "splat"
    provenance: Dict[str, str]

class JobManifest(BaseModel):
    job_id: str
    artifacts: Dict[str, Artifact] = {}
