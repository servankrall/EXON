@echo off
setlocal
cd /d "%~dp0"
title EXON - EXE Derleme (EXON Robotik)

echo.
echo  ================================================
echo    EXON - Tek dosya .exe derleme
echo    Sonuc: indiren kisi Python KURMADAN calistirir
echo  ================================================
echo.

:: ---- Python bul ----
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON ( where py >nul 2>&1 && set "PYTHON=py" )
if not defined PYTHON (
    echo [HATA] Python bulunamadi. Derleme icin Python 3.11+ gerekli.
    pause & exit /b 1
)

:: ---- Once uygulamanin paketleri kurulu olmali (exe bunlari icine gomer) ----
echo [1/3] Gerekli paketler kontrol/kurulum...
%PYTHON% -m pip install --upgrade pip >nul 2>&1
%PYTHON% -m pip install -r "%~dp0requirements.txt"
%PYTHON% -m pip install --upgrade pyinstaller

echo.
echo [2/3] EXON.exe derleniyor... (ilk sefer birkac dakika surebilir)
echo.
:: Ikon olarak EXON.ico varsa kullan (yoksa varsayilan)
set "ICONOPT="
if exist "%~dp0EXON.ico" set "ICONOPT=--icon EXON.ico"

%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name EXON %ICONOPT% ^
  --add-data "SFX;SFX" ^
  --add-data "Icon;Icon" ^
  --add-data "Fonts;Fonts" ^
  --add-data "core;core" ^
  --add-data "config/api_keys.example.json;config" ^
  --collect-all google ^
  --collect-all google.genai ^
  --collect-all pygame ^
  --collect-all bs4 ^
  --collect-all pyttsx3 ^
  --collect-all comtypes ^
  --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import win32com.client ^
  --hidden-import pythoncom ^
  --hidden-import pywintypes ^
  main.py

echo.
echo [3/3] Sonuc:
if exist "%~dp0dist\EXON.exe" (
    echo.
    echo  BASARILI!  ^>^>  dist\EXON.exe
    echo  Bu tek dosyayi paylasabilirsin. Acan kisi Python kurmadan calistirir.
    echo  Kullanici verisi exe'nin yaninda 'EXON_data' klasorunde tutulur.
) else (
    echo.
    echo  [UYARI] Derleme tamamlanamadi. Yukaridaki hata mesajini kontrol et.
    echo  Hata ayiklama icin: bu dosyada --windowed yerine --console yazip tekrar dene
    echo  (boylece acilissta hatayi siyah pencerede gorursun).
)
echo.
pause
endlocal
