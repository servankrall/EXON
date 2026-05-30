@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title EXON - EXON Robotik
color 0B

echo.
echo   ============================================
echo      EXON  -  EXON Robotik
echo      Yapay Zeka Asistani baslatiliyor...
echo   ============================================
echo.

:: ---- Calisan Python bul (bozuk/eksik yollar ve Store stub atlanir) ----
set "PYTHON="
for %%C in (py python python3) do (
    if not defined PYTHON (
        %%C -c "import sys" >nul 2>&1 && set "PYTHON=%%C"
    )
)
if not defined PYTHON (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%PROGRAMFILES%\Python313\python.exe"
        "%PROGRAMFILES%\Python312\python.exe"
    ) do ( if not defined PYTHON if exist %%P ( %%P -c "import sys" >nul 2>&1 && set "PYTHON=%%P" ) )
)

:: ---- Python yoksa OTOMATIK indir + sessiz kur ----
if not defined PYTHON (
    echo   Python bulunamadi. Otomatik indiriliyor ve kuruluyor...
    echo   ^(Bu yalnizca ILK seferde olur, birkac dakika surebilir.^)
    echo.
    set "PYURL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    set "PYEXE=%TEMP%\python_kurulum.exe"
    powershell -Command "try { Invoke-WebRequest -Uri '!PYURL!' -OutFile '!PYEXE!' } catch { exit 1 }"
    if not exist "!PYEXE!" (
        echo   [HATA] Python indirilemedi ^(internet?^). Lutfen elle kur:
        echo   https://www.python.org/downloads/  ^("Add to PATH" isaretli^)
        pause & exit /b 1
    )
    echo   Kuruluyor ^(tcl/tk + PATH dahil^)...
    "!PYEXE!" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_pip=1
    del "!PYEXE!" >nul 2>&1
    :: Yeni kurulan python'u bul
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) do ( if not defined PYTHON if exist %%P set "PYTHON=%%P" )
    if not defined PYTHON ( where python >nul 2>&1 && set "PYTHON=python" )
)

if not defined PYTHON (
    echo   [HATA] Python kurulamadi. Lutfen elle kurup tekrar deneyin:
    echo   https://www.python.org/downloads/
    pause & exit /b 1
)

:: ---- Gerekli paketler (yalnizca ilk acilista) ----
"%PYTHON%" -c "import google.genai, psutil, PIL, pygame, requests, bs4, pyaudio" >nul 2>&1
if errorlevel 1 (
    echo   Gerekenler yukleniyor ^(yalnizca ILK acilista^)...
    echo.
    "%PYTHON%" -m pip install --upgrade pip >nul 2>&1
    "%PYTHON%" -m pip install -r "%~dp0requirements.txt"
    "%PYTHON%" -c "import pyaudio" >nul 2>&1 || "%PYTHON%" -m pip install PyAudio
)

:: ---- Baslat ----
echo.
echo   EXON aciliyor...
"%PYTHON%" "%~dp0main.py"
set ERR=%ERRORLEVEL%
if %ERR% neq 0 (
    echo.
    echo   EXON kapandi ^(kod %ERR%^). Sorun surerse bu pencereyi paylasin.
    pause
)
endlocal
