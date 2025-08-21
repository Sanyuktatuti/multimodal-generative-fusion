
from .base import EnvGenerator
import uuid
from pathlib import Path
from typing import Dict, Any, List
import os
import torch
from PIL import Image
try:
    from diffusers import StableDiffusionXLPipeline  # type: ignore
except Exception:  # pragma: no cover
    StableDiffusionXLPipeline = None  # type: ignore
from .mesh_utils import (
    triposr_single_image_to_mesh,
    zero123_novel_views,
    clean_and_pack_glb,
)

class Env_TripoSR_Fast(EnvGenerator):
    def __init__(self, weights_dir=None, cfg=None):
        super().__init__(weights_dir, cfg or {})
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.num_refs = int(self.cfg.get("num_refs", 2))
        self.guidance_scale = float(self.cfg.get("guidance", 7.0))
        self.steps = int(self.cfg.get("steps", 24))
        self.enable_zero123 = bool(self.cfg.get("zero123", False))
        self.zero123_ckpt = os.getenv("ZERO123_CKPT")
        if StableDiffusionXLPipeline is not None:
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            ).to(self.device)
            try:
                self.pipe.enable_attention_slicing()
            except Exception:
                pass
        else:
            self.pipe = None

    def _ref_images(self, prompt: str, outdir: Path) -> List[Path]:
        outdir.mkdir(parents=True, exist_ok=True)
        paths: List[Path] = []
        if self.pipe is None:
            # Fallback to blank images when diffusers not installed
            from PIL import Image
            for i in range(self.num_refs):
                img = Image.new("RGB", (512, 512), (30, 30, 30))
                p = outdir / f"ref_{i}.png"
                img.save(p)
                paths.append(p)
            return paths
        for i in range(self.num_refs):
            img = self.pipe(
                prompt, num_inference_steps=self.steps, guidance_scale=self.guidance_scale
            ).images[0]
            p = outdir / f"ref_{i}.png"
            img.save(p)
            paths.append(p)
        return paths

    def generate(self, scene_plan: Dict[str, Any]) -> Dict[str, Any]:
        # Derive a prompt from scene plan
        env = scene_plan.get("environment", {})
        prompt = f"{env.get('theme','scene')}, {env.get('time_of_day','night')}, {env.get('weather','none')}, cinematic"

        job_root = Path(self.cfg.get("job_root", os.getenv("JOB_TMP_DIR", "/app/tmp"))) / f"env_{uuid.uuid4().hex}"
        refs_dir = job_root / "refs"
        meshes_dir = job_root / "meshes"
        out_glb = job_root / "scene.glb"
        meshes_dir.mkdir(parents=True, exist_ok=True)

        ref_paths = self._ref_images(prompt, refs_dir)

        groups: List[List[str]] = []
        if self.enable_zero123 and self.zero123_ckpt and os.path.exists(self.zero123_ckpt):
            for rp in ref_paths:
                mv = zero123_novel_views(rp, meshes_dir, ckpt=self.zero123_ckpt, device=self.device)
                groups.append(mv)
        else:
            groups = [[str(p)] for p in ref_paths]

        mesh_paths: List[str] = []
        for idx, views in enumerate(groups):
            mpath = triposr_single_image_to_mesh(views[0], meshes_dir / f"asset_{idx}")
            mesh_paths.append(mpath)

        clean_and_pack_glb(mesh_paths, out_glb)

        return {
            "artifacts": {"scene_glb": str(out_glb)},
            "provenance": {
                "name": "env/triposr_fast",
                "version": "0.2.0",
                "components": {
                    "sdxl": "stabilityai/sdxl-base-1.0" if self.pipe is not None else "stub",
                    "triposr": "facebookresearch/TripoSR",
                    "zero123pp": "enabled" if (self.enable_zero123 and self.zero123_ckpt) else "optional",
                },
            },
        }
