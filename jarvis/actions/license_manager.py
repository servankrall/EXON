"""
EXON Pro — lisans/abonelik yonetimi.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Para akisi (backend GEREKMEZ): satici (sen) Gumroad'da bir urun acar, fiyat koyar.
Her alici otomatik bir LISANS ANAHTARI alir; para SENIN Gumroad hesabina gecer.
Uygulama, anahtari Gumroad'in ucretsiz lisans dogrulama API'siyle kontrol eder.

config/api_keys.json icine:
  "pro_purchase_url": "https://<seninhesap>.gumroad.com/l/exon-pro",
  "gumroad_product_id": "<urun_id>"           (veya)
  "gumroad_product_permalink": "<permalink>"
Ayrintilar: PRO_KURULUM.md
"""

from __future__ import annotations

import requests

from app_config import get_app_config_value, save_app_config


# Pro'ya ozel arac isimleri — main.py bu kapiyi tutar (Free kullanici cagirinca upsell doner).
PRO_TOOLS = {
    "generate_image", "compose_song", "get_news_briefing", "get_stock_price",
    "read_emails", "send_email", "read_code_file", "list_code_files",
    "search_in_code", "write_code_file", "set_performance_mode",
    "analyze_screen", "get_youtube_channel_report",
}

# Pro tanitim ekraninda gosterilecek ozellikler
PRO_FEATURES_TR = [
    "Sinirsiz gorsel olusturma",
    "Sarki yazma & soyleme (ritimli, tonlu)",
    "Kod asistani (oku / ara / duzelt / yaz)",
    "Borsa & hisse fiyatlari",
    "Gunluk haber brifingi",
    "E-posta okuma & gonderme",
    "Oyun modu (performans yukseltme)",
    "Ekran analizi (gorsel zeka)",
    "YouTube kanal analizi",
]

_DEFAULT_PURCHASE_URL = "https://gumroad.com"
_cache: bool | None = None


def get_purchase_url() -> str:
    return str(get_app_config_value("pro_purchase_url", "") or _DEFAULT_PURCHASE_URL)


def _verify_gumroad(key: str):
    """Gumroad lisans dogrulama.
    True = gecerli, False = gecersiz/iade, None = yapilandirilmamis veya ag yok."""
    product_id = str(get_app_config_value("gumroad_product_id", "") or "").strip()
    permalink = str(get_app_config_value("gumroad_product_permalink", "") or "").strip()
    if not product_id and not permalink:
        return None
    try:
        data = {"license_key": (key or "").strip(), "increment_uses_count": "false"}
        if product_id:
            data["product_id"] = product_id
        else:
            data["product_permalink"] = permalink
        r = requests.post("https://api.gumroad.com/v2/licenses/verify",
                          data=data, timeout=10)
        if r.status_code == 200:
            body = r.json()
            if body.get("success"):
                purchase = body.get("purchase", {}) or {}
                if (purchase.get("refunded") or purchase.get("chargebacked")
                        or purchase.get("disputed")):
                    return False
                return True
        return False
    except Exception:
        return None


def _compute_pro() -> bool:
    if bool(get_app_config_value("pro_active", False)):
        return True
    key = str(get_app_config_value("license_key", "") or "").strip()
    if not key:
        return False
    res = _verify_gumroad(key)
    if res is True:
        save_app_config({"pro_active": True})
        return True
    if res is None:
        # Gumroad yapilandirilmamis veya internet yok -> anahtari kabul et (cevrimdisi tolerans).
        return True
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


def activate_license(key: str):
    """Anahtari dogrular ve kaydeder. (ok: bool, mesaj: str) doner."""
    global _cache
    key = (key or "").strip()
    if not key:
        return False, "Lisans anahtari bos olamaz."
    res = _verify_gumroad(key)
    if res is True:
        save_app_config({"license_key": key, "pro_active": True})
        _cache = True
        return True, "EXON Pro etkinlestirildi! Tesekkurler."
    if res is False:
        return False, "Lisans anahtari gecersiz, iade edilmis veya iptal edilmis."
    save_app_config({"license_key": key, "pro_active": True})
    _cache = True
    return True, "Lisans kaydedildi ve EXON Pro acildi."


def deactivate():
    global _cache
    save_app_config({"pro_active": False, "license_key": ""})
    _cache = False
