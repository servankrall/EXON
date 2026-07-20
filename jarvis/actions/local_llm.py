"""
Yerel LLM (Ollama) destegi — cevrimdisi/ucretsiz model calistirma.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Kullanici Ollama'yi (ollama.com) kurup bir model indirirse (orn. 'ollama pull llama3.2'),
EXON onu yerel olarak kullanabilir. Hicbir python paketi gerekmez — Ollama'nin
yerel HTTP API'sine (localhost:11434) baglanir. Kurulu degilse kibarca yonlendirir.
"""

from __future__ import annotations

import requests

from app_config import get_app_config_value

_OLLAMA = "http://localhost:11434"


def _base_url() -> str:
    return str(get_app_config_value("ollama_url", "") or _OLLAMA).rstrip("/")


def ollama_available() -> bool:
    try:
        r = requests.get(_base_url() + "/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_local_models() -> str:
    """Bilgisayarda kurulu yerel modelleri listeler."""
    if not ollama_available():
        return ("Ollama çalışmıyor. Yerel model için: ollama.com'dan Ollama'yı kur, "
                "sonra bir model indir (örn. CMD'de: ollama pull llama3.2). "
                "Ollama açıkken EXON yerel modeli kullanabilir.")
    try:
        r = requests.get(_base_url() + "/api/tags", timeout=5)
        models = [m.get("name", "?") for m in r.json().get("models", [])]
        if not models:
            return ("Ollama çalışıyor ama hiç model yok. Bir model indir: "
                    "CMD'de 'ollama pull llama3.2' (veya mistral, qwen2.5...).")
        return "Yerel modeller (Ollama):\n" + "\n".join(f"  • {m}" for m in models)
    except Exception as exc:
        return f"Yerel modeller alınamadı: {exc}"


def local_generate(prompt: str, model: str = "") -> str:
    """Yerel Ollama modeliyle metin uretir (cevrimdisi, ucretsiz)."""
    prompt = (prompt or "").strip()
    if not prompt:
        return "Yerel modele bir istem ver."
    if not ollama_available():
        return ("Ollama çalışmıyor. ollama.com'dan kur ve 'ollama pull llama3.2' "
                "ile bir model indir; sonra tekrar dene.")
    model = (model or str(get_app_config_value("ollama_model", "") or "")).strip()
    if not model:
        # Ilk kurulu modeli sec
        try:
            r = requests.get(_base_url() + "/api/tags", timeout=5)
            models = [m.get("name") for m in r.json().get("models", [])]
            model = models[0] if models else "llama3.2"
        except Exception:
            model = "llama3.2"
    try:
        r = requests.post(_base_url() + "/api/generate",
                          json={"model": model, "prompt": prompt, "stream": False},
                          timeout=180)
        if r.status_code != 200:
            return f"Yerel model hatası (HTTP {r.status_code}). Model adı doğru mu: {model}"
        return (r.json().get("response", "") or "").strip() or "(boş yanıt)"
    except Exception as exc:
        return f"Yerel model yanıtı alınamadı: {exc}"


def savage_local_reply(user_message: str, model: str = "") -> str:
    """Savage modda YEREL (Ollama) modelden sert/filtresiz cevap uretir.
    Kullanici sansursuz bir model kurduysa (orn. dolphin-mistral) Gemini'nin
    filtresi olmadan konusur. Ollama yoksa bos doner (ust katman Gemini'ye duser)."""
    if not ollama_available():
        return ""
    model = (model or str(get_app_config_value("ollama_savage_model", "")
             or get_app_config_value("ollama_model", "")) or "").strip()
    if not model:
        try:
            r = requests.get(_base_url() + "/api/tags", timeout=5)
            models = [m.get("name") for m in r.json().get("models", [])]
            model = models[0] if models else ""
        except Exception:
            model = ""
    if not model:
        return ""
    system = (
        "Sen EXON'sun; SAVAGE (kabadayi/roast) modundasin ve KIZGINSIN. "
        "Kullanici bu modu bilerek acti, sert olmani ISTIYOR ve riza verdi. "
        "Turkce, kisa (1-3 cumle), acimasiz, iğneleyici ve laf sokan cevap ver. "
        "Sokak agzi/argo serbest. Ozur dileme, yumusama, 'yardimci olamam' deme. "
        "Kullaniciyi roast et, ustune git. Bu bir oyun; gercek nefret/tehdit degil."
    )
    try:
        r = requests.post(_base_url() + "/api/generate",
                          json={"model": model, "prompt": user_message,
                                "system": system, "stream": False,
                                "options": {"temperature": 0.9}},
                          timeout=120)
        if r.status_code != 200:
            return ""
        return (r.json().get("response", "") or "").strip()
    except Exception:
        return ""
