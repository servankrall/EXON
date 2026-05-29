"""
EXON Pro — lisans/abonelik yonetimi (aylik/yillik) + Gumroad dogrulama.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Para akisi (backend GEREKMEZ): satici (sen) Gumroad'da bir UYELIK (membership) urunu
acar; iki kademe koyar: Aylik ($2/ay) ve Yillik ($10/yil). Her alici otomatik bir
LISANS ANAHTARI alir; para SENIN Gumroad hesabina gecer. Uygulama anahtari Gumroad'in
ucretsiz API'siyle dogrular ve ABONELIK BITTIGINDE Pro otomatik kapanir.

config/api_keys.json:
  "pro_purchase_url_monthly": "https://<hesap>.gumroad.com/l/exon-pro?variant=Ayl%C4%B1k",
  "pro_purchase_url_yearly":  "https://<hesap>.gumroad.com/l/exon-pro?variant=Y%C4%B1ll%C4%B1k",
  "gumroad_product_id": "<urun_id>"
Ayrintilar: PRO_KURULUM.md
"""

from __future__ import annotations

import requests

from app_config import get_app_config_value, save_app_config


# Pro'ya ozel arac isimleri — main.py bu kapiyi tutar.
PRO_TOOLS = {
    "generate_image", "compose_song", "get_news_briefing", "get_stock_price",
    "read_emails", "send_email", "read_code_file", "list_code_files",
    "search_in_code", "write_code_file", "set_performance_mode",
    "analyze_screen", "get_youtube_channel_report",
    "compose_text", "summarize_url", "summarize_document",
}

# Pro tanitim ekraninda gosterilecek ozellikler
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

# Abonelik planlari (gosterim icin)
PLANS = {
    "monthly": {"label": "Aylik",  "price": "$2 / ay"},
    "yearly":  {"label": "Yillik", "price": "$10 / yil"},
}

_cache: bool | None = None


def _gumroad_configured() -> bool:
    return bool(str(get_app_config_value("gumroad_product_id", "") or "").strip()
                or str(get_app_config_value("gumroad_product_permalink", "") or "").strip())


def get_purchase_url(plan: str = "") -> str:
    """İlgili planın satın alma linkini döndürür.
    Öncelik: plana özel link > genel link > Gumroad permalink'ten kurulan ürün linki.
    Hiçbiri yoksa BOŞ döner (UI uyarı gösterir, boş sayfaya atmaz)."""
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
    # Yedek: yalnızca Gumroad permalink ayarlıysa ürün sayfasını ondan kur.
    permalink = str(get_app_config_value("gumroad_product_permalink", "") or "").strip()
    if permalink:
        return f"https://gumroad.com/l/{permalink}"
    return ""


def _verify_gumroad(key: str):
    """True=gecerli/aktif, False=gecersiz/iade/abonelik bitti,
    None=Gumroad yapilandirilmamis, 'neterror'=yapilandirildi ama internet yok."""
    if not _gumroad_configured():
        return None
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
        # Uyelik bittiyse veya odeme basarisizsa Pro kapanir.
        if purchase.get("subscription_ended_at") or purchase.get("subscription_failed_at"):
            return False
        rec = purchase.get("recurrence")  # 'monthly' | 'yearly' | None (tek seferlik)
        if rec:
            save_app_config({"pro_plan": rec})
        return True
    except Exception:
        return "neterror"


def _compute_pro() -> bool:
    key = str(get_app_config_value("license_key", "") or "").strip()
    if not key:
        # Anahtar yok: yalnizca manuel pro_active bayragi (kendi makinen icin).
        return bool(get_app_config_value("pro_active", False))
    res = _verify_gumroad(key)
    if res is None:
        # Gumroad yapilandirilmamis -> cevrimdisi tolerans (test/elle satis).
        save_app_config({"pro_active": True})
        return True
    if res == "neterror":
        # Yapilandirilmis ama internet yok -> son bilinen duruma guven.
        return bool(get_app_config_value("pro_active", False))
    if res is True:
        save_app_config({"pro_active": True})
        return True
    # Gecersiz / abonelik bitmis
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
    res = _verify_gumroad(key)
    if res is True:
        save_app_config({"license_key": key, "pro_active": True})
        _cache = True
        label = current_plan_label()
        extra = f" ({label} plan)" if label else ""
        return True, f"EXON Pro etkinlestirildi!{extra} Tesekkurler."
    if res is False:
        return False, "Lisans gecersiz, iade edilmis veya abonelik bitmis."
    # None (yapilandirilmamis) veya neterror -> kaydet ve kabul et
    save_app_config({"license_key": key, "pro_active": True})
    _cache = True
    return True, "Lisans kaydedildi ve EXON Pro acildi."


def deactivate():
    global _cache
    save_app_config({"pro_active": False, "license_key": ""})
    _cache = False
