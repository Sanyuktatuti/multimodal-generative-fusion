
from .base import MotionGenerator

class Motion_MDM_Base(MotionGenerator):
    def generate(self, motion_spec):
        return {
            "artifacts": {"anim_fbx": "file://tmp/stub_walk.fbx"},
            "provenance": {"name": "motion/mdm_base", "version": "0.9.0"}
        }
