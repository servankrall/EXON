"""
Sağlık Verisi — Windows uyumlu.
Apple Watch / iPhone sağlık verisi iCloud üzerinden yalnızca macOS'ta erişilebilir.
Windows'ta alternatif veri kaynakları için yönlendirme yapılır.
Servan Kanğal tarafından yapılmıştır
Windows portu: iCloud sağlık verisi → bilgi mesajı + yerel JSON fallback
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from paths import DATA_DIR

# Windows'ta alternatif sağlık verisi kaynağı (manuel JSON)
HEALTH_DIR = DATA_DIR / "memory" / "health"
_MANUAL_FILE = HEALTH_DIR / "health_data.json"

STALE_WARN_MINUTES = 120


def _normalize_query(text: str) -> str:
    text = (text or "").strip().lower()
    return (
        text.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )


def _extract_target_date(query: str) -> date | None:
    q = _normalize_query(query)
    today = date.today()
    if any(token in q for token in ("dun", "yesterday")):
        return today - timedelta(days=1)
    if any(token in q for token in ("bugun", "today", "simdi")):
        return today
    iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", q)
    if iso_match:
        try:
            return datetime.strptime(iso_match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def _load_manual_data() -> tuple[dict, float] | None:
    """Manuel olarak yerleştirilen JSON sağlık verisini okur."""
    try:
        if _MANUAL_FILE.exists():
            data = json.loads(_MANUAL_FILE.read_text(encoding="utf-8"))
            ts = _MANUAL_FILE.stat().st_mtime
            return data, ts
    except Exception:
        pass
    return None


def _age_str(ts: float) -> str:
    mins = (time.time() - ts) / 60
    if mins < 2:
        return "az önce"
    if mins < 60:
        return f"{int(mins)} dakika önce"
    hrs = mins / 60
    if hrs < 24:
        return f"{hrs:.1f} saat önce"
    return f"{hrs/24:.1f} gün önce"


def _v(d: dict, key: str, unit: str = "", dec: int = 0) -> str:
    val = d.get(key)
    if val is None:
        return "—"
    try:
        f = float(val)
        return f"{f:.{dec}f}{unit}" if dec else f"{int(round(f))}{unit}"
    except (ValueError, TypeError):
        return str(val)


def _format_manual(data: dict, query: str, age: str) -> str:
    q = _normalize_query(query)

    if any(k in q for k in ("nabız", "nabiz", "kalp", "heart", "bpm", "hrv")):
        return "\n".join([
            f"Anlık nabız    : {_v(data, 'heart_rate', ' bpm')}",
            f"Dinlenim nabzı : {_v(data, 'resting_hr', ' bpm')}",
            f"HRV            : {_v(data, 'hrv', ' ms', 1)}",
            f"[güncelleme: {age}]",
        ])

    if any(k in q for k in ("adım", "step", "egzersiz", "exercise", "kalori", "aktivite")):
        return "\n".join([
            f"Bugün adım     : {_v(data, 'steps')}",
            f"Aktif kalori   : {_v(data, 'calories', ' kcal')}",
            f"Egzersiz süresi: {_v(data, 'exercise_min', ' dk')}",
            f"Mesafe         : {_v(data, 'walking_distance_km', ' km', 2)}",
            f"[güncelleme: {age}]",
        ])

    return "\n".join([
        "── SAĞLIK ÖZETİ ──────────────────",
        f"💓 Nabız         : {_v(data, 'heart_rate', ' bpm')}  (din.: {_v(data, 'resting_hr', ' bpm')})",
        f"📊 HRV           : {_v(data, 'hrv', ' ms', 1)}",
        f"🩸 Kan oksijeni  : {_v(data, 'blood_oxygen', '%', 1)}",
        f"👣 Adım          : {_v(data, 'steps')}",
        f"🔥 Aktif kalori  : {_v(data, 'calories', ' kcal')}",
        f"🏃 Egzersiz      : {_v(data, 'exercise_min', ' dk')}",
        f"💤 Uyku          : {_v(data, 'sleep_hours', ' saat', 1)}",
        f"──────────────────────────────────",
        f"[güncelleme: {age}]",
    ])


_WINDOWS_HEALTH_NOTE = (
    "Apple Watch / iPhone sağlık verisi yalnızca macOS iCloud üzerinden erişilebilir. "
    "Windows'ta sağlık verisi kullanmak için:\n"
    "1. Sağlık verilerini JSON formatında dışa aktar (Health Auto Export gibi bir uygulama)\n"
    f"2. '{_MANUAL_FILE}' konumuna 'health_data.json' olarak kaydet\n"
    "3. Format: {{\"heart_rate\": 72, \"steps\": 8000, \"calories\": 450, "
    "\"sleep_hours\": 7.5, \"resting_hr\": 60, \"hrv\": 45, \"blood_oxygen\": 98.5}}"
)


def get_health_data(query: str = "all") -> str:
    # Manuel JSON verisi varsa kullan
    result = _load_manual_data()
    if result:
        data, ts = result
        if data:
            age = _age_str(ts)
            formatted = _format_manual(data, query, age)
            mins_old = (time.time() - ts) / 60
            if mins_old > STALE_WARN_MINUTES:
                formatted += f"\n⚠️  Veri {age} güncellendi — health_data.json dosyasını güncelle."
            return formatted

    return _WINDOWS_HEALTH_NOTE


def get_welcome_health_summary() -> str:
    result = _load_manual_data()
    if result:
        data, ts = result
        if data:
            heart_rate = _v(data, "heart_rate", " bpm")
            steps = _v(data, "steps")
            parts = []
            if heart_rate != "—":
                parts.append(f"Kalp atışın {heart_rate}")
            if steps != "—":
                parts.append(f"{steps} adım attın")
            if parts:
                return ", ".join(parts) + "."
    return "Sağlık verilerin şu anda alınamadı (Windows'ta manuel JSON gerekli)."
