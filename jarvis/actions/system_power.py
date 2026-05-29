"""
Performans (oyun) modu + guc islemleri.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- set_performance_mode: Windows guc planini Yuksek Performans (oyun) veya
  Dengeli (normal) yapar. EXON arayuzu de ayrica kendi yukunu dusurur.
- power_action: kilitle / uyut / yeniden baslat / kapat / iptal.
"""

from __future__ import annotations

import subprocess
import sys


_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

# Standart Windows guc plani GUID'leri (alias calismazsa yedek)
_HIGH_GUID = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"   # Yuksek Performans
_BAL_GUID  = "381b4222-f694-41f0-9685-ff5bb260df2e"   # Dengeli


def _run(args: list[str]) -> tuple[int, str]:
    try:
        r = subprocess.run(args, capture_output=True, text=True, creationflags=_NOWIN)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as exc:
        return 1, str(exc)


def _set_plan(alias: str, guid: str) -> bool:
    rc, _ = _run(["powercfg", "/s", alias])
    if rc == 0:
        return True
    rc, _ = _run(["powercfg", "/s", guid])
    return rc == 0


def set_performance_mode(mode: str = "game") -> str:
    """mode=game -> Yuksek Performans; mode=normal -> Dengeli."""
    m = (mode or "game").lower().strip()
    normal_words = ("normal", "off", "kapat", "kapa", "balanced", "dengeli", "dusur")
    if m in normal_words:
        ok = _set_plan("SCHEME_BALANCED", _BAL_GUID)
        return ("Normal moda gecildi — Dengeli guc plani etkin."
                if ok else
                "Normal moda gecilemedi (yonetici izni gerekebilir).")

    ok = _set_plan("SCHEME_MIN", _HIGH_GUID)
    if ok:
        return ("Oyun modu acildi 🎮 — Yuksek Performans guc plani etkin, "
                "EXON kendi kaynak kullanimini da dusurdu. Iyi oyunlar!")
    return ("Oyun modu kismen acildi: guc plani ayarlanamadi (yonetici izni "
            "gerekebilir), ama EXON yine de kendi yukunu dusurdu.")


_POWER = {
    "lock":     (["rundll32.exe", "user32.dll,LockWorkStation"], "Bilgisayar kilitlendi."),
    "sleep":    (["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                 "Bilgisayar uyku moduna aliniyor."),
    "restart":  (["shutdown", "/r", "/t", "0"], "Bilgisayar yeniden baslatiliyor."),
    "shutdown": (["shutdown", "/s", "/t", "0"], "Bilgisayar kapatiliyor."),
    "cancel":   (["shutdown", "/a"], "Planli kapatma iptal edildi."),
}

_POWER_ALIASES = {
    "kilitle": "lock", "kilit": "lock", "lock": "lock",
    "uyut": "sleep", "uyku": "sleep", "sleep": "sleep",
    "yeniden baslat": "restart", "yeniden başlat": "restart",
    "yeniden": "restart", "restart": "restart",
    "kapat": "shutdown", "kapa": "shutdown", "shutdown": "shutdown",
    "iptal": "cancel", "cancel": "cancel",
}


def power_action(action: str) -> str:
    """Guc islemi: lock / sleep / restart / shutdown / cancel."""
    a = (action or "").lower().strip()
    a = _POWER_ALIASES.get(a, a)
    if a not in _POWER:
        return "Gecersiz guc islemi. Sunlardan biri olmali: lock, sleep, restart, shutdown, cancel."
    args, msg = _POWER[a]
    rc, out = _run(args)
    if rc == 0:
        return msg
    return f"Islem yapilamadi: {out[:160]}"
