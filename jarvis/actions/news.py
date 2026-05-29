"""
Haber brifingi — Google News RSS (ucretsiz, anahtarsiz).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Konu verilirse o konuda, verilmezse gunun manset haberlerini ozetler.
"""

from __future__ import annotations

import urllib.parse

import requests
from bs4 import BeautifulSoup


_HEADERS = {"User-Agent": "EXON-Robotik/1.0"}


def get_news_briefing(topic: str = "", count: int = 6, language: str = "tr") -> str:
    """Gunun haberlerini veya verilen konudaki haberleri ozetler."""
    topic = (topic or "").strip()
    try:
        count = max(1, min(int(count or 6), 12))
    except (TypeError, ValueError):
        count = 6

    lang = (language or "tr").strip().lower()[:2] or "tr"
    gl = "TR" if lang == "tr" else "US"
    ceid = f"{gl}:{lang}"

    if topic:
        url = ("https://news.google.com/rss/search?q="
               + urllib.parse.quote(topic)
               + f"&hl={lang}&gl={gl}&ceid={ceid}")
    else:
        url = f"https://news.google.com/rss?hl={lang}&gl={gl}&ceid={ceid}"

    try:
        res = requests.get(url, headers=_HEADERS, timeout=10)
        if res.status_code != 200:
            return "Haberler su an alinamadi."
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("item")
        if not items:
            return ("Haber bulunamadi."
                    if topic else "Gunun haberleri su an alinamadi.")
        lines = []
        for i, it in enumerate(items[:count], 1):
            title_tag = it.find("title")
            src_tag = it.find("source")
            title = title_tag.get_text(strip=True) if title_tag else ""
            src = src_tag.get_text(strip=True) if src_tag else ""
            if not title:
                continue
            line = f"{i}. {title}"
            if src:
                line += f" — {src}"
            lines.append(line)
        if not lines:
            return "Haber basligi okunamadi."
        header = (f"'{topic}' ile ilgili haberler:" if topic
                  else "Gunun one cikan haberleri:")
        return header + "\n" + "\n".join(lines)
    except Exception as exc:
        return f"Haberler alinamadi: {exc}"
