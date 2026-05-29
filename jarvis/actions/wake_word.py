"""
Uyandırma sözcüğü ("Hey EXON") — Picovoice Porcupine.
Servan Kanğal tarafından yapılmıştır — EXON Windows Edition

Kullanım:
- config/api_keys.json içine "picovoice_access_key" ekle (ücretsiz: console.picovoice.ai).
- "Hey EXON" için Picovoice Console'da özel keyword (.ppn) eğit, indir ve ya
  "wake/Hey-EXON_windows.ppn" olarak koy ya da config "wake_keyword_path" ile belirt.
- Özel .ppn yoksa yerleşik "jarvis" kelimesine düşer (ücretsiz, hazır).

Bu sınıf KENDİ ses akışını açmaz; main.py'deki mikrofon döngüsünden gelen
16kHz mono int16 kareleri process() ile işler (tek mikrofon akışı paylaşılır).
"""

from __future__ import annotations

import struct
from pathlib import Path

from app_config import get_app_config_value

BASE_DIR = Path(__file__).resolve().parent.parent
WAKE_DIR = BASE_DIR / "wake"

try:
    import pvporcupine  # type: ignore
    _PORCUPINE_OK = True
except Exception:
    _PORCUPINE_OK = False


class WakeWordListener:
    def __init__(self):
        self._porcupine = None
        self.enabled = False
        self.label = ""
        self.frame_length = 512
        self.sample_rate = 16000
        self.status = "kapalı"
        self._buf = bytearray()
        self._init()

    def _init(self):
        if not _PORCUPINE_OK:
            self.status = "pvporcupine kurulu değil (pip install pvporcupine)"
            return
        access_key = str(get_app_config_value("picovoice_access_key", "") or "").strip()
        if not access_key:
            self.status = "picovoice_access_key eksik (console.picovoice.ai)"
            return

        keyword_paths = None
        keywords = None
        kw_path = str(get_app_config_value("wake_keyword_path", "") or "").strip()
        default_ppn = WAKE_DIR / "Hey-EXON_windows.ppn"
        if kw_path and Path(kw_path).exists():
            keyword_paths = [kw_path]
            self.label = Path(kw_path).stem.replace("_", " ")
        elif default_ppn.exists():
            keyword_paths = [str(default_ppn)]
            self.label = "Hey EXON"
        else:
            keywords = ["jarvis"]  # yerleşik yedek kelime
            self.label = "Jarvis"

        try:
            if keyword_paths:
                self._porcupine = pvporcupine.create(
                    access_key=access_key, keyword_paths=keyword_paths)
            else:
                self._porcupine = pvporcupine.create(
                    access_key=access_key, keywords=keywords)
            self.frame_length = self._porcupine.frame_length
            self.sample_rate = self._porcupine.sample_rate
            self.enabled = True
            self.status = f"aktif ({self.label})"
        except Exception as exc:
            self._porcupine = None
            self.enabled = False
            self.status = f"başlatılamadı: {str(exc)[:120]}"

    def process(self, pcm_bytes: bytes) -> bool:
        """16kHz mono int16 ses verisi al; uyandırma sözcüğü algılanırsa True döner."""
        if not self.enabled or not self._porcupine:
            return False
        self._buf.extend(pcm_bytes)
        frame_bytes = self.frame_length * 2
        detected = False
        while len(self._buf) >= frame_bytes:
            chunk = bytes(self._buf[:frame_bytes])
            del self._buf[:frame_bytes]
            try:
                pcm = struct.unpack_from("<%dh" % self.frame_length, chunk)
                if self._porcupine.process(pcm) >= 0:
                    detected = True
            except Exception:
                break
        return detected

    def close(self):
        try:
            if self._porcupine:
                self._porcupine.delete()
        except Exception:
            pass
        self._porcupine = None
        self.enabled = False
