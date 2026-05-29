"""
TTS (Text-to-Speech) — Windows SAPI / pyttsx3 kullanır.
macOS 'say' komutu yerine pyttsx3 ile Windows native TTS.
Servan Kanğal tarafından yapılmıştır
Windows portu: 'say' komutu → pyttsx3
"""

import threading

try:
    import pyttsx3
    _engine = pyttsx3.init()
    # Türkçe ses varsa seç, yoksa varsayılanı kullan
    voices = _engine.getProperty("voices")
    _turkish_voice = None
    for v in voices:
        if "tr" in (v.id or "").lower() or "turkish" in (v.name or "").lower():
            _turkish_voice = v.id
            break
    if _turkish_voice:
        _engine.setProperty("voice", _turkish_voice)
    _engine.setProperty("rate", 175)
    _PYTTSX3_OK = True
except Exception:
    _PYTTSX3_OK = False

_tts_lock = threading.Lock()


def speak_text(text: str, on_done=None, blocking: bool = False):
    """
    Metni sesli olarak okur.
    on_done: okuma bitince çağrılacak fonksiyon (opsiyonel)
    blocking: True ise bitene kadar bekler
    """
    if not text or not text.strip():
        if on_done:
            on_done()
        return

    # Çok uzun metinleri kısalt
    max_len = 500
    if len(text) > max_len:
        text = text[:max_len] + "..."

    def _run():
        if _PYTTSX3_OK:
            try:
                with _tts_lock:
                    _engine.say(text)
                    _engine.runAndWait()
            except Exception:
                # pyttsx3 thread-safe olmayabilir, PowerShell fallback
                _powershell_speak(text)
        else:
            _powershell_speak(text)
        if on_done:
            on_done()

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def _powershell_speak(text: str):
    """PowerShell SAPI ile TTS (fallback)."""
    import subprocess
    # Tek tırnak karakterlerini temizle
    safe_text = text.replace("'", "").replace('"', "")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Speak('{safe_text}')"
    )
    try:
        subprocess.run(
            ["powershell", "-Command", script],
            check=False,
            timeout=30,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def get_available_voices() -> list[str]:
    """Windows'taki mevcut sesleri listeler."""
    if not _PYTTSX3_OK:
        return []
    try:
        voices = _engine.getProperty("voices")
        return [v.name for v in voices]
    except Exception:
        return []
