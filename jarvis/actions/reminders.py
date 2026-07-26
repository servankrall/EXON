"""
Yerel Hatırlatıcı Yöneticisi — Windows uyumlu JSON tabanlı.
Apple Reminders + Swift EventKit helper yerine yerel JSON depolama kullanır.
Servan Kanğal tarafından yapılmıştır
Windows portu: Apple Reminders → yerel JSON hatırlatıcı sistemi
"""

from __future__ import annotations

import datetime as dt
import json
import re
import uuid
from pathlib import Path


from paths import DATA_DIR

REMINDERS_FILE = DATA_DIR / "memory" / "reminders.json"

TR_WEEKDAYS = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
TR_MONTHS = ["", "Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran",
             "Temmuz", "Agustos", "Eylul", "Ekim", "Kasim", "Aralik"]


# ── Veri erişim ──────────────────────────────────────────────────────────────

def _load_reminders() -> list[dict]:
    try:
        if REMINDERS_FILE.exists():
            data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_reminders(reminders: list[dict]) -> None:
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REMINDERS_FILE.write_text(
        json.dumps(reminders, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ── Yardımcı ─────────────────────────────────────────────────────────────────

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


def _normalize_query(query: str) -> tuple[str, int]:
    q = (query or "").strip().lower()
    if any(token in q for token in ("bugun", "today")):
        return "today", 8
    if any(token in q for token in ("geciken", "gecmis", "overdue")):
        return "overdue", 8
    if any(token in q for token in ("siradaki", "sıradaki", "next")):
        return "next", 1
    if any(token in q for token in ("hepsi", "tum", "tüm", "all", "listele")):
        return "all", 10
    return "upcoming", 8


def _day_label(when: dt.datetime, now: dt.datetime) -> str:
    today = now.date()
    target = when.date()
    if target == today:
        return "bugun"
    if target == today + dt.timedelta(days=1):
        return "yarin"
    return f"{when.day} {TR_MONTHS[when.month]} {TR_WEEKDAYS[when.weekday()]}"


def _format_due(item: dict, now: dt.datetime) -> str:
    due_iso = item.get("due_iso", "")
    if not due_iso:
        return "zaman atanmamis"
    due = _parse_iso(due_iso)
    if due is None:
        return "zaman atanmamis"
    if item.get("all_day"):
        return f"{_day_label(due, now)} tum gun"
    return f"{_day_label(due, now)} {due.strftime('%H:%M')}"


def _format_reminder_line(item: dict, now: dt.datetime) -> str:
    parts = [f"{_format_due(item, now)} - {item['title']}"]
    if item.get("list_name"):
        parts.append(f"[{item['list_name']}]")
    if item.get("priority") == "high":
        parts.append("(yuksek oncelik)")
    return " ".join(parts)


def _normalize_due_iso(due_iso: str) -> tuple[str, bool]:
    raw = (due_iso or "").strip()
    if not raw:
        return "", False

    candidates = (
        ("%Y-%m-%dT%H:%M:%S", False),
        ("%Y-%m-%dT%H:%M", False),
        ("%Y-%m-%d %H:%M:%S", False),
        ("%Y-%m-%d %H:%M", False),
        ("%d.%m.%Y %H:%M", False),
        ("%Y-%m-%d", True),
        ("%d.%m.%Y", True),
    )

    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", raw):
        try:
            parsed = dt.datetime.fromisoformat(raw)
            return parsed.isoformat(timespec="minutes"), False
        except ValueError:
            pass

    for fmt, is_all_day in candidates:
        try:
            parsed = dt.datetime.strptime(raw, fmt)
            if is_all_day:
                return parsed.date().isoformat(), True
            return parsed.isoformat(timespec="minutes"), False
        except ValueError:
            continue

    raise ValueError(
        "Hatırlatıcı tarihi geçersiz. due_iso için 'YYYY-MM-DD' veya 'YYYY-MM-DDTHH:MM' kullan."
    )


# ── Ana fonksiyonlar ──────────────────────────────────────────────────────────

def get_reminders(query: str = "upcoming", limit: int = 8, list_name: str = "") -> str:
    mode, default_limit = _normalize_query(query)
    limit = max(1, min(20, int(limit or default_limit)))
    now = dt.datetime.now()
    list_filter = (list_name or "").strip().lower()

    all_reminders = _load_reminders()
    # Tamamlanmayanları al
    open_reminders = [r for r in all_reminders if not r.get("completed", False)]

    if list_filter:
        open_reminders = [r for r in open_reminders
                          if list_filter in r.get("list_name", "").lower()]

    if mode == "today":
        today = now.date()
        filtered = []
        for r in open_reminders:
            due = _parse_iso(r.get("due_iso", ""))
            if due and due.date() == today:
                filtered.append(r)
        items = filtered[:limit]
        if not items:
            return "Bugun icin animsatici gorunmuyor."
        header = f"Bugun icin {len(items)} animsatici buldum:"

    elif mode == "overdue":
        filtered = []
        for r in open_reminders:
            due = _parse_iso(r.get("due_iso", ""))
            if due and due < now:
                filtered.append(r)
        filtered.sort(key=lambda x: x.get("due_iso", ""))
        items = filtered[:limit]
        if not items:
            return "Geciken animsatici gorunmuyor."
        header = f"Gecikmis {len(items)} animsatici buldum:"

    elif mode == "next":
        upcoming = [r for r in open_reminders if _parse_iso(r.get("due_iso", ""))]
        upcoming.sort(key=lambda x: x.get("due_iso", ""))
        future = [r for r in upcoming if _parse_iso(r["due_iso"]) >= now]
        if not future:
            return "Siradaki animsaticiyi bulamadim."
        return f"Siradaki animsatici: {_format_reminder_line(future[0], now)}."

    elif mode == "all":
        items = open_reminders[:limit]
        if not items:
            return "Kayitli acik animsatici gorunmuyor."
        header = f"Acik {len(items)} animsatici buldum:"

    else:  # upcoming
        upcoming = [r for r in open_reminders if _parse_iso(r.get("due_iso", ""))]
        upcoming.sort(key=lambda x: x.get("due_iso", ""))
        future = [r for r in upcoming if _parse_iso(r["due_iso"]) >= now]
        items = future[:limit]
        if not items:
            return "Yaklasan animsatici gorunmuyor."
        header = f"Yaklasan {len(items)} animsatici buldum:"

    lines = [header]
    for item in items:
        lines.append(f"- {_format_reminder_line(item, now)}")
    return "\n".join(lines)


def add_reminder(
    title: str,
    due_iso: str = "",
    notes: str = "",
    list_name: str = "",
    priority: str = "",
    all_day: bool = False,
) -> str:
    if not title or not title.strip():
        return "Animsatici basligi bos olamaz."

    normalized_due = ""
    normalized_all_day = bool(all_day)
    if due_iso and due_iso.strip():
        try:
            normalized_due, inferred_all_day = _normalize_due_iso(due_iso)
        except ValueError as exc:
            return str(exc)
        normalized_all_day = normalized_all_day or inferred_all_day

    reminder = {
        "id": str(uuid.uuid4()),
        "title": title.strip(),
        "due_iso": normalized_due,
        "notes": (notes or "").strip(),
        "list_name": (list_name or "").strip(),
        "priority": (priority or "").strip().lower(),
        "all_day": normalized_all_day,
        "completed": False,
    }

    reminders = _load_reminders()
    reminders.append(reminder)
    _save_reminders(reminders)

    now = dt.datetime.now()
    when = _format_due(reminder, now)
    list_suffix = f" [{reminder['list_name']}]" if reminder["list_name"] else ""
    return f"Animsatici eklendi: {when} - {reminder['title']}{list_suffix}"
