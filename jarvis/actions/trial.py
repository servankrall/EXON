"""
Free deneme sistemi — duygu modu ve gorsel yuklemeden kisa sureli ucretsiz yararlanma.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Pro kullanici: sinirsiz. Free kullanici: gunde sinirli sure/adet.
Veriler config'te (gun bazli) tutulur. Pro kontrolu license_manager'dan gelir.
"""

from __future__ import annotations

import time

from app_config import get_app_config_value, save_app_config

# Free limitleri
EMOTION_TRIAL_SECONDS = 600    # gunde 10 dakika duygu modu
IMAGE_TRIAL_PER_DAY   = 3      # gunde 3 gorsel yukleme


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def _data() -> dict:
    raw = get_app_config_value("trial_data", {}) or {}
    return raw if isinstance(raw, dict) else {}


def _save(d: dict) -> None:
    save_app_config({"trial_data": d})


def _is_pro() -> bool:
    try:
        from actions.license_manager import is_pro
        return is_pro()
    except Exception:
        return False


# ── Duygu modu denemesi ──────────────────────────────────────────────────────
def emotion_remaining() -> float:
    """Free kullanici icin bugun kalan duygu modu suresi (saniye). Pro -> sonsuz."""
    if _is_pro():
        return float("inf")
    d = _data()
    used = float(d.get("emotion_used", 0)) if d.get("emotion_day") == _today() else 0.0
    rem = EMOTION_TRIAL_SECONDS - used
    # Aktif oturum varsa onu da dus
    start = d.get("emotion_start")
    if start:
        rem -= max(0.0, time.time() - float(start))
    return max(0.0, rem)


def begin_emotion() -> tuple[bool, str]:
    """Duygu modu acilirken cagrilir. (izin, mesaj)."""
    if _is_pro():
        return True, ""
    rem = emotion_remaining()
    if rem <= 0:
        return False, ("Ücretsiz duygu modu denemen bugünlük doldu. "
                       "Sınırsız için EXON Pro'ya geç.")
    d = _data()
    d["emotion_day"] = _today()
    d.setdefault("emotion_used", 0 if d.get("emotion_day") == _today() else 0)
    d["emotion_start"] = time.time()
    _save(d)
    mins = int(rem // 60)
    return True, f"Deneme: bugün ~{mins} dk duygu modu hakkın kaldı."


def end_emotion() -> None:
    """Duygu modu kapanirken cagrilir; kullanilan sureyi kaydeder."""
    if _is_pro():
        return
    d = _data()
    start = d.get("emotion_start")
    if start:
        used = float(d.get("emotion_used", 0)) if d.get("emotion_day") == _today() else 0.0
        d["emotion_day"] = _today()
        d["emotion_used"] = used + max(0.0, time.time() - float(start))
        d.pop("emotion_start", None)
        _save(d)


def emotion_expired() -> bool:
    """Free oturumda sure doldu mu (periyodik kontrol icin)."""
    if _is_pro():
        return False
    return emotion_remaining() <= 0


# ── Gorsel yukleme denemesi ──────────────────────────────────────────────────
def image_remaining() -> int:
    if _is_pro():
        return 9999
    d = _data()
    used = int(d.get("image_used", 0)) if d.get("image_day") == _today() else 0
    return max(0, IMAGE_TRIAL_PER_DAY - used)


def image_allowed() -> bool:
    return _is_pro() or image_remaining() > 0


def consume_image() -> None:
    """Bir gorsel yukleme hakkini kullanir (free icin)."""
    if _is_pro():
        return
    d = _data()
    used = int(d.get("image_used", 0)) if d.get("image_day") == _today() else 0
    d["image_day"] = _today()
    d["image_used"] = used + 1
    _save(d)
