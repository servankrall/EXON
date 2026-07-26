"""
Wikipedia hizli-cevap kaynagi — kisi/yer/kavram sorulari icin aninda ozet.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Once Turkce Wikipedia'da arar, ozet bulamazsa Ingilizce'ye duser.
Anahtar gerektirmez (Wikipedia REST + MediaWiki API ucretsiz).
"""

from __future__ import annotations

import threading
import time
import urllib.parse

import requests


_HEADERS = {"User-Agent": "EXON-Robotik/1.0 (kisisel asistan)"}

# Ayni sorgu kisa sure icinde tekrar gelirse internete cikmadan cevapla.
_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600.0  # 10 dakika
_CACHE_LOCK = threading.Lock()


def _cache_get(key: str) -> str | None:
    with _CACHE_LOCK:
        item = _CACHE.get(key)
        if item and (time.time() - item[0]) < _CACHE_TTL:
            return item[1]
    return None


def _cache_put(key: str, value: str) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (time.time(), value)


def _search_title(query: str, lang: str) -> str | None:
    """MediaWiki arama API'si ile en alakali sayfa basligini bulur."""
    try:
        res = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={
                "action": "query", "list": "search", "srsearch": query,
                "format": "json", "srlimit": 1,
            },
            headers=_HEADERS, timeout=8,
        )
        if res.status_code != 200:
            return None
        hits = (res.json().get("query", {}) or {}).get("search", []) or []
        if hits:
            return hits[0].get("title")
    except Exception:
        return None
    return None


def _summary_for_title(title: str, lang: str) -> str | None:
    """REST 'page/summary' ucundan duz metin ozet ceker."""
    try:
        res = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(title.replace(" ", "_")),
            headers=_HEADERS, timeout=8,
        )
        if res.status_code != 200:
            return None
        data = res.json()
        extract = (data.get("extract") or "").strip()
        if not extract:
            return None
        page_url = (((data.get("content_urls") or {}).get("desktop") or {})
                    .get("page") or "")
        title_txt = data.get("title") or title
        out = f"{title_txt}: {extract}"
        if page_url:
            out += f"\n(Kaynak: {page_url})"
        return out
    except Exception:
        return None


def get_wikipedia_summary(query: str) -> str:
    """Verilen konu/kisi icin kisa, guvenilir Wikipedia ozeti dondurur.
    Once Turkce, bulamazsa Ingilizce Wikipedia'yi dener."""
    query = (query or "").strip()
    if not query:
        return "Wikipedia icin bir konu vermelisin."

    cached = _cache_get(query.lower())
    if cached is not None:
        return cached

    for lang in ("tr", "en"):
        title = _search_title(query, lang) or query
        summary = _summary_for_title(title, lang)
        if summary:
            _cache_put(query.lower(), summary)
            return summary

    msg = (f"'{query}' icin Wikipedia'da ozet bulunamadi. "
           "deep_web_search ile genis aramayi dene.")
    return msg
