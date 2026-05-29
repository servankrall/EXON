@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
title EXON - EXON Robotik

:: ---- Gecici klasor kontrolu ----
echo %CD% | findstr /i "Temp" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [HATA] Gecici klasorden calistiriliyor. Once kalici bir yere cikarin ^(orn. C:\EXON\^).
    pause & exit /b 1
)

:: ---- Python bul ----
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON ( where py >nul 2>&1 && set "PYTHON=py" )
if not defined PYTHON (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%PROGRAMFILES%\Python313\python.exe"
        "%PROGRAMFILES%\Python312\python.exe"
        "%PROGRAMFILES%\Python311\python.exe"
    ) do ( if exist %%P if not defined PYTHON set "PYTHON=%%P" )
)
if not defined PYTHON (
    echo.
    echo [HATA] Python bulunamadi.
    echo https://www.python.org/downloads/ adresinden Python 3.11+ kurun.
    echo Kurulum sirasinda "Add Python to PATH" kutucugunu MUTLAKA isaretleyin.
    pause & exit /b 1
)

:: ---- Ilk kurulum gerekli mi? ----
set NEED=0
if not exist "%~dp0.exon_installed" set NEED=1
%PYTHON% -c "import google.genai, psutil, PIL, pygame, requests, bs4, pyaudio" >nul 2>&1
if errorlevel 1 set NEED=1

if "%NEED%"=="1" (
    echo.
    echo  ================================================
    echo    EXON ilk kurulum - gerekenler yukleniyor
    echo    Bu yalnizca BIR KEZ yapilir, birkac dakika surebilir.
    echo  ================================================
    echo.
    %PYTHON% -m pip install --upgrade pip
    %PYTHON% -m pip install -r "%~dp0requirements.txt"

    :: Cekirdek paketler hala eksikse teker teker dene
    %PYTHON% -c "import google.genai, psutil, PIL, pygame, requests, bs4" >nul 2>&1
    if errorlevel 1 (
        for %%M in (google-genai psutil Pillow pygame requests beautifulsoup4 pyttsx3 pyperclip pyautogui pygetwindow pywin32) do (
            %PYTHON% -m pip install %%M
        )
    )

    :: PyAudio (ozel)
    %PYTHON% -c "import pyaudio" >nul 2>&1
    if errorlevel 1 (
        echo  PyAudio kuruluyor...
        %PYTHON% -m pip install PyAudio
        %PYTHON% -c "import pyaudio" >nul 2>&1
        if errorlevel 1 (
            %PYTHON% -m pip install pipwin
            %PYTHON% -m pipwin install pyaudio
        )
    )

    :: Opsiyonel ozellikler (basarisiz olursa sorun degil)
    for %%M in (pvporcupine opencv-contrib-python discord.py) do (
        %PYTHON% -m pip install %%M >nul 2>&1
    )

    :: Klasorler + ornek ayar dosyasi
    if not exist "%~dp0config" mkdir "%~dp0config"
    if not exist "%~dp0memory" mkdir "%~dp0memory"
    if not exist "%~dp0config\api_keys.json" if exist "%~dp0config\api_keys.example.json" copy "%~dp0config\api_keys.example.json" "%~dp0config\api_keys.json" >nul

    echo done> "%~dp0.exon_installed"
    echo.
    echo  Kurulum tamamlandi!
    echo.
)

:: ---- Baslat ----
echo EXON baslatiliyor...
%PYTHON% "%~dp0main.py"
set ERR=%ERRORLEVEL%
if %ERR% neq 0 (
    echo.
    echo EXON kapandi ^(hata kodu %ERR%^). Sorun surerse setup.bat calistirin.
    pause
)
endlocal
