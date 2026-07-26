"""
Coklu ajan sistemi — tek soruyu birden cok 'uzman' bakis acisiyla isler.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Tek Gemini modeliyle, farkli ROLLER (uzman profilleri) olusturup her birinden
gorus alir, sonra bir 'sentezci' hepsini birlestirir. Boylece daha derin,
cok-yonlu ve oz-elestirili yanitlar olusur. Paralel calisir (hizli).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app_config import get_app_config_value

# Hazir uzman profilleri (rol -> sistem talimati)
AGENTS = {
    "arastirmaci": "Sen titiz bir araştırmacısın. Konuyu somut bilgi, veri ve "
                   "örneklerle ele al; varsayımları belirt.",
    "elestirmen":  "Sen yapıcı bir eleştirmensin. Riskleri, zayıf noktaları, "
                   "gözden kaçan durumları ve karşı argümanları bul.",
    "planlamaci":  "Sen pratik bir planlamacısın. Konuyu uygulanabilir, adım adım "
                   "bir eylem planına dök; öncelik ve süre ver.",
    "mimar":       "Sen kıdemli bir teknik mimarsın. Tasarım, ölçeklenebilirlik, "
                   "bakım ve teknik tercihleri değerlendir.",
    "kalite":      "Sen bir kalite uzmanısın. Doğruluk, tutarlılık, test edilebilirlik "
                   "ve kullanıcı deneyimi açısından denetle.",
}

# Varsayilan panel (rol secilmezse)
_DEFAULT_PANEL = ["arastirmaci", "elestirmen", "planlamaci"]


def _ask(role_instruction: str, question: str, temperature: float = 0.6) -> str:
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return f"(model yok: {exc})"
    key = str(get_app_config_value("gemini_api_key", "") or "").strip()
    if not key:
        return "(Gemini API anahtarı gerekli)"
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=role_instruction + " Kısa ve öz yanıtla (en fazla 6 cümle).",
                temperature=temperature),
        )
        return (getattr(resp, "text", "") or "").strip() or "(boş yanıt)"
    except Exception as exc:
        return f"(hata: {exc})"


def expert_panel(question: str, roles: str = "") -> str:
    """Birden cok uzman ajandan paralel gorus alip sentezler."""
    question = (question or "").strip()
    if not question:
        return "Uzman paneline bir soru/konu ver."

    # Rolleri sec
    chosen = []
    if roles:
        for r in roles.replace(",", " ").split():
            r = r.strip().lower()
            if r in AGENTS:
                chosen.append(r)
    if not chosen:
        chosen = _DEFAULT_PANEL
    chosen = chosen[:5]

    # Paralel gorus topla
    opinions = {}
    with ThreadPoolExecutor(max_workers=len(chosen)) as pool:
        futs = {pool.submit(_ask, AGENTS[r], question): r for r in chosen}
        for fut in futs:
            role = futs[fut]
            try:
                opinions[role] = fut.result()
            except Exception as exc:
                opinions[role] = f"(hata: {exc})"

    # Sentez
    combined = "\n\n".join(f"[{r.upper()}]\n{op}" for r, op in opinions.items())
    synthesis = _ask(
        "Sen bir danışman konseyi başkanısın. Aşağıdaki uzman görüşlerini birleştirip "
        "TEK, net, dengeli bir sonuç + somut tavsiye üret. Çelişen görüşleri belirt.",
        f"Soru: {question}\n\nUzman görüşleri:\n{combined}",
        temperature=0.4,
    )

    out = ["[UZMAN PANELİ — " + ", ".join(chosen) + "]", ""]
    for r, op in opinions.items():
        out.append(f"● {r.capitalize()}: {op}")
    out.append("")
    out.append("[SENTEZ / SONUÇ]")
    out.append(synthesis)
    return "\n".join(out)


def list_agents() -> str:
    lines = ["[MEVCUT UZMAN AJANLAR]"]
    for role, desc in AGENTS.items():
        lines.append(f"  • {role}: {desc.split('.')[0]}.")
    return "\n".join(lines)
