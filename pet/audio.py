"""Sound synthesis and sound effect manager for desktop sheep pet."""

import os
import math
import wave
import struct
import tempfile
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect


def generate_wav_file(path: str, samples: list, sample_rate: int = 22050):
    """Save raw audio samples to a 16-bit mono WAV file."""
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        raw = bytearray()
        for s in samples:
            val = int(max(-32767, min(32767, s)))
            raw += struct.pack("<h", val)
        wf.writeframes(raw)


def synth_baa(path: str, sample_rate: int = 22050):
    """Synthesize a cute gentle sheep bleat 'baaaa~'."""
    duration = 0.45
    n = int(sample_rate * duration)
    samples = []
    base_freq = 380.0
    for i in range(n):
        t = i / sample_rate
        # Pitch drops slightly then vibrato
        vib = 15.0 * math.sin(2 * math.pi * 7.5 * t)
        freq = base_freq - 40.0 * (t / duration) + vib
        # Soft envelope (fade in and fade out)
        if t < 0.05:
            env = t / 0.05
        elif t > 0.35:
            env = max(0.0, (duration - t) / 0.1)
        else:
            env = 1.0

        # Harmonic richness
        val = (
            math.sin(2 * math.pi * freq * t) * 0.7
            + math.sin(2 * math.pi * freq * 2 * t) * 0.2
            + math.sin(2 * math.pi * freq * 3 * t) * 0.1
        )
        samples.append(val * env * 18000)
    generate_wav_file(path, samples, sample_rate)


def synth_munch(path: str, sample_rate: int = 22050):
    """Synthesize a cute nibble/chewing crunch sound."""
    duration = 0.15
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t = i / sample_rate
        env = max(0.0, 1.0 - (t / duration))
        # High frequency clicks/crunch
        f1 = 600 + 400 * math.sin(2 * math.pi * 30 * t)
        val = math.sin(2 * math.pi * f1 * t) * 0.5 + ((i % 17) - 8) / 16.0 * 0.5
        samples.append(val * env * 14000)
    generate_wav_file(path, samples, sample_rate)


def synth_pop(path: str, sample_rate: int = 22050):
    """Synthesize a cheerful bubble/heart pop sound."""
    duration = 0.1
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t = i / sample_rate
        # Fast upward chirp
        freq = 400.0 + 800.0 * (t / duration)
        env = max(0.0, 1.0 - (t / duration)) ** 1.5
        val = math.sin(2 * math.pi * freq * t)
        samples.append(val * env * 16000)
    generate_wav_file(path, samples, sample_rate)


def synth_boing(path: str, sample_rate: int = 22050):
    """Synthesize a springy bounce sound."""
    duration = 0.22
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t = i / sample_rate
        freq = 220.0 + 350.0 * (1.0 - math.exp(-t * 12))
        env = max(0.0, 1.0 - (t / duration))
        val = math.sin(2 * math.pi * freq * t)
        samples.append(val * env * 17000)
    generate_wav_file(path, samples, sample_rate)


def synth_happy(path: str, sample_rate: int = 22050):
    """Synthesize a happy two-tone chime for petting."""
    duration = 0.25
    n = int(sample_rate * duration)
    samples = []
    for i in range(n):
        t = i / sample_rate
        freq = 523.25 if t < 0.12 else 659.25  # C5 to E5
        env = max(0.0, 1.0 - ((t % 0.12) / 0.12))
        val = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
        samples.append(val * env * 15000)
    generate_wav_file(path, samples, sample_rate)


class SoundManager:
    """Manages synthesis, caching, and playback of pet sound effects."""

    def __init__(self, cache_dir: str = None):
        self.muted = False
        self.volume = 0.7
        self.effects = {}

        if cache_dir is None:
            self.cache_dir = Path(tempfile.gettempdir()) / "desktop_sheep_audio"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._init_sounds()

    def _init_sounds(self):
        """Synthesize sound files and prepare QSoundEffects."""
        generators = {
            "baa": synth_baa,
            "munch": synth_munch,
            "pop": synth_pop,
            "boing": synth_boing,
            "happy": synth_happy,
        }

        for name, gen_fn in generators.items():
            wav_path = self.cache_dir / f"{name}.wav"
            try:
                if not wav_path.exists() or wav_path.stat().st_size == 0:
                    gen_fn(str(wav_path))

                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(wav_path)))
                effect.setVolume(self.volume)
                self.effects[name] = effect
            except Exception as e:
                print(f"[SoundManager] Warning: could not prepare sound {name}: {e}")

    def play(self, name: str):
        """Play a sound effect if not muted."""
        if self.muted:
            return
        effect = self.effects.get(name)
        if effect:
            try:
                effect.stop()
                effect.play()
            except Exception as e:
                # Audio playback failure shouldn't crash app
                pass

    def set_muted(self, muted: bool):
        self.muted = muted

    def toggle_muted(self) -> bool:
        self.muted = not self.muted
        return self.muted

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))
        for effect in self.effects.values():
            effect.setVolume(self.volume)
