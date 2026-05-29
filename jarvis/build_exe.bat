@echo off
setlocal
cd /d "%~dp0"
title EXON - EXE Derleme (EXON Robotik)

echo Calisan Python araniyor...

:: Adaylari sirayla DENE ve gercekten calisani sec (Microsoft Store stub'i atlanir).
set "PYTHON="
call :try py -3
call :try python
call :try python3
call :try "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
call :try "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
call :try "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
call :try "%PROGRAMFILES%\Python313\python.exe"
call :try "%PROGRAMFILES%\Python312\python.exe"
call :try "%PROGRAMFILES%\Python311\python.exe"

if not defined PYTHON (
    echo.
    echo [HATA] Calisan bir Python bulunamadi.
    echo  - Yazdigin "python" Microsoft Store kisayolu (stub) olabilir; o calismaz.
    echo  - Cozum: https://www.python.org/downloads/ adresinden Python 3.12 kur
    echo    ^("Add Python to PATH" VE "tcl/tk and IDLE" isaretli^).
    echo  - Kurduktan sonra bu dosyaya tekrar cift tikla.
    echo.
    pause & exit /b 1
)

echo Kullanilacak Python: %PYTHON%
%PYTHON% --version
echo.

:: Tum derleme mantigi build_exe.py icinde (saglam, hatayi gizlemez).
%PYTHON% "%~dp0build_exe.py"

echo.
echo (Bu pencere acik. Hata varsa yukari kaydirip 'ERROR' satirini kopyala.)
pause
endlocal
exit /b

:: ---- yardimci: aday calisiyorsa PYTHON'a ata ----
:try
if defined PYTHON exit /b
%* --version >nul 2>&1 && set "PYTHON=%*"
exit /b
