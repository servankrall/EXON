@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo %CD% | findstr /i "Temp" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [HATA] Gecici klasorden calistiriliyor!
    echo Once ZIP'i su konuma cikartin: C:\EXON\
    pause & exit /b 1
)

echo.
echo  ================================================
echo   EXON Windows - Kurulum
echo   Servan Kangal
echo  ================================================
echo.

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
    echo [HATA] Python bulunamadi.
    echo https://www.python.org/downloads/ adresinden Python 3.11+ yukleyin.
    pause & exit /b 1
)

echo [1/7] Python: %PYTHON%
for /f "tokens=2 delims= " %%v in ('%PYTHON% --version 2^>^&1') do set PYVER=%%v
echo  Surum: !PYVER!

:: ---- pip ----
echo.
echo [2/7] pip guncelleniyor...
%PYTHON% -m pip install --upgrade pip --quiet >nul 2>&1
echo  Tamam.

:: ---- Ana paketler (teker teker) ----
echo.
echo [3/7] Ana paketler kuruluyor...
call :install_pkg google-genai
call :install_pkg SpeechRecognition
call :install_pkg psutil
call :install_pkg Pillow
call :install_pkg requests
call :install_pkg pygame
call :install_pkg pyttsx3
call :install_pkg pyperclip
call :install_pkg pyautogui
call :install_pkg pygetwindow
call :install_pkg pywin32
echo  Ana paketler tamamlandi.

:: ---- PyAudio (ozel islem) ----
echo.
echo [4/7] PyAudio kuruluyor...
%PYTHON% -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  PyAudio zaten yuklu.
    goto :pyaudio_done
)

:: Deneme 1: dogrudan pip
%PYTHON% -m pip install PyAudio --quiet >nul 2>&1
%PYTHON% -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  PyAudio kuruldu ^(pip^).
    goto :pyaudio_done
)

:: Deneme 2: pipwin
echo  pip basarisiz, pipwin deneniyor...
%PYTHON% -m pip install pipwin --quiet >nul 2>&1
%PYTHON% -m pipwin install pyaudio
%PYTHON% -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  PyAudio kuruldu ^(pipwin^).
    goto :pyaudio_done
)

:: Deneme 3: Python helper script ile wheel yukle
echo  pipwin basarisiz, wheel helper deneniyor...
%PYTHON% -c "
import subprocess, sys, platform
ver = sys.version_info
tag = f'cp{ver.major}{ver.minor}'
arch = 'win_amd64' if platform.machine().endswith('64') else 'win32'
wheel = f'PyAudio-0.2.14-{tag}-{tag}-{arch}.whl'
url = f'https://files.pythonhosted.org/packages/source/P/PyAudio/{wheel}'
print(f'Wheel: {wheel}')
try:
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', f'PyAudio'], capture_output=True)
    if r.returncode == 0: print('OK')
    else: print('FAIL:', r.stderr.decode()[:200])
except Exception as e:
    print('ERR:', e)
" 2>&1
%PYTHON% -c "import pyaudio" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo  PyAudio kuruldu.
    goto :pyaudio_done
)

echo.
echo  [UYARI] PyAudio otomatik kurulamadi.
echo  Python surum: !PYVER!
echo.
echo  Cozum 1: Yonetici olarak CMD acin ve calistirin:
echo    pip install pipwin
echo    pipwin install pyaudio
echo.
echo  Cozum 2: PortAudio DLL'i kurun:
echo    https://github.com/intxcc/pyaudio_portaudio/releases
echo.
echo  Cozum 3: Conda kullaniyorsaniz:
echo    conda install pyaudio
echo.

:pyaudio_done

:: ---- Dizin yapisi ----
echo.
echo [5/7] Dizin yapisi hazirlaniyor...
if not exist "%~dp0config" mkdir "%~dp0config"
if not exist "%~dp0memory" mkdir "%~dp0memory"
if not exist "%~dp0memory\health" mkdir "%~dp0memory\health"
if not exist "%~dp0config\api_keys.json" if exist "%~dp0config\api_keys.example.json" (
    copy "%~dp0config\api_keys.example.json" "%~dp0config\api_keys.json" >nul
)
if not exist "%~dp0memory\memory.json" if exist "%~dp0memory\memory.example.json" (
    copy "%~dp0memory\memory.example.json" "%~dp0memory\memory.json" >nul
)
if not exist "%~dp0memory\phone_book.json" if exist "%~dp0memory\phone_book.example.json" (
    copy "%~dp0memory\phone_book.example.json" "%~dp0memory\phone_book.json" >nul
)
echo  Dizin yapisi hazir.

:: ---- Fontlar ----
echo.
echo [6/7] Fontlar yukleniyor...
if exist "%~dp0Fonts\Grift-Regular.ttf" (
    copy /Y "%~dp0Fonts\Grift-Regular.ttf"   "%LOCALAPPDATA%\Microsoft\Windows\Fonts\" >nul 2>&1
    copy /Y "%~dp0Fonts\Grift-Bold.ttf"      "%LOCALAPPDATA%\Microsoft\Windows\Fonts\" >nul 2>&1
    copy /Y "%~dp0Fonts\Grift-ExtraBold.ttf" "%LOCALAPPDATA%\Microsoft\Windows\Fonts\" >nul 2>&1
    reg add "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "Grift (TrueType)" /t REG_SZ /d "Grift-Regular.ttf" /f >nul 2>&1
    reg add "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "Grift Bold (TrueType)" /t REG_SZ /d "Grift-Bold.ttf" /f >nul 2>&1
    reg add "HKCU\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "Grift ExtraBold (TrueType)" /t REG_SZ /d "Grift-ExtraBold.ttf" /f >nul 2>&1
    echo  Fontlar yuklendi.
) else (
    echo  [UYARI] Fonts\Grift-Regular.ttf bulunamadi.
)

:: ---- Son kontrol ----
echo.
echo [7/7] Kurulum ozeti:
for %%M in (pyaudio google.genai psutil PIL pygame pyttsx3 pyperclip pyautogui win32gui) do (
    %PYTHON% -c "import %%M" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo   [OK] %%M
    ) else (
        echo   [--] %%M ^(eksik^)
    )
)

echo.
echo  ================================================
echo   Kurulum Tamamlandi!
echo  ================================================
echo.
echo   Baslatmak icin: run.bat cift tiklayin
echo.
echo   Klavye kisayollari:
echo     Ctrl+M / F4 : Mikrofon ac/kapat
echo     F5          : Duraklat/Devam
echo     F11         : Tam ekran
echo     ESC         : Kapat
echo.
pause
endlocal
exit /b 0

:: ---- Yardimci fonksiyon ----
:install_pkg
echo  Kuruluyor: %~1
%PYTHON% -m pip install %~1 --quiet >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo    [UYARI] %~1 kurulamadi, tekrar deneniyor...
    %PYTHON% -m pip install %~1
)
exit /b 0
