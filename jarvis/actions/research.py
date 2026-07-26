"""
Akademik arastirma araclari — arXiv + Crossref (ucretsiz, anahtarsiz).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- search_academic: arXiv'de bilimsel makale arar (baslik/ozet/yazar/link).
- resolve_doi: bir DOI'yi Crossref ile coup kunye/ozet dondurur.
- Kaynak guvenilirlik puani: yayinci/atif/tarih sezgisel skoru.
Harici paket gerekmez (requests + stdlib XML).
"""

from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET

import requests

_HEADERS = {"User-Agent": "EXON-Robotik/1.0 (akademik arastirma)"}


def search_academic(query: str, limit: int = 5) -> str:
    """arXiv'de makale arar. Baslik, yazarlar, yil, ozet ve link dondurur."""
    query = (query or "").strip()
    if not query:
        return "Araştırma konusu/sorgusu gerekli."
    try:
        limit = max(1, min(int(limit or 5), 10))
    except (TypeError, ValueError):
        limit = 5
    try:
        url = ("http://export.arxiv.org/api/query?search_query="
               + urllib.parse.quote(f"all:{query}")
               + f"&start=0&max_results={limit}&sortBy=relevance")
        res = requests.get(url, headers=_HEADERS, timeout=15)
        if res.status_code != 200:
            return f"arXiv'e ulaşılamadı (HTTP {res.status_code})."
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(res.text)
        entries = root.findall("a:entry", ns)
        if not entries:
            return f"'{query}' için arXiv'de makale bulunamadı."
        out = [f"'{query}' için {len(entries)} akademik makale (arXiv):"]
        for i, e in enumerate(entries, 1):
            title = (e.findtext("a:title", "", ns) or "").strip().replace("\n", " ")
            summary = (e.findtext("a:summary", "", ns) or "").strip().replace("\n", " ")
            published = (e.findtext("a:published", "", ns) or "")[:4]
            authors = [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]
            link = ""
            for ln in e.findall("a:link", ns):
                if ln.get("type") == "text/html" or ln.get("rel") == "alternate":
                    link = ln.get("href", "")
                    break
            auth_str = ", ".join(a for a in authors[:3] if a)
            if len(authors) > 3:
                auth_str += " ve diğerleri"
            out.append(f"\n{i}. {title} ({published})")
            if auth_str:
                out.append(f"   Yazarlar: {auth_str}")
            out.append(f"   Özet: {summary[:280]}...")
            if link:
                out.append(f"   Link: {link}")
        return "\n".join(out)
    except Exception as exc:
        return f"Akademik arama başarısız: {exc}"


def resolve_doi(doi: str) -> str:
    """Bir DOI'yi Crossref ile çözer: künye + dergi + atıf sayısı + güven puanı."""
    doi = (doi or "").strip().replace("https://doi.org/", "").replace("doi:", "").strip()
    if not doi:
        return "Çözülecek bir DOI gir (örn. 10.1038/nature12373)."
    try:
        res = requests.get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}",
                           headers=_HEADERS, timeout=15)
        if res.status_code == 404:
            return f"DOI bulunamadı: {doi}"
        if res.status_code != 200:
            return f"Crossref'e ulaşılamadı (HTTP {res.status_code})."
        msg = res.json().get("message", {})
        title = (msg.get("title") or ["(başlık yok)"])[0]
        authors = msg.get("author", []) or []
        auth_str = ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in authors[:4]) or "?"
        journal = (msg.get("container-title") or [""])[0]
        year = ""
        try:
            year = str(msg.get("published", {}).get("date-parts", [[None]])[0][0] or "")
        except Exception:
            pass
        cites = msg.get("is-referenced-by-count", 0)
        publisher = msg.get("publisher", "")
        score = _source_trust(cites, year, publisher)
        lines = [
            f"DOI: {doi}",
            f"Başlık: {title}",
            f"Yazarlar: {auth_str}",
            f"Dergi/Yayıncı: {journal or publisher}",
            f"Yıl: {year or '?'} · Atıf sayısı: {cites}",
            f"Kaynak güvenilirlik puanı: {score}/100",
            f"Bağlantı: https://doi.org/{doi}",
        ]
        return "\n".join(lines)
    except Exception as exc:
        return f"DOI çözümleme başarısız: {exc}"


def _source_trust(citations: int, year: str, publisher: str) -> int:
    """Atif/tarih/yayinciya gore basit kaynak guvenilirlik puani (0-100)."""
    score = 40
    score += min(35, int(citations) // 10) if str(citations).isdigit() else 0
    if citations and int(citations) > 100:
        score += 10
    rep = ("nature", "elsevier", "springer", "ieee", "acm", "wiley",
           "oxford", "cambridge", "science")
    if publisher and any(r in publisher.lower() for r in rep):
        score += 12
    try:
        if year and int(year) >= 2018:
            score += 5  # guncel
    except Exception:
        pass
    return max(10, min(98, score))
