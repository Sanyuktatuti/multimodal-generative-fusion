
from .base import EnvGenerator

class Env_SDXL_TripoSR_v1(EnvGenerator):
    def generate(self, scene_plan):
        return {
            "artifacts": {"scene_glb": "file://tmp/stub_scene.glb"},
            "provenance": {"name": "env/sdxl_triposr", "version": "1.0.0", "seed": 42}
        }
