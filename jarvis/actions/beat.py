"""
Sarki icin basit ritim/beat uretimi — stdlib (numpy/ek paket GEREKTIRMEZ).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Tur bazli (rap/pop/duygusal/rock) 2 olcu'luk donguye uygun bir WAV uretir ve
yolunu dondurur. Uretilen dosya 'beats/' altinda onbeleklenir (bir kez uretilir).
EXON sarki soylerken bu dongu arka planda calar.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


from paths import DATA_DIR

_BEAT_DIR = DATA_DIR / "beats"
_SR = 44100

# tur -> (bpm, kick16, snare16, hat16)  her desen 16 adim, '1' = vurus
_STYLES = {
    "rap":      (88,  "1000001000100000", "0000100000001000", "1010101010101010"),
    "pop":      (118, "1000100010001000", "0000100000001000", "0010001000100010"),
    "duygusal": (72,  "1000000010000000", "0000000010000000", "0000100000001000"),
    "rock":     (100, "1010001010100010", "0000100000001000", "1111111111111111"),
}
_ALIASES = {
    "emotional": "duygusal", "sad": "duygusal", "ballad": "duygusal",
    "hüzünlü": "duygusal", "huzunlu": "duygusal", "arabesk": "duygusal", "slow": "duygusal",
    "hiphop": "rap", "hip-hop": "rap", "trap": "rap",
    "mutlu": "pop", "happy": "pop", "dance": "pop", "electronic": "pop", "elektronik": "pop",
}


def _kick(dur: float = 0.20) -> list[float]:
    n = int(_SR * dur); o = [0.0] * n
    for i in range(n):
        t = i / _SR
        f = 48 + 70 * math.exp(-32 * t)
        o[i] = math.sin(2 * math.pi * f * t) * math.exp(-16 * t)
    return o


def _snare(dur: float = 0.18) -> list[float]:
    n = int(_SR * dur); o = [0.0] * n
    for i in range(n):
        t = i / _SR
        o[i] = (random.uniform(-1, 1) * 0.7 + math.sin(2 * math.pi * 190 * t) * 0.3) * math.exp(-28 * t)
    return o


def _hat(dur: float = 0.05) -> list[float]:
    n = int(_SR * dur); o = [0.0] * n
    for i in range(n):
        t = i / _SR
        o[i] = random.uniform(-1, 1) * math.exp(-130 * t)
    return o


def _norm_style(style: str) -> str:
    s = (style or "pop").lower().strip()
    s = _ALIASES.get(s, s)
    return s if s in _STYLES else "pop"


def make_beat_loop(style: str = "pop") -> str | None:
    """Verilen tur icin donguye uygun bir beat WAV uretir/onbellekten dondurur."""
    s = _norm_style(style)
    try:
        _BEAT_DIR.mkdir(parents=True, exist_ok=True)
        path = _BEAT_DIR / f"beat_{s}.wav"
        if path.exists():
            return str(path)

        bpm, kp, sp, hp = _STYLES[s]
        step = (60.0 / bpm) / 4.0          # 16'lik nota suresi (sn)
        bars = 2
        total = int(_SR * step * 16 * bars) + _SR // 4
        buf = [0.0] * total
        kick, snare, hat = _kick(), _snare(), _hat()

        def place(samples: list[float], at: float, gain: float) -> None:
            off = int(at * _SR)
            for i, v in enumerate(samples):
                j = off + i
                if 0 <= j < total:
                    buf[j] += v * gain

        for bar in range(bars):
            for stp in range(16):
                at = (bar * 16 + stp) * step
                if kp[stp] == "1": place(kick, at, 0.95)
                if sp[stp] == "1": place(snare, at, 0.60)
                if hp[stp] == "1": place(hat, at, 0.25)

        peak = max(1e-6, max(abs(x) for x in buf))
        scale = 0.85 / peak
        frames = bytearray()
        for x in buf:
            frames += struct.pack("<h", int(max(-1.0, min(1.0, x * scale)) * 32767))

        with wave.open(str(path), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(_SR)
            w.writeframes(bytes(frames))
        return str(path)
    except Exception:
        return None
