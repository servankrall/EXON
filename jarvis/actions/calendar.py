"""
Yerel Takvim Yöneticisi — Windows uyumlu JSON tabanlı.
Apple Calendar + Swift EventKit helper yerine yerel JSON depolama kullanır.
Servan Kanğal tarafından yapılmıştır
Windows portu: Apple Calendar → yerel JSON takvim
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CALENDAR_FILE = BASE_DIR / "memory" / "calendar.json"

TR_WEEKDAYS = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
TR_MONTHS = ["", "Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran",
             "Temmuz", "Agustos", "Eylul", "Ekim", "Kasim", "Aralik"]


# ── Veri erişim ──────────────────────────────────────────────────────────────

def _load_events() -> list[dict]:
    try:
        if CALENDAR_FILE.exists():
            data = json.loads(CALENDAR_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_events(events: list[dict]) -> None:
    CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_FILE.write_text(
        json.dumps(events, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _month_start(value: dt.datetime) -> dt.datetime:
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_months(value: dt.datetime, months: int) -> dt.datetime:
    total = (value.year * 12 + (value.month - 1)) + months
    year = total // 12
    month = total % 12 + 1
    return value.replace(year=year, month=month, day=1)


# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _day_label(when: dt.datetime, now: dt.datetime) -> str:
    today = now.date()
    target = when.date()
    if target == today:
        return "bugun"
    if target == today + dt.timedelta(days=1):
        return "yarin"
    return f"{when.day} {TR_MONTHS[when.month]} {TR_WEEKDAYS[when.weekday()]}"


def _format_time_range(event: dict, now: dt.datetime) -> str:
    start = dt.datetime.fromisoformat(event["start_iso"])
    end = dt.datetime.fromisoformat(event["end_iso"])
    prefix = _day_label(start, now)
    if event.get("all_day"):
        return f"{prefix} tum gun"
    return f"{prefix} {start.strftime('%H:%M')}-{end.strftime('%H:%M')}"


def _format_event_line(event: dict, now: dt.datetime) -> str:
    pieces = [f"{_format_time_range(event, now)} - {event['title']}"]
    cal = event.get("calendar_name", "")
    if cal:
        pieces.append(f"[{cal}]")
    loc = event.get("location", "")
    if loc:
        pieces.append(f"@ {loc}")
    return " ".join(pieces)


def _parse_iso(iso_str: str) -> dt.datetime | None:
    if not iso_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(iso_str.strip(), fmt)
        except ValueError:
            continue
    try:
        return dt.datetime.fromisoformat(iso_str.strip())
    except ValueError:
        return None


def _normalize_query(query: str) -> tuple[str, dt.datetime, dt.datetime, str, str]:
    """(mode, start, end, header_template, empty_msg) döndürür."""
    q = (query or "today").strip().lower()
    now = dt.datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + dt.timedelta(days=1)

    month_match = re.search(r"(\d+)\s*(ay|month|months)", q)
    if "gelecek ay" in q or "önümüzdeki ay" in q or "onumuzdeki ay" in q or "next month" in q:
        start = _add_months(_month_start(now), 1)
        end = _add_months(start, 1)
        return "range", start, end, "Gelecek ay icin {count} etkinlik buldum:", "Gelecek ay takviminde etkinlik gorunmuyor."
    if "bu ay" in q or "this month" in q:
        start = _month_start(now)
        end = _add_months(start, 1)
        return "range", start, end, "Bu ay icin {count} etkinlik buldum:", "Bu ay takviminde etkinlik gorunmuyor."
    if month_match:
        months = max(1, min(12, int(month_match.group(1))))
        return "range", today_start, _add_months(_month_start(now), months), \
               f"Onumuzdeki {months} ay icin {{count}} etkinlik buldum:", \
               f"Onumuzdeki {months} ayda takviminde etkinlik gorunmuyor."

    week_match = re.search(r"(\d+)\s*(hafta|week|weeks)", q)
    if week_match:
        weeks = max(1, min(12, int(week_match.group(1))))
        return "range", today_start, today_start + dt.timedelta(days=weeks * 7), \
               f"Onumuzdeki {weeks} hafta icin {{count}} etkinlik buldum:", \
               f"Onumuzdeki {weeks} haftada takviminde etkinlik gorunmuyor."

    day_match = re.search(r"(\d+)\s*(g[uü]n|gun|day|days)", q)
    if day_match:
        days = max(1, min(365, int(day_match.group(1))))
        return "range", today_start, today_start + dt.timedelta(days=days), \
               f"Onumuzdeki {days} gun icin {{count}} etkinlik buldum:", \
               f"Onumuzdeki {days} gunde takviminde etkinlik gorunmuyor."

    if any(t in q for t in ("yarin", "tomorrow")):
        start = today_start + dt.timedelta(days=1)
        return "range", start, start + dt.timedelta(days=1), \
               "Yarin icin {count} etkinlik buldum:", "Yarin takviminde etkinlik gorunmuyor."

    if any(t in q for t in ("hafta", "week", "7 gun")):
        return "range", today_start, today_start + dt.timedelta(days=7), \
               "Onumuzdeki 7 gun icin {count} etkinlik buldum:", "Onumuzdeki 7 gunde takviminde etkinlik gorunmuyor."

    if any(t in q for t in ("siradaki", "sıradaki", "sonraki", "next")):
        return "next", now, now + dt.timedelta(days=365), "", "Siradaki takvim etkinligini bulamadim."

    if any(t in q for t in ("ajanda", "agenda", "yaklasan", "yaklaşan", "upcoming")):
        return "range", now, now + dt.timedelta(days=30), \
               "Yaklasan ajandanda {count} etkinlik var:", "Yaklasan takvim etkinligi gorunmuyor."

    # today
    return "range", today_start, today_end, \
           "Bugun icin {count} etkinlik buldum:", "Bugun takviminde etkinlik gorunmuyor."


# ── Ana fonksiyonlar ──────────────────────────────────────────────────────────

def get_calendar_events(query: str = "today", limit: int = 6) -> str:
    mode, start, end, header_tpl, empty_msg = _normalize_query(query)
    limit = max(1, min(60, int(limit or 6)))
    now = dt.datetime.now()

    events = _load_events()
    # Filtrele: start_iso ve end_iso aralığına göre
    matching = []
    for ev in events:
        ev_start = _parse_iso(ev.get("start_iso", ""))
        ev_end = _parse_iso(ev.get("end_iso", ""))
        if ev_start is None or ev_end is None:
            continue
        if ev_end < start or ev_start > end:
            continue
        if mode in {"next", "agenda"} and ev_end < now:
            continue
        matching.append(ev)

    matching.sort(key=lambda e: e.get("start_iso", ""))

    if not matching:
        return empty_msg

    if mode == "next":
        return f"Siradaki etkinlik: {_format_event_line(matching[0], now)}."

    selected = matching[:limit]
    header = header_tpl.format(count=len(selected))
    lines = [header]
    for ev in selected:
        lines.append(f"- {_format_event_line(ev, now)}")
    return "\n".join(lines)


def add_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str = "",
    notes: str = "",
    location: str = "",
    calendar_name: str = "",
    all_day: bool = False,
) -> str:
    title = (title or "").strip()
    start_iso = (start_iso or "").strip()
    if not title:
        return "Takvime eklemek icin etkinlik basligi gerekli."
    if not start_iso:
        return "Takvime eklemek icin baslangic tarihi gerekli."

    start_dt = _parse_iso(start_iso)
    if not start_dt:
        return f"Geçersiz başlangıç tarihi formatı: {start_iso}"

    # Bitiş tarihi belirtilmemişse +1 saat ekle (tüm gün değilse)
    if end_iso and end_iso.strip():
        end_dt = _parse_iso(end_iso.strip())
        if not end_dt:
            end_dt = start_dt + dt.timedelta(hours=1)
    else:
        if all_day:
            end_dt = start_dt + dt.timedelta(days=1)
        else:
            end_dt = start_dt + dt.timedelta(hours=1)

    event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "start_iso": start_dt.isoformat(),
        "end_iso": end_dt.isoformat(),
        "notes": (notes or "").strip(),
        "location": (location or "").strip(),
        "calendar_name": (calendar_name or "").strip(),
        "all_day": bool(all_day),
    }

    events = _load_events()
    events.append(event)
    _save_events(events)

    now = dt.datetime.now()
    line = _format_event_line(event, now)
    return f"Takvime eklendi: {line}."


def delete_calendar_event(
    title: str,
    start_iso: str = "",
    calendar_name: str = "",
    delete_all_matches: bool = False,
) -> str:
    title = (title or "").strip()
    if not title:
        return "Takvimden silmek icin etkinlik basligi gerekli."

    events = _load_events()
    title_lower = title.lower()
    start_dt = _parse_iso(start_iso) if start_iso else None
    cal_filter = (calendar_name or "").strip().lower()

    matched = []
    for ev in events:
        ev_title_lower = ev.get("title", "").lower()
        if title_lower not in ev_title_lower:
            continue
        if start_dt:
            ev_start = _parse_iso(ev.get("start_iso", ""))
            if ev_start is None:
                continue
            # Tarihler yakın mı? (aynı gün kabul et)
            if abs((ev_start - start_dt).total_seconds()) > 86400:
                continue
        if cal_filter:
            ev_cal = ev.get("calendar_name", "").lower()
            if cal_filter not in ev_cal:
                continue
        matched.append(ev)

    if not matched:
        return f"'{title}' başlıklı bir etkinlik bulunamadı."

    if len(matched) > 1 and not delete_all_matches:
        now = dt.datetime.now()
        options = [_format_event_line(ev, now) for ev in matched[:3]]
        return (
            f"'{title}' başlıklı {len(matched)} etkinlik bulundu. "
            f"Hangisini silmek istiyorsun? Seçenekler:\n"
            + "\n".join(f"- {opt}" for opt in options)
        )

    now = dt.datetime.now()
    if delete_all_matches:
        deleted_ids = {ev["id"] for ev in matched}
        events = [ev for ev in events if ev.get("id") not in deleted_ids]
        _save_events(events)
        return f"'{title}' başlıklı {len(matched)} etkinlik takvimden silindi."

    # İlk eşleşeni sil
    to_delete = matched[0]
    events = [ev for ev in events if ev.get("id") != to_delete.get("id")]
    _save_events(events)
    line = _format_event_line(to_delete, now)
    return f"Takvimden silindi: {line}."
