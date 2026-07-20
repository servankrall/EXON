# Servan Kanğal tarafından yapılmıştır
from __future__ import annotations

import json
from pathlib import Path


from paths import DATA_DIR

CONFIG_DIR = DATA_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "api_keys.json"


DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    # Opsiyonel: ücretsiz Hugging Face token'ı (görsel üretimi için).
    # Boşsa görsel üretimi otomatik olarak ücretsiz Pollinations.ai'ye düşer.
    "hf_api_key": "",
    # ── İleri seviye özellikler (hepsi opsiyonel) ──
    "picovoice_access_key": "",   # "Hey EXON" uyandırma sözcüğü (console.picovoice.ai)
    "wake_keyword_path": "",      # özel .ppn yolu (boşsa wake/Hey-EXON_windows.ppn veya 'jarvis')
    "telegram_bot_token": "",     # Telegram köprüsü (@BotFather)
    "discord_bot_token": "",      # Discord köprüsü (discord.py gerekir)
    # ── E-posta (Gmail IMAP/SMTP — uygulama şifresi, OAuth gerekmez) ──
    "gmail_address": "",          # Gmail adresin (e-posta okuma/gönderme için)
    "gmail_app_password": "",     # Google 'uygulama şifresi' (16 hane; normal şifre değil)
    # ── Barge-in: EXON konuşurken konuşursan susup seni dinler ──
    "barge_in": True,             # false yaparsan kapanır
    "barge_in_threshold": 1100,   # ses eşiği; düşürürsen daha hassas, yükseltirsen daha zor tetiklenir
    # ── EXON Pro (ücretli katman — Gumroad lisans doğrulama, backend gerekmez) ──
    "pro_active": False,                 # true: tüm Pro özellikleri açık (kendi makinen için)
    "license_key": "",                   # müşterinin girdiği lisans anahtarı
    "license_secret": "",                 # çevrimdışı anahtar imzası (boşsa gömülü varsayılan)
    "pro_plan": "",                       # 'monthly' | 'yearly' | 'lifetime'
    "gumroad_product_id": "",            # Gumroad ürün ID'si (lisans doğrulama için)
    "gumroad_product_permalink": "",     # alternatif: Gumroad permalink (örn. 'exon-pro')
    "pro_purchase_url": "",              # genel satın alma linki (yedek)
    "pro_purchase_url_monthly": "",      # Aylık ($2/ay) satın alma linki
    "pro_purchase_url_yearly": "",       # Yıllık ($10/yıl) satın alma linki
    # ── Yerel model (Ollama) — çevrimdışı/sansürsüz ──
    "ollama_url": "",                    # boşsa http://localhost:11434
    "ollama_model": "",                  # genel yerel model (örn. llama3.2)
    "ollama_savage_model": "",           # savage için sansürsüz model (örn. dolphin-mistral)
}


def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            config.update(raw)
    except Exception:
        pass
    return config


def save_app_config(updates: dict) -> dict:
    config = load_app_config()
    for key, value in (updates or {}).items():
        if value is None:
            continue
        config[key] = value
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def get_app_config_value(key: str, default=None):
    return load_app_config().get(key, default)


def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return bool(value)