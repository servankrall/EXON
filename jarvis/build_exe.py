"""
EXON tek-exe derleyici (cok-denemeli, saglam surum).
Kullanim:  python build_exe.py     (veya build_exe.bat'a cift tikla)

Neden cok-denemeli? PyInstaller bazi paketleri (ozellikle --collect-all comtypes
ve namespace 'google') derinlemesine tararken COKEBILIR (0xC0000005). Bu yuzden
once EN SADE ayarlarla denenir; exe cikmazsa biraz daha ekleyip tekrar denenir.
EXON Robotik tarafindan gelistirilmistir.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
SEP = ";" if os.name == "nt" else ":"
EXE = HERE / "dist" / ("EXON.exe" if os.name == "nt" else "EXON")


def have(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False


# ── 1) Gerekli paketler (toleransli) ─────────────────────────────────────────
print("=" * 60)
print("  EXON - tek dosya .exe derleme")
print("=" * 60)
print("\n[1/3] Paketler kuruluyor (birkac dakika surebilir)...")
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
for pkg in ("google-genai", "psutil", "Pillow", "requests", "beautifulsoup4",
            "pygame", "pyttsx3", "pyperclip", "pyautogui", "pygetwindow",
            "pywin32", "comtypes", "pyaudio", "SpeechRecognition"):
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"])


# ── Ortak argumanlar ─────────────────────────────────────────────────────────
def base_args() -> list[str]:
    a = ["--noconfirm", "--onefile", "--windowed", "--name", "EXON"]
    if (HERE / "EXON.ico").is_file():
        a += ["--icon", "EXON.ico"]
    for folder in ("SFX", "Icon", "Fonts", "core"):
        if (HERE / folder).is_dir():
            a += ["--add-data", f"{folder}{SEP}{folder}"]
    if (HERE / "config" / "api_keys.example.json").is_file():
        a += ["--add-data", f"config{os.sep}api_keys.example.json{SEP}config"]
    # Hooklarin yakalayamadigi gizli importlar (hafif, cokme riski yok)
    for h in ("pyttsx3.drivers.sapi5", "win32com.client", "pythoncom", "pywintypes",
              "pyaudio", "psutil", "requests", "bs4", "PIL._tkinter_finder"):
        root = h.split(".")[0]
        if have(root):
            a += ["--hidden-import", h]
    # google-genai icin metadata (namespace paketi); collect-all'dan daha guvenli
    if have("google.genai"):
        a += ["--collect-submodules", "google.genai",
              "--copy-metadata", "google-genai"]
    return a


def run(extra: list[str], clean: bool) -> bool:
    args = base_args() + extra
    if clean:
        args = ["--clean"] + args
    args += ["main.py"]
    print("\n  python -m PyInstaller " + " ".join(args) + "\n")
    if EXE.exists():
        try:
            EXE.unlink()
        except Exception:
            pass
    r = subprocess.run([sys.executable, "-m", "PyInstaller", *args])
    ok = (r.returncode == 0 and EXE.exists())
    print(f"\n  -> cikis kodu {r.returncode}; exe {'VAR' if EXE.exists() else 'YOK'}")
    return ok


# ── 2) Denemeler: sadeden -> kapsamliya ──────────────────────────────────────
print("\n[2/3] Derleniyor...")
print("\n--- Deneme 1/3: sade (yerlesik hooklara guven) ---")
ok = run([], clean=True)

if not ok:
    print("\n--- Deneme 2/3: pygame + bs4 submodulleri ---")
    extra = []
    if have("pygame"):
        extra += ["--collect-submodules", "pygame"]
    if have("bs4"):
        extra += ["--collect-all", "bs4"]
    ok = run(extra, clean=True)

if not ok:
    print("\n--- Deneme 3/3: konsol modu (hatayi gormek icin) ---")
    # comtypes'i KASTEN dislariz (0xC0000005 cokmesinin baslica sebebi)
    ok = run(["--console", "--exclude-module", "comtypes"], clean=True)

# ── 3) Sonuc ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if ok:
    print("  BASARILI!  ->  " + str(EXE))
    print("  Bu tek dosyayi paylas; acan kisi Python KURMADAN calistirir.")
    print("  Kullanici verisi exe yanindaki 'EXON_data' klasorunde tutulur.")
else:
    print("  Derleme tamamlanamadi.")
    print("  - 0xC0000005 / cokme genelde antivirus VEYA bozuk PyInstaller onbellegi.")
    print("  - Cozum 1: Antivirusu gecici kapat, tekrar dene.")
    print("  - Cozum 2: Onbellegi temizle:  python -m PyInstaller --clean ...")
    print("  - Yukarida 'ERROR:' satiri varsa bana yapistir.")
print("=" * 60)
