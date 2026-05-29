"""
Tarayici sekmesi kapatma — sadece aktif sekmeyi kapatir (tarayiciyi DEGIL).
EXON Robotik tarafindan gelistirilmistir — EXON Windows Edition

Tarayici penceresini one getirip Ctrl+W gonderir. pyautogui/pygetwindow
yalnizca cagri aninda (lazy) yuklenir; eksikse EXON acilirken sorun cikmaz.
"""

from __future__ import annotations

import time


_BROWSER_HINTS = ("chrome", "edge", "firefox", "brave", "opera",
                  "mozilla", "vivaldi", "yandex")


def close_browser_tab() -> str:
    """Aktif tarayicinin acik sekmesini kapatir (Ctrl+W)."""
    try:
        import pyautogui
    except Exception as exc:
        return f"Sekme kapatma icin pyautogui gerekli: {exc}"

    found = False
    try:
        import pygetwindow as gw
        for w in gw.getAllWindows():
            title = (getattr(w, "title", "") or "").lower()
            if title and any(h in title for h in _BROWSER_HINTS):
                try:
                    if getattr(w, "isMinimized", False):
                        w.restore()
                    w.activate()
                    time.sleep(0.25)
                    found = True
                except Exception:
                    pass
                break
    except Exception:
        # pygetwindow yoksa: tarayici zaten onde varsayilir
        found = True

    if not found:
        return "Acik bir tarayici penceresi bulamadim; once tarayiciyi ac."

    try:
        pyautogui.hotkey("ctrl", "w")
        return "Tarayici sekmesi kapatildi."
    except Exception as exc:
        return f"Sekme kapatilamadi: {exc}"
