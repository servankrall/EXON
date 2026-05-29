@echo off
setlocal
cd /d "%~dp0"
title EXON - EXE Derleme (EXON Robotik)

:: ---- Python bul ----
set "PYTHON="
where python >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON ( where py >nul 2>&1 && set "PYTHON=py" )
if not defined PYTHON (
    echo [HATA] Python bulunamadi. Derleme icin Python 3.11+ gerekli.
    echo https://www.python.org/downloads/  ("Add Python to PATH" isaretli)
    pause & exit /b 1
)

:: Tum is mantigi build_exe.py icinde (saglam, hatayi gizlemez)
%PYTHON% "%~dp0build_exe.py"

echo.
pause
endlocal
