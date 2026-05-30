"""
EXON exe derleyici — en saglam surum (onedir oncelikli).
Kullanim:  python build_exe.py

0xC0000005 cokmesi cogunlukla --onefile bootloader'indan ve UPX'ten gelir.
Bu yuzden ONCE --onedir (klasor) + --noupx denenir (en guvenilir). Olmazsa
--onefile denenir. PyInstaller temiz kurulup DOGRULANIR.
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
SEP = ";" if os.name == "nt" else ":"
PY = sys.executable


def have(m: str) -> bool:
    try:
        return importlib.util.find_spec(m) is not None
    except Exception:
        return False


def pipi(*pkgs: str) -> None:
    subprocess.run([PY, "-m", "pip", "install", "--upgrade", *pkgs])


print("=" * 60)
print("  EXON - exe derleme (saglam surum)")
print("=" * 60)

# ── 1) Uygulama paketleri ────────────────────────────────────────────────────
print("\n[1/4] Uygulama paketleri kuruluyor...")
subprocess.run([PY, "-m", "pip", "install", "--upgrade", "pip"])
for pkg in ("google-genai", "psutil", "Pillow", "requests", "beautifulsoup4",
            "pygame", "pyttsx3", "pyperclip", "pyautogui", "pygetwindow",
            "pywin32", "comtypes", "pyaudio", "SpeechRecognition"):
    subprocess.run([PY, "-m", "pip", "install", "--upgrade", pkg])

# ── 2) PyInstaller temiz kur + DOGRULA ───────────────────────────────────────
print("\n[2/4] PyInstaller kuruluyor ve dogrulaniyor...")
subprocess.run([PY, "-m", "pip", "uninstall", "-y", "pyinstaller"])
pipi("pyinstaller")
check = subprocess.run([PY, "-m", "PyInstaller", "--version"],
                       capture_output=True, text=True)
if check.returncode != 0:
    print("\n  [HATA] PyInstaller kurulamadi/calismiyor.")
    print("  Cikti:", (check.stderr or check.stdout or "").strip()[:300])
    print("  Elle dene:  python -m pip install --force-reinstall pyinstaller")
    input("\n  ENTER ile cik...")
    sys.exit(1)
print("  PyInstaller surumu:", (check.stdout or "").strip())


def base_args() -> list[str]:
    a = ["--noconfirm", "--clean", "--noupx", "--windowed", "--name", "EXON"]
    if (HERE / "EXON.ico").is_file():
        a += ["--icon", "EXON.ico"]
    for folder in ("SFX", "Icon", "Fonts", "core"):
        if (HERE / folder).is_dir():
            a += ["--add-data", f"{folder}{SEP}{folder}"]
    if (HERE / "config" / "api_keys.example.json").is_file():
        a += ["--add-data", f"config{os.sep}api_keys.example.json{SEP}config"]
    for h in ("pyttsx3.drivers.sapi5", "win32com.client", "pythoncom", "pywintypes",
              "pyaudio", "psutil", "requests", "bs4", "PIL._tkinter_finder"):
        if have(h.split(".")[0]):
            a += ["--hidden-import", h]
    if have("google.genai"):
        a += ["--collect-submodules", "google.genai", "--copy-metadata", "google-genai"]
    return a


def run(mode_args: list[str]) -> bool:
    args = base_args() + mode_args + ["main.py"]
    print("\n  python -m PyInstaller " + " ".join(args) + "\n")
    r = subprocess.run([PY, "-m", "PyInstaller", *args])
    print(f"\n  -> PyInstaller cikis kodu: {r.returncode}")
    return r.returncode == 0


onedir_exe = HERE / "dist" / "EXON" / ("EXON.exe" if os.name == "nt" else "EXON")
onefile_exe = HERE / "dist" / ("EXON.exe" if os.name == "nt" else "EXON")

# ── 3) Deneme 1: onedir (klasor) — EN GUVENILIR ──────────────────────────────
print("\n[3/4] Deneme 1: --onedir (klasor modu, en saglam)...")
run(["--onedir"])
result = "onedir" if onedir_exe.exists() else ""

# ── 4) Deneme 2: onefile (tek dosya) ─────────────────────────────────────────
if not result:
    print("\n[4/4] Deneme 2: --onefile (tek dosya)...")
    run(["--onefile"])
    result = "onefile" if onefile_exe.exists() else ""

# ── Sonuc ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if result in ("onedir", "onefile"):
    out_dir = (HERE / "dist" / "EXON") if result == "onedir" else (HERE / "dist")
    if result == "onedir":
        print("  BASARILI (klasor modu)!")
        print("  ->  dist\\EXON\\  klasorunun TAMAMINI zip'leyip paylas.")
        print("  Acan kisi icindeki EXON.exe'ye cift tiklar; Python GEREKMEZ.")
    else:
        print("  BASARILI (tek dosya)!  ->  dist\\EXON.exe")
        print("  Bu tek dosyayi paylas; acan kisi Python KURMADAN calistirir.")
    print("  Kullanici verisi exe yanindaki 'EXON_data' klasorunde tutulur.")
    # Sonuc klasorunu Explorer'da ac (kolaylik)
    try:
        if os.name == "nt":
            os.startfile(str(out_dir))  # type: ignore[attr-defined]
    except Exception:
        pass
else:
    print("  Iki mod da basarisiz oldu.")
    print("  ALTERNATIF (kesin calisir): exe yerine klasoru zip'le; karsi taraf")
    print("  EXON_Baslat.bat'a tiklar (Python'u bile otomatik kurar).")
    print("  Ya da yukaridaki ilk 'ERROR' satirini bana yapistir.")
print("=" * 60)
input("\n  ENTER ile kapat...")
