@echo off
cd /d "%~dp0"
title EXON - TEK DOSYA exe yapma
color 0A
echo.
echo  ============================================
echo    EXON - TEK DOSYA (.exe) olusturucu
echo    Sonuc: dist\EXON.exe  (tek bir dosya)
echo  ============================================
echo.

:: tkinter'li gercek Python'u sec (klasordeki gomulu python.exe elenir)
set "PYTHON="
for %%C in (py python python3) do (
    if not defined PYTHON ( %%C -c "import tkinter" >nul 2>&1 && set "PYTHON=%%C" )
)
if not defined PYTHON (
    echo [HATA] Python bulunamadi. Once EXON normal calismali.
    pause & exit /b 1
)
echo Kullanilan Python: %PYTHON%
%PYTHON% --version
echo.

echo Gerekli arac (PyInstaller) hazirlaniyor...
%PYTHON% -m pip install --upgrade pyinstaller >nul 2>&1

echo.
echo TEK DOSYA derleniyor... Bu BIRKAC DAKIKA surer, lutfen bekle.
echo (Pencereyi KAPATMA.)
echo.

set "ICONOPT="
if exist "%~dp0EXON.ico" set "ICONOPT=--icon EXON.ico"

%PYTHON% -m PyInstaller --noconfirm --clean --onefile --noupx --windowed --name EXON %ICONOPT% ^
  --add-data "SFX;SFX" ^
  --add-data "Icon;Icon" ^
  --add-data "Fonts;Fonts" ^
  --add-data "core;core" ^
  --add-data "config\api_keys.example.json;config" ^
  --collect-submodules google.genai ^
  --copy-metadata google-genai ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import win32com.client ^
  --hidden-import pythoncom ^
  --hidden-import pywintypes ^
  --hidden-import pyaudio ^
  --hidden-import PIL._tkinter_finder ^
  main.py

echo.
if exist "%~dp0dist\EXON.exe" (
    echo  ============================================
    echo   BASARILI!  Tek dosyan hazir:
    echo   %~dp0dist\EXON.exe
    echo  ============================================
    echo  Klasoru aciyorum...
    explorer "%~dp0dist"
) else (
    echo  [UYARI] dist\EXON.exe olusmadi.
    echo  Yukari kaydirip ilk 'ERROR' satirini kopyala ve paylas.
)
echo.
pause
