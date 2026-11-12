r"""Sounds for factory TEST assets (tools\assets\test_assets.py): short pleasant tones, made with numpy and
written by ffmpeg (bit-exact WAV, no metadata). Deterministic: the key and voicing come from the slot id.

  music.*   calm 8-bar loop (pad chords, plucked arpeggio, soft bass), I-V-vi-IV; the loop wraps its
            note tails to the start, so it repeats without a click. music.feature is brighter and faster.
  sting.*   arpeggio into a held chord (big win), a IV-V-I fanfare (max win), a rising shimmer (bonus intro)
  sfx.*     clicks, soft lands, bell chimes on a pentatonic scale, arpeggios for wins, a riser, a coin loop
"""

import hashlib
import subprocess
from pathlib import Path

import numpy as np

RATE = 44100
BITEXACT = ["-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact"]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
PENTA = [0, 2, 4, 7, 9]
CHORDS = {"I": [0, 4, 7], "ii": [2, 5, 9], "IV": [5, 9, 12], "V": [7, 11, 14], "vi": [9, 12, 16]}


def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


class Track:
    def __init__(self, seconds: float, loop=False):
        self.n = int(round(seconds * RATE))
        self.loop = loop
        self.buf = np.zeros(self.n + (RATE * 3 if loop else RATE * 2), np.float64)

    def add(self, t0: float, wave: np.ndarray, gain=1.0):
        i = int(round(t0 * RATE))
        end = min(len(self.buf), i + len(wave))
        self.buf[i:end] += wave[: end - i] * gain

    def render(self, peak=0.8) -> np.ndarray:
        if self.loop:  # wrap tails into the start: seamless loop
            out = self.buf[: self.n].copy()
            tail = self.buf[self.n:]
            for k in range(0, len(tail), self.n):
                part = tail[k:k + self.n]
                out[: len(part)] += part
        else:
            nz = np.nonzero(np.abs(self.buf) > 1e-4)[0]
            out = self.buf[: (nz[-1] + 1 if len(nz) else self.n)].copy()
            fade = min(len(out), int(0.02 * RATE))
            out[len(out) - fade:] *= np.linspace(1, 0, fade)
        m = np.abs(out).max()
        return out * (peak / m) if m > 0 else out


def tone(freq, dur, partials, decay, attack=0.004):
    t = np.arange(int(dur * RATE)) / RATE
    w = sum(a * np.sin(2 * np.pi * freq * k * t) for k, a in partials)
    env = np.exp(-t * decay) * np.minimum(1, t / attack)
    rel = min(len(t), int(0.01 * RATE))
    env[len(t) - rel:] *= np.linspace(1, 0, rel)
    return w * env


def bell(freq, dur=1.2):
    return tone(freq, dur, [(1, 1.0), (2, 0.35), (3, 0.12), (4.2, 0.06)], 3.5)


def pluck(freq, dur=0.6):
    return tone(freq, dur, [(1, 1.0), (2, 0.4), (3, 0.15)], 6.0)


def pad(freq, dur):
    t = np.arange(int(dur * RATE)) / RATE
    w = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t) + 0.1 * np.sin(2 * np.pi * freq * 1.003 * t)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return w * env


def thud(freq, dur=0.18):
    t = np.arange(int(dur * RATE)) / RATE
    f = freq * (1 + 0.6 * np.exp(-t * 40))
    return np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t * 22) * np.minimum(1, t / 0.002)


def noise_burst(dur, rng):
    t = np.arange(int(dur * RATE)) / RATE
    n = rng.standard_normal(len(t))
    n = np.convolve(n, np.ones(6) / 6, mode="same")  # soften
    return n * np.exp(-t * 18)


def loop_music(key: int, bpm: float, bright: bool) -> np.ndarray:
    beat = 60 / bpm
    bar = beat * 4
    prog = ["I", "V", "vi", "IV", "I", "V", "IV", "I"] if not bright else ["vi", "IV", "I", "V", "vi", "IV", "V", "I"]
    tr = Track(bar * 8, loop=True)
    for b, name in enumerate(prog):
        t0 = b * bar
        chord = CHORDS[name]
        for iv in chord:
            tr.add(t0, pad(hz(key + iv), bar), 0.10)
        tr.add(t0, pluck(hz(key - 12 + chord[0]), 1.2), 0.30)
        tr.add(t0 + 2 * beat, pluck(hz(key - 12 + chord[0] + (7 if b % 2 else 0)), 1.0), 0.22)
        pattern = [0, 1, 2, 1, 2, 1, 0, 1] if not bright else [0, 1, 2, 3, 2, 1, 2, 3]
        notes = chord + [chord[0] + 12]
        for k, idx in enumerate(pattern):
            tr.add(t0 + k * beat / 2, pluck(hz(key + 12 + notes[idx]), 0.5), 0.16 if not bright else 0.19)
    return tr.render(0.7)


def arpeggio(tr, t0, key, steps, gap, voice=bell, gain=0.35, dur=1.0):
    for k, s in enumerate(steps):
        tr.add(t0 + k * gap, voice(hz(key + s), dur), gain)


def chord_hit(tr, t0, key, chord, dur, gain=0.18):
    for iv in chord:
        tr.add(t0, bell(hz(key + iv), dur), gain)
        tr.add(t0, pad(hz(key + iv - 12), dur), gain * 0.6)


def sfx(sid: str, key: int, rng) -> np.ndarray:
    tr = Track(4)
    if sid == "sfx.click":
        tr.add(0, tone(1800, 0.05, [(1, 1)], 90), 1)
    elif sid == "sfx.spin":
        arpeggio(tr, 0, key + 12, [0, 7], 0.06, pluck, 0.5, 0.25)
    elif sid == "sfx.land":
        tr.add(0, thud(hz(key - 12)), 1)
    elif sid == "sfx.scatterLand":
        tr.add(0, bell(hz(key + 24), 0.7), 0.6)
        tr.add(0.01, bell(hz(key + 31), 0.6), 0.3)
    elif sid == "sfx.scatterWin":
        arpeggio(tr, 0, key + 12, [0, 4, 7, 12, 16], 0.07, bell, 0.35, 0.8)
    elif sid == "sfx.riser":
        t = np.arange(int(3.0 * RATE)) / RATE
        f = hz(key - 5) * 2 ** (2 * t / 3.0)
        w = np.sin(2 * np.pi * np.cumsum(f) / RATE) * (t / 3.0) ** 1.5 * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * t))
        tr.add(0, w, 0.5)
        for k in range(12):
            tr.add(1.5 + k * 0.12, bell(hz(key + 24 + PENTA[k % 5] + 12 * (k // 5)), 0.4), 0.06 + k * 0.01)
    elif sid.startswith("sfx.chime") and sid[-1].isdigit():
        step = int(sid[-1]) - 1
        tr.add(0, bell(hz(key + 12 + PENTA[step % 5] + 12 * (step // 5)), 0.9), 0.6)
    elif sid == "sfx.spotMark":
        tr.add(0, bell(hz(key + 28), 0.35), 0.4)
        tr.add(0, noise_burst(0.15, rng), 0.05)
    elif sid == "sfx.spotUp":
        arpeggio(tr, 0, key + 19, [0, 5, 9, 12], 0.05, bell, 0.3, 0.35)
    elif sid == "sfx.spotBurst":
        tr.add(0, noise_burst(0.25, rng), 0.5)
        tr.add(0, thud(hz(key - 5), 0.25), 0.8)
        tr.add(0.02, bell(hz(key + 24), 0.3), 0.2)
    elif sid == "sfx.spotWin":
        chord_hit(tr, 0, key + 12, [0, 4, 7, 12], 0.9)
        arpeggio(tr, 0.05, key + 24, [0, 4, 7, 12], 0.04, bell, 0.12, 0.4)
    elif sid == "sfx.spotReset":
        arpeggio(tr, 0, key + 12, [7, 4, 0], 0.08, pluck, 0.4, 0.3)
    elif sid == "sfx.retrigger":
        arpeggio(tr, 0, key + 12, [0, 4, 7, 12, 16, 19, 24], 0.07, bell, 0.3, 0.6)
    elif sid == "sfx.coins":
        tr = Track(1.2, loop=True)
        for k in range(10):
            tr.add(k * 0.12 + rng.uniform(0, 0.03), bell(hz(key + 31 + PENTA[int(rng.integers(0, 5))]), 0.3), 0.3)
    elif sid == "sfx.winSmall":
        arpeggio(tr, 0, key + 12, [0, 4, 7], 0.08, bell, 0.4, 0.6)
    elif sid == "sfx.winMid":
        arpeggio(tr, 0, key + 12, [0, 4, 7, 12, 16], 0.08, bell, 0.3, 0.6)
        chord_hit(tr, 0.42, key + 12, [0, 4, 7], 0.8)
    elif sid == "sfx.winEnd":
        chord_hit(tr, 0, key + 12, CHORDS["V"], 0.45, 0.15)
        chord_hit(tr, 0.4, key + 12, CHORDS["I"] + [12], 1.0, 0.18)
    else:
        tr.add(0, bell(hz(key + 12 + PENTA[seed(sid) % 5]), 0.6), 0.5)
    return tr.render(0.8)


def sting(sid: str, key: int) -> np.ndarray:
    tr = Track(8)
    if sid == "sting.maxWin":
        for k, (name, t0) in enumerate((("IV", 0.0), ("V", 0.7), ("I", 1.4))):
            arpeggio(tr, t0, key + 12, CHORDS[name] + [CHORDS[name][0] + 12], 0.07, bell, 0.25, 0.9)
            chord_hit(tr, t0, key, CHORDS[name], 0.8 if k < 2 else 3.2, 0.16)
        arpeggio(tr, 1.7, key + 24, [0, 4, 7, 12, 16, 19, 24], 0.06, bell, 0.12, 1.2)
    elif sid == "sting.bonusIntro":
        for k in range(14):
            tr.add(k * 0.09, bell(hz(key + 12 + PENTA[k % 5] + 12 * (k // 5)), 0.6), 0.12 + k * 0.012)
        chord_hit(tr, 0.9, key, CHORDS["I"] + [12], 1.6, 0.14)
    else:  # sting.bigWin and any other sting
        arpeggio(tr, 0, key + 12, [0, 4, 7, 12, 16, 19, 24], 0.08, bell, 0.25, 0.8)
        chord_hit(tr, 0.6, key, CHORDS["I"] + [12], 2.2, 0.17)
    return tr.render(0.8)


def write_wav(samples: np.ndarray, out: Path):
    pcm = (np.clip(samples, -1, 1) * 32767).round().astype("<i2").tobytes()
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", "pipe:0",
                    "-ac", "2", *BITEXACT, "-c:a", "pcm_s16le", str(out)], input=pcm, check=True)


def make(slot: dict, out: Path, game_key: str = ""):
    sid = slot["id"]
    key = 57 + seed("key:" + game_key) % 7  # one key per game (A3..D#4), so all sounds fit together
    rng = np.random.default_rng(seed(sid))
    if sid.startswith("music."):
        bright = sid != "music.base"
        samples = loop_music(key + (5 if bright else 0), 112 if bright else 92, bright)
    elif sid.startswith("sting."):
        samples = sting(sid, key)
    else:
        samples = sfx(sid, key, rng)
    write_wav(samples, out)
