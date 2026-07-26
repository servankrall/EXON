"""
Gelismis hafiza zekasi — onem derecelendirme, cakisma tespiti, temizleme,
sikistirma ozeti ve otomatik kullanici profili.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Mevcut memory_manager.py'yi BOZMAZ; onun uzerine ek bir zeka katmanidir.
Veriler memory/memory.json icindeki kayitlara 'meta' alani ekler:
  {"value": "...", "importance": 1-5, "ts": <epoch>, "hits": <int>}
Eski (meta'siz) kayitlar da sorunsuz okunur.
"""

from __future__ import annotations

import json
import time

from memory.memory_manager import (load_memory, _write_memory, _normalize_text,
                                    _entry_value_text)


# Onem anahtar kelimeleri (kategori/anahtar/degerden puan cikarir)
_HIGH_WORDS = ("isim", "ad", "name", "dogum", "birthday", "telefon", "phone",
               "adres", "address", "email", "sifre", "allerji", "alerji",
               "saglik", "hastalik", "ilac", "acil")
_MED_WORDS = ("proje", "project", "is", "okul", "sirket", "hedef", "plan",
              "tercih", "favori", "sevdigi", "calistigi")


def _now() -> float:
    return time.time()


def score_importance(category: str, key: str, value: str) -> int:
    """Bir kaydin onemini 1-5 arasi puanlar (5 = en onemli)."""
    blob = _normalize_text(f"{category} {key} {value}")
    if category.lower() in ("identity", "kimlik"):
        return 5
    if any(w in blob for w in _HIGH_WORDS):
        return 5
    if any(w in blob for w in _MED_WORDS):
        return 3
    # Kisa notlar dusuk, uzun/aciklayici olanlar orta.
    return 2 if len(value) < 60 else 3


def _ensure_meta(entry, category: str, key: str):
    """Kaydi {value, importance, ts, hits} formatina getirir (eski kayitlari korur)."""
    if isinstance(entry, dict) and "value" in entry:
        val = entry.get("value", "")
        meta = dict(entry)
    else:
        val = entry
        meta = {"value": val}
    meta.setdefault("importance", score_importance(category, key, str(val)))
    meta.setdefault("ts", _now())
    meta.setdefault("hits", 0)
    return meta


def detect_conflicts(category: str, key: str, new_value: str) -> list[str]:
    """Yeni bilgi, ayni kategoride var olan bir kayitla CELISIYOR mu? Uyari listesi."""
    mem = load_memory()
    warnings = []
    bucket = mem.get(category)
    if isinstance(bucket, dict) and key in bucket:
        old = _entry_value_text(bucket[key]).strip()
        new = (new_value or "").strip()
        if old and new and _normalize_text(old) != _normalize_text(new):
            warnings.append(f"'{category}/{key}' eski: '{old}' -> yeni: '{new}'")
    return warnings


def remember(category: str, key: str, value: str,
             importance: int | None = None) -> dict:
    """Onem/zaman damgali kayit ekler. Cakisma varsa uyari dondurur."""
    category = (category or "notes").strip() or "notes"
    key = (key or "").strip()
    value = str(value or "").strip()
    if not key or not value:
        return {"ok": False, "msg": "key ve value gerekli."}

    conflicts = detect_conflicts(category, key, value)
    mem = load_memory()
    bucket = mem.setdefault(category, {})
    if not isinstance(bucket, dict):
        bucket = {}
        mem[category] = bucket
    imp = int(importance) if importance else score_importance(category, key, value)
    bucket[key] = {"value": value, "importance": max(1, min(5, imp)),
                   "ts": _now(), "hits": 0}
    _write_memory(mem)
    return {"ok": True, "importance": imp, "conflicts": conflicts}


def touch(category: str, key: str) -> None:
    """Bir kaydin 'kullanildi' sayacini artirir (onem icin)."""
    mem = load_memory()
    bucket = mem.get(category)
    if isinstance(bucket, dict) and key in bucket:
        entry = _ensure_meta(bucket[key], category, key)
        entry["hits"] = int(entry.get("hits", 0)) + 1
        bucket[key] = entry
        _write_memory(mem)


def cleanup_memory(max_entries_per_category: int = 40,
                   min_importance_to_keep: int = 2) -> str:
    """Eski + dusuk onemli + az kullanilan kayitlari budar (kategori basina sinir)."""
    mem = load_memory()
    removed = 0
    for category, bucket in list(mem.items()):
        if not isinstance(bucket, dict):
            continue
        # identity asla budanmaz
        if category.lower() in ("identity", "kimlik", "whatsapp_contacts"):
            continue
        scored = []
        for key, entry in bucket.items():
            meta = _ensure_meta(entry, category, key)
            # skor = onem*100 + kullanim*5 - yas(gun)
            age_days = (_now() - float(meta.get("ts", _now()))) / 86400.0
            rank = meta.get("importance", 2) * 100 + meta.get("hits", 0) * 5 - age_days
            scored.append((rank, key, meta))
        scored.sort(reverse=True)
        keep = {}
        for i, (rank, key, meta) in enumerate(scored):
            if i < max_entries_per_category and meta.get("importance", 2) >= min_importance_to_keep:
                keep[key] = meta
            else:
                removed += 1
        mem[category] = keep
    _write_memory(mem)
    return f"Hafiza temizlendi: {removed} dusuk onemli/eski kayit kaldirildi."


def compress_memory_summary(max_chars: int = 1500) -> str:
    """Tum hafizayi onem sirasina gore kisa bir ozete sikistirir (prompt icin)."""
    mem = load_memory()
    rows = []
    for category, bucket in mem.items():
        if isinstance(bucket, dict):
            for key, entry in bucket.items():
                meta = _ensure_meta(entry, category, key)
                rows.append((meta.get("importance", 2), category, key,
                             str(meta.get("value", ""))))
    rows.sort(reverse=True)  # once en onemliler
    out, total = [], 0
    for imp, cat, key, val in rows:
        line = f"- [{imp}] {cat}/{key}: {val}"
        if total + len(line) > max_chars:
            break
        out.append(line)
        total += len(line)
    if not out:
        return "Hafizada kayit yok."
    return "ONEM SIRALI HAFIZA OZETI:\n" + "\n".join(out)


def build_user_profile() -> str:
    """Hafizadan otomatik kullanici profili + ilgi alani analizi cikarir."""
    mem = load_memory()
    if not mem:
        return ("Henuz seni tanimiyorum. Konustukca ismini, ilgi alanlarini ve "
                "tercihlerini ogrenip profil olustururum.")
    identity = {}
    interests, prefs, projects, notes = [], [], [], []
    for category, bucket in mem.items():
        if not isinstance(bucket, dict):
            continue
        cl = category.lower()
        for key, entry in bucket.items():
            meta = _ensure_meta(entry, category, key)
            val = str(meta.get("value", ""))
            if cl in ("identity", "kimlik"):
                identity[key] = val
            elif cl in ("interests", "ilgi", "ilgi_alanlari"):
                interests.append(val)
            elif cl in ("preferences", "tercihler"):
                prefs.append(f"{key}: {val}")
            elif cl in ("projects", "projeler"):
                projects.append(val)
            else:
                notes.append(f"{key}: {val}")

    parts = ["[OTOMATIK KULLANICI PROFILI]"]
    if identity:
        parts.append("Kimlik: " + ", ".join(f"{k}={v}" for k, v in identity.items()))
    if interests:
        parts.append("Ilgi alanlari: " + ", ".join(interests[:10]))
    if prefs:
        parts.append("Tercihler: " + "; ".join(prefs[:10]))
    if projects:
        parts.append("Projeler: " + ", ".join(projects[:8]))
    if notes:
        parts.append("Diger notlar: " + "; ".join(notes[:8]))
    if len(parts) == 1:
        return "Seninle ilgili henuz yeterli bilgi toplamadim."
    return "\n".join(parts)


def memory_stats() -> dict:
    """Gelistirici modu icin hafiza istatistikleri."""
    mem = load_memory()
    total = 0
    by_cat = {}
    by_imp = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for category, bucket in mem.items():
        if isinstance(bucket, dict):
            by_cat[category] = len(bucket)
            for key, entry in bucket.items():
                total += 1
                meta = _ensure_meta(entry, category, key)
                imp = max(1, min(5, int(meta.get("importance", 2))))
                by_imp[imp] += 1
    return {"total": total, "categories": by_cat, "by_importance": by_imp}
