@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

:: Temp/RAR klasor kontrolu
echo %CD% | findstr /i "Temp" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [HATA] Gecici klasorden calistiriliyor - once kalici bir yere cikartin.
    echo Ornek: C:\EXON\
    pause & exit /b 1
)

:: ---- Python bul ----
set PYTHON=
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON=python
) else (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "%PROGRAMFILES%\Python314\python.exe"
        "%PROGRAMFILES%\Python313\python.exe"
        "%PROGRAMFILES%\Python312\python.exe"
        "%PROGRAMFILES%\Python311\python.exe"
    ) do (
        if exist %%P if not defined PYTHON set PYTHON=%%P
    )
)

if not defined PYTHON (
    echo [HATA] Python bulunamadi. https://www.python.org/downloads/
    pause & exit /b 1
)

echo EXON Windows baslatiliyor...
echo Python: %PYTHON%
echo.

:: ---- PyAudio kontrol ve otomatik kurulum ----
%PYTHON% -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [BILGI] PyAudio eksik, kuruluyor...

    %PYTHON% -m pip install PyAudio --quiet >nul 2>&1
    %PYTHON% -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! equ 0 goto :pyaudio_ok

    echo  pip basarisiz, pipwin deneniyor...
    %PYTHON% -m pip install pipwin --quiet >nul 2>&1
    %PYTHON% -m pipwin install pyaudio >nul 2>&1
    %PYTHON% -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! equ 0 goto :pyaudio_ok

    %PYTHON% -m pip install PyAudio --only-binary :all: --quiet >nul 2>&1
    %PYTHON% -c "import pyaudio" >nul 2>&1
    if !ERRORLEVEL! equ 0 goto :pyaudio_ok

    echo.
    echo  [UYARI] PyAudio otomatik kurulamadi.
    echo  Manuel cozum - Yonetici CMD'de su komutu calistirin:
    echo    pip install pipwin
    echo    pipwin install pyaudio
    echo.
    echo  ENTER ile devam et, CTRL+C ile cik.
    pause
    goto :deps_check
)

:pyaudio_ok
echo  PyAudio hazir.

:deps_check
:: ---- Diger modul kontrolleri ----
echo Moduller kontrol ediliyor...
%PYTHON% -c "import google.genai" >nul 2>&1
if %ERRORLEVEL% neq 0 echo  [UYARI] google-genai eksik: pip install google-genai
%PYTHON% -c "import psutil" >nul 2>&1
if %ERRORLEVEL% neq 0 echo  [UYARI] psutil eksik: pip install psutil
%PYTHON% -c "import PIL" >nul 2>&1
if %ERRORLEVEL% neq 0 echo  [UYARI] Pillow eksik: pip install Pillow
%PYTHON% -c "import pygame" >nul 2>&1
if %ERRORLEVEL% neq 0 echo  [UYARI] pygame eksik: pip install pygame
%PYTHON% -c "import pyttsx3" >nul 2>&1
if %ERRORLEVEL% neq 0 echo  [UYARI] pyttsx3 eksik: pip install pyttsx3
echo Kontrol tamamlandi.
echo.

:: ---- Baslatma ----
%PYTHON% main.py
set ERR=%ERRORLEVEL%
if %ERR% neq 0 (
    echo.
    echo -----------------------------------------------
    echo EXON kapandi. Hata kodu: %ERR%
    echo -----------------------------------------------
    echo Cozum: setup.bat calistirin veya hata mesajini kontrol edin.
    echo.
    pause
)
endlocal
