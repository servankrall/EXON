@echo off
cd /d "%~dp0"
title EXON - Bozuk paketleri onar
color 0E
echo.
echo  ============================================
echo    EXON - Bozuk paket onarimi
echo    (cokme veren paketler yeniden kurulur)
echo  ============================================
echo.

:: tkinter'i olan GERCEK Python'u sec (klasordeki gomulu python.exe elenir)
set "PYTHON="
for %%C in (py python python3) do (
    if not defined PYTHON ( %%C -c "import tkinter" >nul 2>&1 && set "PYTHON=%%C" )
)
if not defined PYTHON (
    for %%C in (py python python3) do (
        if not defined PYTHON ( %%C -c "import sys" >nul 2>&1 && set "PYTHON=%%C" )
    )
)
if not defined PYTHON (
    echo [HATA] Python bulunamadi.
    pause & exit /b 1
)
echo Python: %PYTHON%
%PYTHON% --version
echo.

echo Onbellek temizlenmeden, cokme veren paketler YENIDEN kuruluyor...
echo (Internet gerekir; birkac dakika surebilir)
echo.
for %%P in (pygame pyttsx3 pyautogui pygetwindow pyscreeze pyrect mouseinfo pyperclip comtypes pywin32) do (
    echo --- %%P yeniden kuruluyor ---
    %PYTHON% -m pip install --upgrade --force-reinstall --no-cache-dir %%P
)

echo.
echo  ============================================
echo   Onarim bitti. Simdi TANI.bat ile tekrar test et,
echo   sonra EXON_Baslat.bat ile ac.
echo  ============================================
pause
