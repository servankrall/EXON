"""
EXON Pro — lisans yonetimi.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

IKI YONTEM (ikisi de para'yi sana getirir; Gumroad/Shopier sadece ODEME alir):

A) KOLAY — Cevrimdisi imzali anahtar (Gumroad'in lisans ozelligi GEREKMEZ):
   - 'python make_license.py yearly' ile anahtar uretirsin (aylik/yillik/omurluk).
   - Gumroad/Shopier'de normal urun satarsin; alici'ya urettigin anahtari verirsin
     (Gumroad satis sonrasi 'content' alanina yazabilir veya e-posta atarsin).
   - Alici anahtari girer; EXON cevrimdisi dogrular (aylik/yillik icin son kullanma tarihli).

B) GELISMIS — Gumroad uyelik + lisans dogrulama (otomatik, iptal edilince kapanir):
   - config'e gumroad_product_id veya gumroad_product_permalink koyarsin.
   - Gumroad lisans anahtarlarini API ile dogrularis (abonelik bitince Pro kapanir).

Ayrintilar: PRO_KURULUM.md
"""

from __future__ import annotations

import hashlib
import hmac
import time

import requests

from app_config import get_app_config_value, save_app_config


# Pro'ya ozel arac isimleri — main.py bu kapiyi tutar.
PRO_TOOLS = {
    "generate_image", "compose_song", "get_news_briefing", "get_stock_price",
    "read_emails", "send_email", "read_code_file", "list_code_files",
    "search_in_code", "write_code_file", "set_performance_mode",
    "analyze_screen", "get_youtube_channel_report",
    "compose_text", "summarize_url", "summarize_document",
    "learn_file", "learn_text", "knowledge_query", "knowledge_search",
}

PRO_FEATURES_TR = [
    "Sinirsiz gorsel olusturma",
    "Sarki yazma & soyleme (ritimli, tonlu)",
    "Kod asistani (oku / ara / duzelt / yaz)",
    "Metin yazarligi (e-posta, blog, sosyal medya)",
    "Web sayfasi & dokuman ozetleme",
    "Borsa & hisse fiyatlari",
    "Gunluk haber brifingi",
    "E-posta okuma & gonderme",
    "Oyun modu (performans yukseltme)",
    "Ekran analizi (gorsel zeka)",
    "YouTube kanal analizi",
]

PLANS = {
    "monthly":  {"label": "Aylik",   "price": "$2 / ay"},
    "yearly":   {"label": "Yillik",  "price": "$10 / yil"},
    "lifetime": {"label": "Omurluk", "price": "tek seferlik"},
}

# Cevrimdisi anahtar imzasi (kodda gomulu — teknik olmayan kullanicilara karsi korur).
# Istersen config'e "license_secret" koyarak degistirebilirsin (tum kopyalarda ayni olmali).
_DEFAULT_SECRET = "EXON-ROBOTIK-b7Q2x9Lm4Vt8KpZ"
_PLAN_CODE = {"monthly": "M", "yearly": "Y", "lifetime": "L"}
_CODE_PLAN = {"M": "monthly", "Y": "yearly", "L": "lifetime"}
_PLAN_DAYS = {"monthly": 30, "yearly": 365, "lifetime": 0}

_cache: bool | None = None


# ── Cevrimdisi imzali anahtar ────────────────────────────────────────────────
def _secret() -> str:
    return str(get_app_config_value("license_secret", "") or _DEFAULT_SECRET)


def _today_days() -> int:
    return int(time.time() // 86400)


def _sign(body: str) -> str:
    return hmac.new(_secret().encode(), body.encode(),
                    hashlib.sha256).hexdigest()[:10].upper()


def generate_key(plan: str = "yearly", days: int | None = None) -> str:
    """Imzali bir lisans anahtari uretir. plan: monthly | yearly | lifetime."""
    plan = (plan or "yearly").lower()
    code = _PLAN_CODE.get(plan, "Y")
    if days is None:
        days = _PLAN_DAYS.get(plan, 365)
    exp = 0 if (code == "L" or int(days) == 0) else _today_days() + int(days)
    body = f"{code}{exp}"
    return f"EXON-{code}-{exp}-{_sign(body)}"


def _verify_offline(key: str):
    """True=gecerli, False=gecersiz/suresi dolmus."""
    parts = (key or "").strip().upper().split("-")
    if len(parts) != 4 or parts[0] != "EXON":
        return False
    code, exp_s, sig = parts[1], parts[2], parts[3]
    if code not in _CODE_PLAN or not exp_s.isdigit():
        return False
    if _sign(f"{code}{exp_s}") != sig:
        return False
    exp = int(exp_s)
    if exp != 0 and _today_days() > exp:
        return False
    save_app_config({"pro_plan": _CODE_PLAN[code]})
    return True


# ── Gumroad (opsiyonel, gelismis) ────────────────────────────────────────────
def _gumroad_configured() -> bool:
    return bool(str(get_app_config_value("gumroad_product_id", "") or "").strip()
                or str(get_app_config_value("gumroad_product_permalink", "") or "").strip())


def _verify_gumroad(key: str):
    """True=aktif, False=gecersiz/iade/abonelik bitti, 'neterror'=internet yok."""
    product_id = str(get_app_config_value("gumroad_product_id", "") or "").strip()
    permalink = str(get_app_config_value("gumroad_product_permalink", "") or "").strip()
    try:
        data = {"license_key": (key or "").strip(), "increment_uses_count": "false"}
        if product_id:
            data["product_id"] = product_id
        else:
            data["product_permalink"] = permalink
        r = requests.post("https://api.gumroad.com/v2/licenses/verify",
                          data=data, timeout=10)
        if r.status_code != 200:
            return False
        body = r.json()
        if not body.get("success"):
            return False
        purchase = body.get("purchase", {}) or {}
        if (purchase.get("refunded") or purchase.get("chargebacked")
                or purchase.get("disputed")):
            return False
        if purchase.get("subscription_ended_at") or purchase.get("subscription_failed_at"):
            return False
        rec = purchase.get("recurrence")
        if rec:
            save_app_config({"pro_plan": rec})
        return True
    except Exception:
        return "neterror"


# ── Ortak ────────────────────────────────────────────────────────────────────
def _verify_key(key: str):
    if _gumroad_configured():
        return _verify_gumroad(key)   # True / False / 'neterror'
    return _verify_offline(key)        # True / False


def get_purchase_url(plan: str = "") -> str:
    """Plana ozel link > genel link > Gumroad permalink'ten kurulan link. Yoksa BOS."""
    plan = (plan or "").lower()
    url = ""
    if plan == "monthly":
        url = get_app_config_value("pro_purchase_url_monthly", "")
    elif plan == "yearly":
        url = get_app_config_value("pro_purchase_url_yearly", "")
    url = str(url or "").strip()
    if url:
        return url
    general = str(get_app_config_value("pro_purchase_url", "") or "").strip()
    if general:
        return general
    permalink = str(get_app_config_value("gumroad_product_permalink", "") or "").strip()
    if permalink:
        if permalink.startswith(("http://", "https://")):
            return permalink
        return f"https://gumroad.com/l/{permalink}"
    return ""


def _compute_pro() -> bool:
    key = str(get_app_config_value("license_key", "") or "").strip()
    if not key:
        return bool(get_app_config_value("pro_active", False))
    res = _verify_key(key)
    if res == "neterror":
        return bool(get_app_config_value("pro_active", False))
    if res is True:
        save_app_config({"pro_active": True})
        return True
    save_app_config({"pro_active": False})
    return False


def is_pro() -> bool:
    global _cache
    if _cache is None:
        _cache = _compute_pro()
    return _cache


def refresh() -> bool:
    global _cache
    _cache = _compute_pro()
    return _cache


def current_plan_label() -> str:
    plan = str(get_app_config_value("pro_plan", "") or "").lower()
    return PLANS.get(plan, {}).get("label", "")


def activate_license(key: str):
    """Anahtari dogrular ve kaydeder. (ok: bool, mesaj: str) doner."""
    global _cache
    key = (key or "").strip()
    if not key:
        return False, "Lisans anahtari bos olamaz."
    res = _verify_key(key)
    if res is True:
        save_app_config({"license_key": key, "pro_active": True})
        _cache = True
        label = current_plan_label()
        extra = f" ({label} plan)" if label else ""
        return True, f"EXON Pro etkinlestirildi!{extra} Tesekkurler."
    if res == "neterror":
        save_app_config({"license_key": key, "pro_active": True})
        _cache = True
        return True, "Lisans kaydedildi (cevrimici dogrulama internet gelince yapilacak)."
    return False, "Lisans anahtari gecersiz veya suresi dolmus."


def deactivate():
    global _cache
    save_app_config({"pro_active": False, "license_key": ""})
    _cache = False


if __name__ == "__main__":
    import sys
    _plan = sys.argv[1] if len(sys.argv) > 1 else "yearly"
    _days = int(sys.argv[2]) if len(sys.argv) > 2 else None
    print(generate_key(_plan, _days))
