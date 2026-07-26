"""
Dogruluk & Kontrol — cikti dogrulama, celiski/tutarsizlik tespiti, guven puani.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

- Guven puani: bir iddianin ne kadar 'emin' sunuldugunu/desteklendigini tahmin eder.
- Celiski tespiti: bir metinde birbiriyle celisen ifadeleri yakalar.
- Kaynak dogrulama: web arama sonucu bir iddiayi destekliyor mu (anahtar kelime ortusumu).
- Halusinasyon ipuclari: belirsizlik/uydurma sinyalleri.
Ikinci bir Gemini cagrisi gerektirmez; hizli ve yerel sezgisel kontrollerdir.
"""

from __future__ import annotations

import re

from memory.memory_manager import _normalize_text, _tokenize_text


# Belirsizlik / dusuk guven sinyalleri
_HEDGE = ("belki", "sanirim", "galiba", "muhtemelen", "emin degilim",
          "olabilir", "tahminen", "duydugum kadariyla", "kesin degil",
          "maybe", "i think", "probably", "not sure", "might be")
# Yuksek guven sinyalleri
_STRONG = ("kesinlikle", "kanitlanmis", "resmi", "kaynaga gore", "verilere gore",
           "olcum", "istatistik", "%", "tarihinde", "doğrulandı")
# Celiski cifti yakalama (basit zit kaliplar)
_NEG = ("değil", "degil", "yok", "olmaz", "hayır", "hayir", "asla", "not", "no")


def confidence_score(text: str, sources: int = 0) -> dict:
    """Bir iddianin guven puanini (0-100) tahmin eder."""
    t = _normalize_text(text)
    score = 55
    for w in _HEDGE:
        if w in t:
            score -= 12
    for w in _STRONG:
        if w in t:
            score += 8
    # rakam/tarih varligi guveni artirir
    if re.search(r"\d", text):
        score += 6
    # kaynak sayisi
    score += min(20, sources * 7)
    # cok kisa veya cok uzun cevaplar biraz daha az guvenli
    if len(text) < 15:
        score -= 8
    score = max(5, min(98, score))
    if score >= 75:
        label = "yüksek"
    elif score >= 50:
        label = "orta"
    else:
        label = "düşük"
    return {"score": score, "label": label}


def detect_contradictions(text: str) -> list[str]:
    """Metindeki cumleler arasinda basit celiski/tutarsizlik arar."""
    sentences = [s.strip() for s in re.split(r"[.!?\n]+", text) if len(s.strip()) > 8]
    warnings = []
    seen = []
    for s in sentences:
        toks = set(tok for tok in _tokenize_text(s) if len(tok) >= 4)
        neg = any(n in s.lower() for n in _NEG)
        for prev_s, prev_toks, prev_neg in seen:
            overlap = toks & prev_toks
            # ayni konudan bahsedip biri olumlu biri olumsuzsa -> olasi celiski
            if len(overlap) >= 2 and neg != prev_neg:
                warnings.append(f"Olası çelişki: '{prev_s[:50]}' ↔ '{s[:50]}'")
                break
        seen.append((s, toks, neg))
    return warnings[:5]


def verify_against_sources(claim: str, source_text: str) -> dict:
    """Bir iddianin, verilen kaynak metinde ne kadar desteklendigini olcer."""
    claim_toks = set(tok for tok in _tokenize_text(claim) if len(tok) >= 4)
    if not claim_toks:
        return {"supported": False, "overlap": 0.0,
                "msg": "İddiada kontrol edilebilir anahtar kelime yok."}
    src = _normalize_text(source_text)
    src_toks = set(_tokenize_text(source_text))
    matched = sum(1 for tok in claim_toks if tok in src_toks or tok in src)
    ratio = matched / len(claim_toks)
    supported = ratio >= 0.5
    return {
        "supported": supported,
        "overlap": round(ratio * 100, 0),
        "msg": (f"İddianın %{ratio*100:.0f}'i kaynak metinde destekleniyor."
                + ("" if supported else " Dikkat: zayıf destek, doğrulama öneririm.")),
    }


def review_answer(answer: str, sources: int = 0) -> str:
    """Bir cevabi cok yonlu denetler: guven + celiski + halusinasyon ipucu."""
    conf = confidence_score(answer, sources)
    contradictions = detect_contradictions(answer)
    t = _normalize_text(answer)
    hedges = [w for w in _HEDGE if w in t]
    lines = [f"[ÖZ-DENETİM] Güven: %{conf['score']} ({conf['label']})"]
    if hedges:
        lines.append("Belirsizlik ifadeleri: " + ", ".join(hedges[:5]))
    if contradictions:
        lines.append("Tutarsızlık uyarıları:")
        lines.extend("  - " + c for c in contradictions)
    if conf["label"] == "düşük":
        lines.append("Öneri: Bu bilgiyi deep_web_search ile doğrula.")
    if len(lines) == 1:
        lines.append("Belirgin çelişki/belirsizlik yok ✓")
    return "\n".join(lines)
