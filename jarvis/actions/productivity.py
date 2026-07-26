"""
Uretkenlik+ paketi — yapilacaklar, hizli not, tarih hesabi, dunya saati, QR.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition
Veriler memory/ altinda JSON; QR icin qrcode varsa gorsel, yoksa link.
"""

from __future__ import annotations

import datetime
import json
import urllib.parse
from pathlib import Path

from paths import DATA_DIR

_TODO_FILE = DATA_DIR / "memory" / "todo.json"
_NOTES_FILE = DATA_DIR / "memory" / "quick_notes.json"


def _load(path: Path) -> list:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Yapilacaklar listesi ─────────────────────────────────────────────────────
def todo_action(action: str = "list", item: str = "", index: int = 0) -> str:
    """Yapilacaklar: add, list, done, remove, clear."""
    action = (action or "list").lower().strip()
    todos = _load(_TODO_FILE)
    if action == "add":
        if not item.strip():
            return "Ne eklemek istersin?"
        todos.append({"text": item.strip(), "done": False})
        _save(_TODO_FILE, todos)
        return f"✅ Eklendi: {item.strip()} (toplam {len(todos)})"
    if action in ("done", "tamam"):
        try:
            i = int(index) - 1
            todos[i]["done"] = True
            _save(_TODO_FILE, todos)
            return f"✔️ Tamamlandı: {todos[i]['text']}"
        except Exception:
            return "Geçerli bir sıra numarası ver."
    if action in ("remove", "sil"):
        try:
            i = int(index) - 1
            t = todos.pop(i)
            _save(_TODO_FILE, todos)
            return f"🗑️ Silindi: {t['text']}"
        except Exception:
            return "Geçerli bir sıra numarası ver."
    if action in ("clear", "temizle"):
        _save(_TODO_FILE, [])
        return "Liste temizlendi."
    # list
    if not todos:
        return "Yapılacaklar listen boş. 'ekle: ...' diyerek ekleyebilirsin."
    lines = ["📋 YAPILACAKLAR:"]
    for i, t in enumerate(todos, 1):
        mark = "✔️" if t.get("done") else "⬜"
        lines.append(f"  {i}. {mark} {t['text']}")
    return "\n".join(lines)


# ── Hizli not ────────────────────────────────────────────────────────────────
def quick_note(action: str = "list", text: str = "") -> str:
    """Hizli not: add, list, clear."""
    action = (action or "list").lower().strip()
    notes = _load(_NOTES_FILE)
    if action == "add":
        if not text.strip():
            return "Ne not almak istersin?"
        notes.append({"text": text.strip(),
                      "ts": datetime.datetime.now().strftime("%d.%m %H:%M")})
        _save(_NOTES_FILE, notes)
        return f"📝 Not alındı: {text.strip()}"
    if action in ("clear", "temizle"):
        _save(_NOTES_FILE, [])
        return "Notlar temizlendi."
    if not notes:
        return "Hiç notun yok."
    lines = ["📝 NOTLARIN:"]
    for n in notes[-15:]:
        lines.append(f"  • [{n.get('ts','')}] {n['text']}")
    return "\n".join(lines)


# ── Tarih hesabi ─────────────────────────────────────────────────────────────
def date_diff(target_date: str = "", label: str = "") -> str:
    """Verilen tarihe kac gun kaldigini/gectigini hesaplar. Format: GG.AA.YYYY veya YYYY-AA-GG."""
    target_date = (target_date or "").strip()
    if not target_date:
        return "Bir tarih ver (örn. 31.12.2026)."
    dt = None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            dt = datetime.datetime.strptime(target_date, fmt).date()
            break
        except ValueError:
            continue
    if not dt:
        return "Tarihi anlayamadım. Örnek: 31.12.2026"
    today = datetime.date.today()
    diff = (dt - today).days
    name = label or target_date
    if diff > 0:
        return f"📅 {name} için {diff} gün kaldı (~{diff//7} hafta)."
    if diff < 0:
        return f"📅 {name} tarihinin üzerinden {-diff} gün geçti."
    return f"📅 {name} bugün! 🎉"


def days_between(date1: str, date2: str) -> str:
    """Iki tarih arasindaki gun sayisi."""
    def _p(s):
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(s.strip(), fmt).date()
            except ValueError:
                continue
        return None
    d1, d2 = _p(date1), _p(date2)
    if not d1 or not d2:
        return "İki geçerli tarih ver (GG.AA.YYYY)."
    return f"İki tarih arası: {abs((d2-d1).days)} gün."


# ── Dunya saati ──────────────────────────────────────────────────────────────
_TZ_OFFSETS = {
    "istanbul": 3, "turkiye": 3, "ankara": 3, "londra": 0, "london": 0,
    "newyork": -5, "new york": -5, "ny": -5, "tokyo": 9, "tokio": 9,
    "berlin": 1, "paris": 1, "moskova": 3, "moscow": 3, "dubai": 4,
    "los angeles": -8, "la": -8, "sydney": 11, "pekin": 8, "beijing": 8,
}


def world_time(city: str = "istanbul") -> str:
    """Bir sehrin yaklasik yerel saatini soyler (UTC ofseti ile)."""
    c = (city or "istanbul").lower().strip()
    off = _TZ_OFFSETS.get(c)
    if off is None:
        return (f"'{city}' için saat dilimini bilmiyorum. "
                "Bilinen: İstanbul, Londra, New York, Tokyo, Berlin, Dubai, LA, Sydney...")
    utc = datetime.datetime.utcnow()
    local = utc + datetime.timedelta(hours=off)
    return f"🕐 {city.title()} saati: {local.strftime('%H:%M')} (UTC{off:+d})"


# ── QR kod ───────────────────────────────────────────────────────────────────
def make_qr(text: str) -> str:
    """Metin/URL icin QR kod uretir. qrcode varsa PNG kaydeder, yoksa online link verir."""
    text = (text or "").strip()
    if not text:
        return "QR için bir metin/URL ver."
    try:
        import qrcode
        out = DATA_DIR / "generated_images"
        out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = out / f"qr_{stamp}.png"
        qrcode.make(text).save(str(path))
        return f"📱 QR kod oluşturuldu: {path}"
    except Exception:
        url = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" + urllib.parse.quote(text)
        return f"📱 QR kod (tarayıcıda aç): {url}"
