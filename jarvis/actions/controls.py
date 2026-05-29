"""
Ses seviyesi + ekran goruntusu kontrolleri.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

pyautogui (medya tuslari) ve Pillow (ImageGrab) yalnizca cagri aninda yuklenir;
eksik olsalar bile EXON acilirken sorun cikmaz.
"""

from __future__ import annotations

import datetime
from pathlib import Path


from paths import DATA_DIR

_SHOT_DIR = DATA_DIR / "screenshots"


def set_volume(action: str = "mute", steps: int = 5) -> str:
    """Sistem sesini ayarlar. action: up | down | mute."""
    try:
        import pyautogui
    except Exception as exc:
        return f"Ses kontrolu icin pyautogui gerekli: {exc}"

    a = (action or "").lower().strip()
    try:
        steps = max(1, min(int(steps or 5), 20))
    except (TypeError, ValueError):
        steps = 5

    try:
        if a in ("mute", "sessiz", "sus", "unmute", "sustur"):
            pyautogui.press("volumemute")
            return "Ses ac/kapat (mute) uygulandi."
        if a in ("up", "arttir", "artir", "yukselt", "yükselt", "ac"):
            for _ in range(steps):
                pyautogui.press("volumeup")
            return f"Ses {steps} kademe artirildi."
        if a in ("down", "azalt", "kis", "kıs", "dusur", "düsür", "düşür"):
            for _ in range(steps):
                pyautogui.press("volumedown")
            return f"Ses {steps} kademe azaltildi."
        return "Ses islemi belirsiz. up / down / mute olmali."
    except Exception as exc:
        return f"Ses ayarlanamadi: {exc}"


def take_screenshot() -> str:
    """Tum ekranin goruntusunu alip dosyaya kaydeder, yolunu dondurur."""
    try:
        from PIL import ImageGrab
    except Exception as exc:
        return f"Ekran goruntusu icin Pillow gerekli: {exc}"

    try:
        _SHOT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = _SHOT_DIR / f"exon_shot_{stamp}.png"
        img = ImageGrab.grab()
        img.save(path)
        return f"Ekran goruntusu kaydedildi: {path}"
    except Exception as exc:
        return f"Ekran goruntusu alinamadi: {exc}"
