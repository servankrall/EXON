"""
Uygulama kapatma — EXON'un actigi (veya adi verilen) uygulamayi kapatir.
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

taskkill ile process imaj adina gore kapatir. explorer/python gibi kritik
surecler korunur (yanlislikla sistemi/EXON'u kapatmamak icin).
"""

from __future__ import annotations

import subprocess
import sys

from actions.open_app import OPENED_APPS, APP_ALIASES


_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

# Friendly ad -> kapatilacak process imaj adi/adlari
CLOSE_ALIASES = {
    "chrome": ["chrome.exe"], "google chrome": ["chrome.exe"],
    "firefox": ["firefox.exe"],
    "edge": ["msedge.exe"], "microsoft edge": ["msedge.exe"],
    "spotify": ["Spotify.exe"], "discord": ["Discord.exe"], "slack": ["slack.exe"],
    "telegram": ["Telegram.exe"], "whatsapp": ["WhatsApp.exe"], "zoom": ["Zoom.exe"],
    "vscode": ["Code.exe"], "vs code": ["Code.exe"], "code": ["Code.exe"],
    "visual studio code": ["Code.exe"],
    "notion": ["Notion.exe"], "outlook": ["OUTLOOK.EXE"], "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"], "powerpoint": ["POWERPNT.EXE"],
    "notepad": ["notepad.exe"], "notes": ["notepad.exe"], "notlar": ["notepad.exe"],
    "paint": ["mspaint.exe"], "preview": ["mspaint.exe"], "önizleme": ["mspaint.exe"],
    "calculator": ["Calculator.exe", "CalculatorApp.exe"],
    "hesap makinesi": ["Calculator.exe", "CalculatorApp.exe"],
    "hesap": ["Calculator.exe", "CalculatorApp.exe"],
    "task manager": ["Taskmgr.exe"], "görev yöneticisi": ["Taskmgr.exe"],
    "activity monitor": ["Taskmgr.exe"],
    "music": ["wmplayer.exe"], "müzik": ["wmplayer.exe"],
    "windows media player": ["wmplayer.exe"],
    "figma": ["Figma.exe"], "postman": ["Postman.exe"],
    "teams": ["ms-teams.exe", "Teams.exe"], "microsoft teams": ["ms-teams.exe", "Teams.exe"],
    "powershell": ["powershell.exe"], "cmd": ["cmd.exe"], "terminal": ["cmd.exe"],
}

# Asla kapatilmamasi gereken kritik surecler
_PROTECTED = {"explorer.exe", "python.exe", "pythonw.exe",
              "winlogon.exe", "csrss.exe", "dwm.exe", "svchost.exe"}


def _image_names(name: str) -> list[str]:
    key = (name or "").lower().strip()
    if key in CLOSE_ALIASES:
        return CLOSE_ALIASES[key]
    alias = APP_ALIASES.get(key)
    if isinstance(alias, str) and alias and ":" not in alias:
        exe = alias if alias.lower().endswith(".exe") else alias + ".exe"
        return [exe]
    base = key if key.endswith(".exe") else key + ".exe"
    return [base]


def _taskkill(image: str) -> bool:
    if not image or image.lower() in _PROTECTED:
        return False
    try:
        r = subprocess.run(["taskkill", "/F", "/IM", image, "/T"],
                           capture_output=True, text=True, creationflags=_NOWIN)
        return r.returncode == 0
    except Exception:
        return False


def close_app(name: str) -> str:
    """Adi verilen uygulamayi kapatir."""
    name = (name or "").strip()
    if not name:
        return "Hangi uygulamayi kapatacagimi belirt."
    images = _image_names(name)
    closed = [img for img in images if _taskkill(img)]
    low = name.lower()
    if low in OPENED_APPS:
        OPENED_APPS.remove(low)
    if closed:
        return f"{name} kapatildi."
    return f"{name} kapatilamadi (zaten kapali olabilir veya farkli bir adi olabilir)."


def close_opened_apps() -> str:
    """EXON'un bu oturumda actigi tum uygulamalari kapatir."""
    if not OPENED_APPS:
        return "EXON bu oturumda kapatilacak bir uygulama acmadi."
    names = list(OPENED_APPS)
    closed = []
    for n in names:
        if any(_taskkill(img) for img in _image_names(n)):
            closed.append(n)
    OPENED_APPS.clear()
    if closed:
        return "Actigim uygulamalar kapatildi: " + ", ".join(closed) + "."
    return "Actigim uygulamalar kapatilamadi (zaten kapali olabilir)."
