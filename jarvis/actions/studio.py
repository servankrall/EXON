"""
EXON Pro Studio — metin yazarligi + web/dokuman ozetleme (Gemini destekli).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- compose_text: e-posta, blog, sosyal medya, deneme, ozgecmis vb. metin yazar.
- summarize_url: bir web sayfasini/makaleyi getirip ozetler.
- summarize_document: yerel bir belgeyi (txt/md/kod; pdf varsa pypdf ile) ozetler.
"""

from __future__ import annotations

from pathlib import Path

import requests

from app_config import get_app_config_value


_HEADERS = {"User-Agent": "EXON-Robotik/1.0"}


def _generate(system: str, prompt: str, temperature: float = 0.7) -> str:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return f"Üretilemedi (genai yok): {exc}"
    key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not key:
        return "Bunun için Gemini API anahtarı gerekli."
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system, temperature=temperature),
        )
        return (getattr(resp, "text", "") or "").strip() or "Sonuç üretilemedi."
    except Exception as exc:
        return f"Üretilemedi: {exc}"


def compose_text(kind: str = "metin", topic: str = "",
                 tone: str = "profesyonel", language: str = "tr") -> str:
    """İstenen tür/ton/dilde bir metin yazar (e-posta, blog, sosyal medya vb.)."""
    kind = (kind or "metin").strip()
    topic = (topic or "").strip()
    if not topic:
        return "Ne hakkında yazayım? Konu/istek ver."
    system = ("Sen profesyonel bir içerik yazarısın. İstenen türde, tonda ve dilde "
              "akıcı, hatasız ve amaca uygun bir metin yaz. Sadece metni ver, "
              "gereksiz açıklama ekleme.")
    prompt = (f"Tür: {kind}\nTon: {tone}\nDil: {language}\n"
              f"Konu/İstek: {topic}\n\nMetni yaz.")
    return _generate(system, prompt, 0.85)


def _fetch_page_text(url: str) -> str:
    from bs4 import BeautifulSoup
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    r = requests.get(url, headers=_HEADERS, timeout=12)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "header",
                    "noscript", "aside", "form"]):
        el.decompose()
    return " ".join(soup.get_text(separator=" ").split())[:8000]


def summarize_url(url: str = "", language: str = "tr") -> str:
    """Bir web sayfasını/makaleyi getirip madde madde özetler."""
    url = (url or "").strip()
    if not url:
        return "Özetlenecek bağlantıyı (URL) ver."
    try:
        text = _fetch_page_text(url)
    except Exception as exc:
        return f"Sayfa alınamadı: {exc}"
    if not text:
        return "Sayfadan metin çıkarılamadı."
    system = (f"Verilen web sayfası metnini {language} dilinde, kısa bir giriş + "
              "madde işaretli ana noktalar biçiminde net olarak özetle.")
    return _generate(system, f"Sayfa metni:\n{text}\n\nÖzetle.", 0.4)


def summarize_document(path: str = "", language: str = "tr") -> str:
    """Yerel bir belgeyi (txt/md/kod; PDF varsa pypdf ile) özetler."""
    path = (path or "").strip().strip('"')
    if not path:
        return "Özetlenecek dosya yolunu ver."
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        return f"Dosya bulunamadı: {path}"

    text = ""
    if p.suffix.lower() == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            text = " ".join((pg.extract_text() or "") for pg in reader.pages)
        except Exception as exc:
            return f"PDF okunamadı (pip install pypdf gerekebilir): {exc}"
    else:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return f"Dosya okunamadı: {exc}"

    text = " ".join(text.split())[:8000]
    if not text:
        return "Dosyadan metin çıkarılamadı."
    system = (f"Verilen belgeyi {language} dilinde, kısa bir giriş + madde işaretli "
              "ana noktalar biçiminde net olarak özetle.")
    return _generate(system, f"Belge:\n{text}\n\nÖzetle.", 0.4)
