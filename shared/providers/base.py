
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class EnvGenerator(ABC):
    def __init__(self, weights_dir: Optional[str] = None, cfg: Optional[Dict[str, Any]] = None):
        self.weights_dir = weights_dir
        self.cfg = cfg or {}
    @abstractmethod
    def generate(self, scene_plan: Dict[str, Any]) -> Dict[str, Any]:
        ...

class MotionGenerator(ABC):
    def __init__(self, weights_dir: Optional[str] = None, cfg: Optional[Dict[str, Any]] = None):
        self.weights_dir = weights_dir
        self.cfg = cfg or {}
    @abstractmethod
    def generate(self, motion_spec: Dict[str, Any]) -> Dict[str, Any]:
        ...

class AudioGenerator(ABC):
    def __init__(self, weights_dir: Optional[str] = None, cfg: Optional[Dict[str, Any]] = None):
        self.weights_dir = weights_dir
        self.cfg = cfg or {}
    @abstractmethod
    def generate(self, audio_spec: Dict[str, Any]) -> Dict[str, Any]:
        ...
