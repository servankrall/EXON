@echo off
cd /d "%~dp0"
title EXON - EXE Derleme (EXON Robotik)
echo ================================================
echo    EXON - tek dosya .exe derleme (EXON Robotik)
echo ================================================
echo.

:: tkinter'i olan GERCEK Python'u sec (klasordeki gomulu python.exe elenir)
set "PYTHON="
for %%C in (py python python3) do (
    if not defined PYTHON ( %%C -c "import tkinter" >nul 2>&1 && set "PYTHON=%%C" )
)
if not defined PYTHON (
    echo [HATA] tkinter'li Python bulunamadi. python.org'dan Python 3.12 kur
    echo ^("Add to PATH" + "tcl/tk and IDLE" isaretli^).
    pause & exit /b 1
)

echo Kullanilan Python: %PYTHON%
%PYTHON% --version
echo.
echo Derleme basliyor... (ilk sefer birkac dakika surebilir)
echo.

%PYTHON% build_exe.py

echo.
echo ================================================
echo  Bitti. 'dist\EXON' klasoru ^(veya dist\EXON.exe^) olustu mu kontrol et.
echo  Hata varsa yukari kaydirip ERROR satirini kopyala.
echo ================================================
pause
