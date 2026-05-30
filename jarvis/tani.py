"""
EXON tani araci — 0xC0000005 (kod -1073741819) cokmesinin sebebini bulur.
Kullanim:  python tani.py    (veya TANI.bat'a cift tikla)

Her 'native' modulu AYRI bir surecte test eder; biri cokse bile digerleri devam
eder. Sonunda hangisinin COKERTTIGINI net listeler. Cikti'yi paylasinca
sorumlu modulu kesin biliriz.
EXON Robotik tarafindan gelistirilmistir.
"""

from __future__ import annotations

import subprocess
import sys

# (etiket, import/init kodu) — native cokme riski olanlar onde
TESTS = [
    ("tkinter (arayuz)",        "import tkinter; tkinter.Tk().destroy()"),
    ("PIL / Pillow",            "from PIL import Image, ImageTk"),
    ("psutil",                  "import psutil; psutil.cpu_percent()"),
    ("requests",                "import requests"),
    ("bs4",                     "import bs4"),
    ("google.genai",            "from google import genai"),
    ("pygame (import)",         "import pygame"),
    ("pygame.mixer.init SES",   "import pygame; pygame.mixer.init()"),
    ("pyaudio (import)",        "import pyaudio"),
    ("pyaudio.PyAudio() SES",   "import pyaudio; p=pyaudio.PyAudio(); p.terminate()"),
    ("pywin32 win32gui",        "import win32gui"),
    ("pywin32 win32com",        "import win32com.client"),
    ("pyttsx3 (TTS)",           "import pyttsx3; pyttsx3.init()"),
    ("pyautogui",               "import pyautogui"),
    ("pygetwindow",             "import pygetwindow"),
]

print("=" * 60)
print("  EXON tani - modulleri tek tek test ediyor")
print("=" * 60)

crashed, failed, ok = [], [], []
for label, code in TESTS:
    sys.stdout.write(f"  {label:.<34} ")
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("OK")
        ok.append(label)
    elif r.returncode in (-1073741819, 3221225477, -1073741795, -1073740791):
        print("COKTU (0xC0000005)  <-- SORUMLU OLABILIR")
        crashed.append(label)
    else:
        print(f"hata (kod {r.returncode})")
        err = (r.stderr or "").strip().splitlines()
        if err:
            print("        " + err[-1][:90])
        failed.append(label)

print("\n" + "=" * 60)
print("  OZET")
print("=" * 60)
if crashed:
    print("  COKEN (0xC0000005) modul(ler):")
    for c in crashed:
        print("    - " + c)
    print("\n  >>> Bu satir(lar)i bana yapistir; o modulu guvenli hale getiririm.")
elif failed:
    print("  Cokme yok ama su modul(ler) yuklenemedi:")
    for f in failed:
        print("    - " + f)
    print("\n  Bu listeyi paylas.")
else:
    print("  Tum moduller TEK TEK sorunsuz! Cokme birlikte yuklenince olusuyor.")
    print("  Bu sonucu bana yaz; main.py'de izole baslatma ekleyecegim.")
print("=" * 60)
input("\n  ENTER ile kapat...")
