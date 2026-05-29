"""
Anlik metin cevirisi — anahtar gerektirmez.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

1. Google'in ucretsiz cevir ucu (gtx) — birincil
2. MyMemory API — yedek
Ikisi de ucretsizdir ve anahtar istemez.
"""

from __future__ import annotations

import requests


_HEADERS = {"User-Agent": "EXON-Robotik/1.0"}

# Dil adi -> ISO kodu (kullanici "ingilizce" derse de calissin)
_LANG_ALIASES = {
    "turkce": "tr", "türkçe": "tr", "turkish": "tr", "tr": "tr",
    "ingilizce": "en", "english": "en", "en": "en",
    "almanca": "de", "german": "de", "de": "de",
    "fransizca": "fr", "französisce": "fr", "french": "fr", "fr": "fr",
    "ispanyolca": "es", "spanish": "es", "es": "es",
    "italyanca": "it", "italian": "it", "it": "it",
    "rusca": "ru", "rusça": "ru", "russian": "ru", "ru": "ru",
    "arapca": "ar", "arapça": "ar", "arabic": "ar", "ar": "ar",
    "japonca": "ja", "japanese": "ja", "ja": "ja",
    "korece": "ko", "korean": "ko", "ko": "ko",
    "cince": "zh", "çince": "zh", "chinese": "zh", "zh": "zh",
}


def _norm_lang(lang: str, default: str = "tr") -> str:
    key = (lang or "").strip().lower()
    if not key:
        return default
    return _LANG_ALIASES.get(key, key[:5])


def _google_translate(text: str, target: str, source: str) -> str | None:
    try:
        res = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx", "sl": source or "auto", "tl": target,
                "dt": "t", "q": text,
            },
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        data = res.json()
        segments = data[0] if data and isinstance(data, list) else []
        out = "".join(seg[0] for seg in segments if seg and seg[0])
        return out.strip() or None
    except Exception:
        return None


def _mymemory_translate(text: str, target: str, source: str) -> str | None:
    try:
        res = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{source or 'en'}|{target}"},
            headers=_HEADERS, timeout=10,
        )
        if res.status_code != 200:
            return None
        out = (res.json().get("responseData", {}) or {}).get("translatedText", "")
        return out.strip() or None
    except Exception:
        return None


def translate_text(text: str, target_lang: str = "tr",
                   source_lang: str = "auto") -> str:
    """Metni hedef dile cevirir. source_lang bos/auto ise dil otomatik algilanir."""
    text = (text or "").strip()
    if not text:
        return "Cevrilecek bir metin vermelisin."
    target = _norm_lang(target_lang, "tr")
    source = _norm_lang(source_lang, "auto") if source_lang else "auto"
    if source == "auto":
        source = ""

    result = _google_translate(text, target, source)
    if not result:
        result = _mymemory_translate(text, target, source or "en")
    if not result:
        return "Ceviri su an yapilamadi (cevrimici servise ulasilamadi)."
    return result
