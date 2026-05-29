"""
Yol yardimcisi — hem normal calismayi hem de PyInstaller ile derlenmis tek-exe
(donmus/frozen) calismayi AYNI kodla destekler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- RESOURCE_DIR: salt-okunur paketli kaynaklar (SFX, Icon, Fonts...).
  Normal: jarvis klasoru. Exe: PyInstaller'in actigi gecici klasor (_MEIPASS).
- DATA_DIR: kalici, yazilabilir kullanici verisi (config, memory, ciktilar).
  Normal: jarvis klasoru. Exe: EXON.exe'nin yaninda 'EXON_data' klasoru.

Normal calismada her ikisi de jarvis klasorudur; yani mevcut davranis birebir korunur.
"""

from __future__ import annotations

import sys
from pathlib import Path


_SRC_DIR = Path(__file__).resolve().parent


def _frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    if _frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return _SRC_DIR


def data_dir() -> Path:
    if _frozen():
        base = Path(sys.executable).resolve().parent / "EXON_data"
    else:
        base = _SRC_DIR
    # Yazicilarin guvenle calismasi icin yaygin alt klasorleri hazirla.
    for sub in ("", "config", "memory", "memory/health"):
        try:
            (base / sub).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    return base


RESOURCE_DIR = resource_dir()
DATA_DIR = data_dir()
