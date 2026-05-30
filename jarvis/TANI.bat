@echo off
cd /d "%~dp0"
title EXON - Tani (cokme sebebi)

:: tkinter'i olan GERCEK Python'u sec (klasordeki gomulu python.exe elenir)
set "PYTHON="
for %%C in (py python python3) do (
    if not defined PYTHON ( %%C -c "import tkinter" >nul 2>&1 && set "PYTHON=%%C" )
)
if not defined PYTHON (
    :: tkinter'i olan yoksa en azindan calisan herhangi bir Python ile calis
    for %%C in (py python python3) do (
        if not defined PYTHON ( %%C -c "import sys" >nul 2>&1 && set "PYTHON=%%C" )
    )
)
if not defined PYTHON (
    echo [HATA] Python bulunamadi.
    pause & exit /b 1
)

echo Kullanilan Python: %PYTHON%
echo.
%PYTHON% tani.py
pause
