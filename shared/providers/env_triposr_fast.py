
from .base import EnvGenerator
import uuid

class Env_TripoSR_Fast(EnvGenerator):
    def generate(self, scene_plan):
        """
        Fast path stub: returns a placeholder GLB path.
        """
        import os
        base_tmp_dir = os.getenv("JOB_TMP_DIR", "/app/tmp")
        try:
            os.makedirs(base_tmp_dir, exist_ok=True)
        except Exception:
            pass
        fake_path = f"{base_tmp_dir}/{uuid.uuid4()}_scene.glb"
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
