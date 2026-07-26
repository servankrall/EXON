"""
Uygulama açma — Windows uyumlu.
macOS 'open -a' yerine Windows start komutu, os.startfile ve winreg kullanır.
Servan Kanğal tarafından yapılmıştır
Windows portu: 'open -a AppName' → subprocess start / os.startfile / winreg
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# EXON'un bu oturumda açtığı uygulamalar (close_app ile kapatmak için izlenir)
OPENED_APPS: list[str] = []

# Kısa isimden Windows yürütülebilir/URI eşlemesi
APP_ALIASES = {
    # Tarayıcılar
    "safari":           None,  # Windows'ta yok
    "chrome":           "chrome",
    "google chrome":    "chrome",
    "firefox":          "firefox",
    "edge":             "msedge",
    "microsoft edge":   "msedge",
    # Terminal / Shell
    "terminal":         "cmd",
    "cmd":              "cmd",
    "powershell":       "powershell",
    "iterm":            "cmd",
    "iterm2":           "cmd",
    # Dosya yöneticisi
    "finder":           "explorer",
    "explorer":         "explorer",
    # Müzik / Medya
    "spotify":          "spotify",
    "music":            "wmplayer",
    "müzik":            "wmplayer",
    "apple music":      "wmplayer",  # Windows'ta WMP
    "windows media player": "wmplayer",
    # Geliştirici araçları
    "vscode":           "code",
    "vs code":          "code",
    "code":             "code",
    "visual studio code": "code",
    "xcode":            None,  # Windows'ta yok
    "docker":           "Docker Desktop",
    "postman":          "postman",
    "sequel pro":       None,
    "tableplus":        "TablePlus",
    # İletişim
    "whatsapp":         "WhatsApp",
    "telegram":         "Telegram",
    "slack":            "slack",
    "discord":          "Discord",
    "zoom":             "Zoom",
    "teams":            "ms-teams:",
    "microsoft teams":  "ms-teams:",
    # Ofis / Üretkenlik
    "notion":           "notion",
    "mail":             "mailto:",
    "outlook":          "outlook",
    "takvim":           "ms-calendar:",
    "calendar":         "ms-calendar:",
    "notes":            "notepad",
    "notlar":           "notepad",
    "onenote":          "onenote:",
    "word":             "winword",
    "excel":            "excel",
    "powerpoint":       "powerpnt",
    "numbers":          None,
    "pages":            None,
    "keynote":          None,
    # Sistem araçları
    "system settings":  "ms-settings:",
    "system preferences": "ms-settings:",
    "ayarlar":          "ms-settings:",
    "activity monitor": "taskmgr",
    "görev yöneticisi": "taskmgr",
    "task manager":     "taskmgr",
    "aktivite monitörü": "taskmgr",
    "calculator":       "calc",
    "hesap makinesi":   "calc",
    "hesap":            "calc",
    "preview":          "mspaint",
    "önizleme":         "mspaint",
    "paint":            "mspaint",
    "textedit":         "notepad",
    "photos":           "ms-photos:",
    "fotoğraflar":      "ms-photos:",
    "maps":             "bingmaps:",
    "haritalar":        "bingmaps:",
    "figma":            "figma",
}

# Windows'ta uygulama yollarının aranacağı dizinler
_APP_DIRS = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
    Path(os.environ.get("APPDATA", "")),
]


def _find_in_registry(app_name: str) -> str | None:
    """Windows Registry'de uygulama yolunu arar."""
    try:
        import winreg
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        ]
        names_to_try = [app_name, app_name + ".exe"]
        for hive, key_path in keys:
            for name in names_to_try:
                try:
                    with winreg.OpenKey(hive, f"{key_path}\\{name}") as k:
                        val, _ = winreg.QueryValueEx(k, "")
                        if val and Path(val).exists():
                            return val
                except OSError:
                    continue
    except ImportError:
        pass
    return None


def _find_exe_in_dirs(exe_name: str) -> str | None:
    """Program dizinlerinde .exe arar."""
    if not exe_name.lower().endswith(".exe"):
        exe_name_ext = exe_name + ".exe"
    else:
        exe_name_ext = exe_name

    for base in _APP_DIRS:
        if not base.exists():
            continue
        # Doğrudan veya alt klasörlerde ara
        for candidate in [
            base / exe_name_ext,
            base / exe_name / exe_name_ext,
        ]:
            if candidate.exists():
                return str(candidate)
    return None


def _launch(target: str, display_name: str) -> str:
    """Hedef uygulamayı başlatır."""
    # URI scheme ise (ms-settings:, mailto:, spotify: vb.)
    if ":" in target and not target.startswith(("C:", "D:", "http")):
        try:
            os.startfile(target)
            return f"{display_name} açıldı."
        except Exception as e:
            return f"'{display_name}' açılamadı: {e}"

    # PATH'te var mı?
    if shutil.which(target):
        try:
            subprocess.Popen([target], creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
            return f"{display_name} açıldı."
        except Exception as e:
            return f"'{display_name}' açılamadı: {e}"

    # Registry'de ara
    reg_path = _find_in_registry(target)
    if reg_path:
        try:
            os.startfile(reg_path)
            return f"{display_name} açıldı."
        except Exception as e:
            return f"'{display_name}' açılamadı: {e}"

    # Program dizinlerinde ara
    exe_path = _find_exe_in_dirs(target)
    if exe_path:
        try:
            os.startfile(exe_path)
            return f"{display_name} açıldı."
        except Exception as e:
            return f"'{display_name}' açılamadı: {e}"

    # Son çare: Windows 'start' komutu ile aç
    try:
        subprocess.Popen(
            f'start "" "{target}"',
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return f"{display_name} açıldı."
    except Exception as e:
        return f"'{display_name}' bulunamadı veya açılamadı: {e}"


def open_app(app_name: str) -> str:
    """Uygulamayı açar, başarı/hata mesajı döndürür."""
    if not app_name:
        return "Uygulama adı belirtilmedi."

    normalized = app_name.lower().strip()
    resolved = APP_ALIASES.get(normalized)

    # None → Windows'ta bu uygulama yok
    if resolved is None and normalized in APP_ALIASES:
        return f"'{app_name}' macOS'a özgü bir uygulamadır ve Windows'ta kullanılamaz."

    # Alias bulunamadıysa orijinal adı kullan
    if resolved is None:
        resolved = app_name

    result = _launch(resolved, app_name)
    if "açıldı" in result and normalized not in OPENED_APPS:
        OPENED_APPS.append(normalized)
    return result
