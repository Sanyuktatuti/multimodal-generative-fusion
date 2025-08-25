
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

class EnvSpec(BaseModel):
    theme: str
    weather: Optional[Literal["none","light_rain","heavy_rain","fog","snow"]] = "none"
    time_of_day: Optional[Literal["day","golden_hour","night"]] = "night"

class ObjectSpec(BaseModel):
    type: str
    instances: int = Field(ge=1, le=32)
    tags: List[str] = []
    text_overlays: Optional[List[str]] = None

class CharacterSpec(BaseModel):
    archetype: str = "generic"
    rig: Literal["humanoid"] = "humanoid"
    motion_text: str = "walk"

class CameraSpec(BaseModel):
    path: Literal["dolly","orbit","static"] = "dolly"
    duration_s: int = Field(ge=2, le=30, default=8)

class AudioSpec(BaseModel):
    tempo: int = Field(ge=60, le=180, default=80)
    mood: List[str] = ["lofi","minor"]
    sfx: List[str] = ["ambience"]

class ScenePlan(BaseModel):
    environment: EnvSpec
    objects: List[ObjectSpec] = Field(default_factory=list, min_items=0, max_items=20)
    character: Optional[CharacterSpec] = None
    camera: CameraSpec
    audio: AudioSpec
