"""
Tam Gelistirici Modu — EXON'un ic bilesenlerini canli izleme.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Calisma zamani telemetrisi toplar: son arac cagrilari, sayaclar, oturum suresi,
hafiza durumu, aktif alt sistemler. Gelistirici paneli ve 'sistem durumu' araci
bunu okur. Hafif ve thread-guvenli (deque + lock).
"""

from __future__ import annotations

import threading
import time
from collections import deque, Counter


_LOCK = threading.Lock()
_START = time.time()
_TOOL_LOG: deque = deque(maxlen=60)      # (zaman, arac, ok)
_TOOL_COUNTS: Counter = Counter()
_EVENTS: deque = deque(maxlen=40)        # (zaman, mesaj)
_STATE = {
    "last_tool": "-",
    "errors": 0,
    "tool_calls": 0,
}


def record_tool(name: str, ok: bool = True) -> None:
    with _LOCK:
        _TOOL_LOG.append((time.time(), name, ok))
        _TOOL_COUNTS[name] += 1
        _STATE["last_tool"] = name
        _STATE["tool_calls"] += 1
        if not ok:
            _STATE["errors"] += 1


def record_event(message: str) -> None:
    with _LOCK:
        _EVENTS.append((time.time(), str(message)[:120]))


def uptime_str() -> str:
    secs = int(time.time() - _START)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def snapshot() -> dict:
    """Gelistirici paneli icin anlik durum."""
    with _LOCK:
        recent = list(_TOOL_LOG)[-8:][::-1]
        top = _TOOL_COUNTS.most_common(6)
        events = list(_EVENTS)[-6:][::-1]
        state = dict(_STATE)
    return {
        "uptime": uptime_str(),
        "tool_calls": state["tool_calls"],
        "errors": state["errors"],
        "last_tool": state["last_tool"],
        "recent_tools": [(time.strftime("%H:%M:%S", time.localtime(t)), n,
                          "OK" if ok else "ERR") for t, n, ok in recent],
        "top_tools": top,
        "recent_events": [(time.strftime("%H:%M:%S", time.localtime(t)), m)
                          for t, m in events],
    }


def system_status_text() -> str:
    """'Sistem durumu / gelistirici raporu' araci icin metin ozeti."""
    snap = snapshot()
    lines = [
        "[EXON GELİŞTİRİCİ DURUMU]",
        f"Çalışma süresi: {snap['uptime']}",
        f"Toplam araç çağrısı: {snap['tool_calls']} (hata: {snap['errors']})",
        f"Son araç: {snap['last_tool']}",
    ]
    if snap["top_tools"]:
        lines.append("En çok kullanılan araçlar: "
                     + ", ".join(f"{n}×{c}" for n, c in snap["top_tools"]))
    # Hafiza istatistigi (varsa)
    try:
        from memory.smart_memory import memory_stats
        ms = memory_stats()
        lines.append(f"Hafıza: {ms['total']} kayıt, {len(ms['categories'])} kategori")
    except Exception:
        pass
    if snap["recent_tools"]:
        lines.append("Son işlemler:")
        for t, n, st in snap["recent_tools"]:
            lines.append(f"  {t}  {n}  [{st}]")
    return "\n".join(lines)
