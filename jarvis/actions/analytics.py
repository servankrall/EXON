"""
Performans & Analitik.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- Akilli onbellek (TTL'li, genel amacli) — pahali islemleri tekrar etmemek icin.
- Kullanim analitigi: ozellik/arac kullanim sayaclari (yerel JSON'da kalici).
- Sistem saglik raporu: CPU/RAM/disk + EXON ic durumu.
- Baslangic/kaynak ipuclari.
Harici paket gerekmez (psutil zaten projede var).
"""

from __future__ import annotations

import json
import threading
import time
from collections import Counter

from paths import DATA_DIR

_STATS_FILE = DATA_DIR / "analytics.json"
_LOCK = threading.Lock()


# ── Akilli onbellek (TTL) ────────────────────────────────────────────────────
class TTLCache:
    """Basit, thread-guvenli, suresi dolan onbellek."""

    def __init__(self, ttl: float = 300.0, max_items: int = 256):
        self.ttl = ttl
        self.max_items = max_items
        self._data: dict = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item and (time.time() - item[0]) < self.ttl:
                self.hits += 1
                return item[1]
            if item:
                self._data.pop(key, None)
            self.misses += 1
            return None

    def put(self, key, value):
        with self._lock:
            if len(self._data) >= self.max_items:
                # en eski %20'yi at
                oldest = sorted(self._data.items(), key=lambda kv: kv[1][0])
                for k, _ in oldest[: max(1, self.max_items // 5)]:
                    self._data.pop(k, None)
            self._data[key] = (time.time(), value)

    def stats(self) -> dict:
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total else 0.0
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": round(rate, 1), "size": len(self._data)}


# Genel amacli paylasilan onbellek
CACHE = TTLCache(ttl=300.0)


# ── Kullanim analitigi (kalici) ──────────────────────────────────────────────
def _load() -> dict:
    try:
        if _STATS_FILE.exists():
            return json.loads(_STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"features": {}, "sessions": 0, "first_seen": time.time()}


def _save(data: dict) -> None:
    try:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                               encoding="utf-8")
    except Exception:
        pass


def track_feature(name: str) -> None:
    """Bir ozelligin/aracin kullanimini kalici olarak sayar."""
    with _LOCK:
        data = _load()
        feats = data.setdefault("features", {})
        feats[name] = int(feats.get(name, 0)) + 1
        _save(data)


def mark_session() -> None:
    with _LOCK:
        data = _load()
        data["sessions"] = int(data.get("sessions", 0)) + 1
        _save(data)


def usage_report(top: int = 10) -> str:
    """En cok kullanilan ozellikler + oturum sayisi."""
    data = _load()
    feats = data.get("features", {})
    if not feats:
        return "Henüz kullanım verisi toplanmadı."
    ranked = Counter(feats).most_common(top)
    lines = [f"[KULLANIM ANALİTİĞİ] (toplam oturum: {data.get('sessions', 0)})"]
    for name, cnt in ranked:
        lines.append(f"  {name}: {cnt}×")
    cs = CACHE.stats()
    lines.append(f"Önbellek: %{cs['hit_rate']} isabet ({cs['hits']}/{cs['hits']+cs['misses']})")
    return "\n".join(lines)


# ── Sistem saglik raporu ─────────────────────────────────────────────────────
def health_report() -> str:
    lines = ["[SİSTEM SAĞLIK RAPORU]"]
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        ram = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage("C:\\" if __import__("os").name == "nt" else "/")
        except Exception:
            disk = psutil.disk_usage("/")
        lines.append(f"CPU: %{cpu:.0f}")
        lines.append(f"RAM: %{ram.percent:.0f} ({ram.used // (1024**2)}/{ram.total // (1024**2)} MB)")
        lines.append(f"Disk: %{disk.percent:.0f} boş {disk.free // (1024**3)} GB")
        batt = getattr(psutil, "sensors_battery", lambda: None)()
        if batt:
            lines.append(f"Pil: %{batt.percent:.0f}" + (" (şarjda)" if batt.power_plugged else ""))
        # Basit saglik degerlendirmesi
        warns = []
        if cpu > 85:
            warns.append("CPU yüksek")
        if ram.percent > 88:
            warns.append("RAM yüksek")
        if disk.percent > 92:
            warns.append("Disk dolmak üzere")
        lines.append("Değerlendirme: " + ("⚠ " + ", ".join(warns) if warns else "Sağlıklı ✓"))
    except Exception as exc:
        lines.append(f"Sistem metrikleri alınamadı: {exc}")
    # EXON ic durumu
    try:
        from actions.dev_mode import snapshot
        snap = snapshot()
        lines.append(f"EXON çalışma süresi: {snap['uptime']}, "
                     f"araç çağrısı: {snap['tool_calls']} (hata: {snap['errors']})")
    except Exception:
        pass
    return "\n".join(lines)
