from .base import EnvGenerator
import uuid
from pathlib import Path
from typing import Dict, Any


class Env_Stub(EnvGenerator):
    """Stub environment generator for testing without heavy dependencies"""
    
    def __init__(self, weights_dir=None, cfg=None):
        super().__init__(weights_dir, cfg or {})
    
    def generate(self, scene_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a stub GLB file for testing"""
        # Create a simple stub GLB file
        job_root = Path(self.cfg.get("job_root", "/app/tmp")) / f"env_{uuid.uuid4().hex}"
        out_glb = job_root / "scene.glb"
        out_glb.parent.mkdir(parents=True, exist_ok=True)
        
        # Write a minimal GLB stub (just enough to be recognized as GLB)
        # This is a minimal GLB file with no geometry
        minimal_glb = b'glTF\x02\x00\x00\x00\x08\x00\x00\x00JSON{"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[]}],"nodes":[],"meshes":[],"accessors":[],"bufferViews":[],"buffers":[]}\x00\x00\x00\x00'
        
        with open(out_glb, "wb") as f:
            f.write(minimal_glb)
        
        return {
            "artifacts": {"scene_glb": str(out_glb)},
            "provenance": {
                "name": "env/stub",
                "version": "0.1.0",
                "components": {
                    "sdxl": "stub",
                    "triposr": "stub",
                    "zero123pp": "disabled"
                }
            }
        }
