"""
Medya oynatma — Windows uyumlu.
YouTube, Spotify (Windows Desktop) ve Windows Media Player / Groove.
macOS osascript/AppleScript kaldırıldı, Windows URI scheme ve webbrowser kullanılıyor.
Servan Kanğal tarafından yapılmıştır
Windows portu: osascript → pyautogui / webbrowser, 'open' → os.startfile
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

from actions.browser import browser_control


# Windows'ta Spotify yolları
_SPOTIFY_PATHS = [
    Path(os.environ.get("APPDATA", "")) / "Spotify" / "Spotify.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps" / "Spotify.exe",
    Path(r"C:\Program Files\Spotify\Spotify.exe"),
    Path(r"C:\Program Files (x86)\Spotify\Spotify.exe"),
]


def _app_exists(paths: list) -> bool:
    return any(p.exists() for p in paths)


def _play_youtube(query: str) -> str:
    return browser_control("play_youtube", query=query)


def _open_uri(uri: str) -> bool:
    """URI veya URL'yi platform uygun şekilde açar."""
    try:
        os.startfile(uri)
        return True
    except Exception:
        try:
            webbrowser.open(uri)
            return True
        except Exception:
            return False


def _play_spotify(query: str, autoplay: bool = True) -> str:
    if not _app_exists(_SPOTIFY_PATHS):
        # Spotify yüklü değilse web ile dene
        encoded = urllib.parse.quote(query.strip())
        url = f"https://open.spotify.com/search/{encoded}"
        webbrowser.open(url)
        return f"Spotify Desktop bulunamadı. Spotify Web'de '{query}' araması açıldı."

    encoded_query = urllib.parse.quote(query.strip())
    search_uri = f"spotify:search:{encoded_query}"

    try:
        os.startfile(search_uri)
    except Exception:
        # Fallback: Spotify.exe ile URI
        spotify_exe = next((str(p) for p in _SPOTIFY_PATHS if p.exists()), None)
        if spotify_exe:
            try:
                subprocess.Popen([spotify_exe, search_uri])
            except Exception as exc:
                return f"Spotify açılamadı: {exc}"
        else:
            return "Spotify açılamadı."

    if not autoplay:
        return f"Spotify'da '{query}' araması açıldı."

    # Otomatik oynatma için pyautogui ile Enter/aşağı ok
    try:
        import pyautogui
        time.sleep(2.5)
        pyautogui.hotkey("alt", "tab")  # Spotify'a geç
        time.sleep(0.5)
        pyautogui.press("down")
        time.sleep(0.2)
        pyautogui.press("enter")
        return f"Spotify'da oynatılıyor: {query}"
    except ImportError:
        return (
            f"Spotify araması açıldı ama otomatik oynatma tamamlanamadı "
            f"(pyautogui gerekli). '{query}' araması Spotify'da hazır."
        )
    except Exception as exc:
        return (
            f"Spotify araması açıldı ama otomatik oynatma tamamlanamadı: {exc}. "
            f"'{query}' araması Spotify'da hazır."
        )


def _play_windows_media(query: str, autoplay: bool = True) -> str:
    """Groove Music / Windows Media Player üzerinden çalma."""
    # Groove Music URI
    encoded = urllib.parse.quote(query.strip())
    try:
        os.startfile(f"mswindowsmusic:search?q={encoded}")
        return f"Groove Music'te '{query}' araması açıldı."
    except Exception:
        pass

    # WMP ile dene
    wmp_paths = [
        Path(r"C:\Program Files\Windows Media Player\wmplayer.exe"),
        Path(r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"),
    ]
    for wmp in wmp_paths:
        if wmp.exists():
            try:
                subprocess.Popen([str(wmp)])
                return f"Windows Media Player açıldı. '{query}' için arama yapabilirsiniz."
            except Exception:
                pass

    return f"Windows müzik uygulaması bulunamadı."


def play_media(query: str, provider: str = "auto", autoplay: bool = True) -> str:
    if not query or not query.strip():
        return "Çalınacak içerik belirtilmedi."

    normalized_provider = (provider or "auto").strip().lower()
    if normalized_provider in {"yt", "youtube music"}:
        normalized_provider = "youtube"
    elif normalized_provider in {"apple music", "music", "apple_music"}:
        # Windows'ta Apple Music yok, Spotify veya YouTube'a yönlendir
        normalized_provider = "auto"

    if normalized_provider == "spotify":
        return _play_spotify(query, autoplay=autoplay)
    if normalized_provider == "youtube":
        return _play_youtube(query)
    if normalized_provider in {"windows_media", "groove", "wmp"}:
        return _play_windows_media(query, autoplay=autoplay)

    # auto: Spotify varsa önce dene, sonra YouTube
    if _app_exists(_SPOTIFY_PATHS):
        result = _play_spotify(query, autoplay=autoplay)
        if "bulunamadı" not in result and "açılamadı" not in result:
            return result

    return _play_youtube(query)
