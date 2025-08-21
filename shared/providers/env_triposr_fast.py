
from .base import EnvGenerator
import uuid

class Env_TripoSR_Fast(EnvGenerator):
    def generate(self, scene_plan):
        """
        Fast path stub: returns a placeholder GLB path.
        """
        fake_path = f"/tmp/{uuid.uuid4()}_scene.glb"
        with open(fake_path, "wb") as f:
            f.write(b"glTF-stub")
        return {
            "artifacts": {"scene_glb": fake_path},
            "provenance": {
                "name": "env/triposr_fast",
                "version": "0.1.0",
                "generator": "stub",
            },
        }
