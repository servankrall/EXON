"""
EXON tek-exe derleyici (saglam surum).
Kullanim:  python build_exe.py     (veya build_exe.bat'a cift tikla)

Neden Python script? Boylece SADECE kurulu paketler toplanir ve SADECE var olan
klasorler eklenir; bir paket eksik diye PyInstaller aniden durmaz. Ayrica tum
PyInstaller ciktisi ekranda gosterilir (hatalar gizlenmez).
EXON Robotik tarafindan gelistirilmistir.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)


def have(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False


def pip(*pkgs: str) -> None:
    for p in pkgs:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", p])


print("=" * 60)
print("  EXON - tek dosya .exe derleme")
print("=" * 60)

# ---- 1) Gerekli paketler (toleransli; biri olmazsa devam) ----
print("\n[1/3] Paketler kuruluyor (birkac dakika surebilir)...")
subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
for pkg in ("google-genai", "psutil", "Pillow", "requests", "beautifulsoup4",
            "pygame", "pyttsx3", "pyperclip", "pyautogui", "pygetwindow",
            "pywin32", "comtypes", "pyaudio", "SpeechRecognition"):
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", pkg])
pip("pyinstaller")

# ---- 2) PyInstaller argumanlari ----
sep = ";" if os.name == "nt" else ":"
args = ["--noconfirm", "--clean", "--onefile", "--windowed", "--name", "EXON"]

if (HERE / "EXON.ico").is_file():
    args += ["--icon", "EXON.ico"]

# Yalnizca VAR OLAN klasor/dosyalari paketle
for folder in ("SFX", "Icon", "Fonts", "core"):
    if (HERE / folder).is_dir():
        args += ["--add-data", f"{folder}{sep}{folder}"]
example_cfg = HERE / "config" / "api_keys.example.json"
if example_cfg.is_file():
    args += ["--add-data", f"config{os.sep}api_keys.example.json{sep}config"]

# Yalnizca KURULU paketleri tamamen topla (eksikse atla -> derleme durmaz)
for pkg in ("google.genai", "pygame", "bs4", "pyttsx3", "comtypes", "PIL"):
    if have(pkg):
        args += ["--collect-all", pkg]

for hidden in ("pyttsx3.drivers.sapi5", "win32com.client", "pythoncom",
               "pywintypes", "google.genai", "psutil", "requests", "pyaudio"):
    if have(hidden.split(".")[0]):
        args += ["--hidden-import", hidden]

args.append("main.py")

print("\n[2/3] PyInstaller calisiyor...")
print("  python -m PyInstaller " + " ".join(args) + "\n")
result = subprocess.run([sys.executable, "-m", "PyInstaller", *args])

# ---- 3) Sonuc ----
exe = HERE / "dist" / ("EXON.exe" if os.name == "nt" else "EXON")
print("\n" + "=" * 60)
if result.returncode == 0 and exe.exists():
    print("  BASARILI!  ->  " + str(exe))
    print("  Bu tek dosyayi paylas; acan kisi Python KURMADAN calistirir.")
    print("  Kullanici verisi exe yanindaki 'EXON_data' klasorunde tutulur.")
else:
    print("  HATA: derleme tamamlanamadi (cikis kodu %s)." % result.returncode)
    print("  Yukaridaki PyInstaller ciktisinda ilk 'ERROR:' satirini bul ve")
    print("  bana yapistir; eksik parcayi tek satirla eklerim.")
    print("  (Acilis hatasini gormek icin --windowed yerine --console ile dene.)")
print("=" * 60)
