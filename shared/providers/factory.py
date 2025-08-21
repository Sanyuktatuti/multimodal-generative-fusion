
from .env_sdxl_triposr_v1 import Env_SDXL_TripoSR_v1
from .env_triposr_fast import Env_TripoSR_Fast
from .motion_mdm_base import Motion_MDM_Base
from .audio_musicgen_small import Audio_MusicGen_Small

PROVIDERS = {
  ("env","sdxl_triposr"): Env_TripoSR_Fast,
  ("motion","mdm_base"):   Motion_MDM_Base,
  ("audio","musicgen_small"): Audio_MusicGen_Small,
}

def get_provider(stage: str, name: str, version: str, cfg=None):
    cls = PROVIDERS[(stage, name)]
    return cls(weights_dir=None, cfg=cfg)
