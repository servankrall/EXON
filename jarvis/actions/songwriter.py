"""
Sarki sozu yazma — istenen tur/dil/ruh haline gore ANLAMLI sozler uretir.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Gemini metin modeliyle soz yazilir; ardindan EXON (canli ses) bunu seslendirir.
rap / pop / duygusal / arabesk / rock ... her tur ve her dil desteklenir.
"""

from __future__ import annotations

from app_config import get_app_config_value


def compose_song(topic: str = "", style: str = "pop",
                 language: str = "tr", mood: str = "") -> str:
    """Verilen konu/tur/dil/ruh haline uygun kisa bir sarki sozu dondurur."""
    topic    = (topic or "").strip()
    style    = (style or "pop").strip()
    language = (language or "tr").strip()
    mood     = (mood or "").strip()

    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return f"Sarki uretilemedi (genai yok): {exc}"

    api_key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not api_key:
        return "Sarki yazmak icin Gemini API anahtari gerekli."

    system = (
        "Sen usta bir soz yazari ve bestecisin. Sana verilen TUR, DIL ve RUH HALINE "
        "tam uygun, akici, ANLAMLI ve ozgun bir sarki sozu yaz. "
        "Yapi: 1 kita + akilda kalici bir NAKARAT + 1 kita (kisa tut). "
        "Tur kurallarina sadik kal: rap ise kafiyeli, ritmik ve vurgulu; pop ise "
        "akilda kalici ve melodik nakaratli; duygusal/arabesk ise icten ve derin. "
        "SADECE sarki sozunu ver — aciklama, baslik etiketi veya nota yazma. "
        "Sozu istenen dilde yaz."
    )
    prompt = (
        f"Tur: {style}\n"
        f"Dil: {language}\n"
        f"Ruh hali: {mood or 'serbest'}\n"
        f"Konu: {topic or 'serbest, anlamli bir tema sec'}\n\n"
        "Simdi sarki sozunu yaz."
    )

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system, temperature=0.95),
        )
        text = (getattr(resp, "text", "") or "").strip()
        return text or "Sarki sozu uretilemedi, tekrar dener misin?"
    except Exception as exc:
        return f"Sarki sozu uretilemedi: {exc}"
