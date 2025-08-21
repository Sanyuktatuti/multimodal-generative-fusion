
from .base import AudioGenerator

class Audio_MusicGen_Small(AudioGenerator):
    def generate(self, audio_spec):
        return {
            "artifacts": {"music_mp3": "file://tmp/stub_track.mp3"},
            "provenance": {"name": "audio/musicgen_small", "version": "1.1.0"}
        }
