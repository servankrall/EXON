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
    echo [HATA] Calisan bir Python bulunamadi ya da kurulum BOZUK.
    echo  ^(0x80070002 = python.exe dosyasi yerinde yok; kurulum silinmis/bozulmus.^)
    echo.
    echo  COZUM - Python'u yeniden kur:
    echo   1^) https://www.python.org/downloads/ ^> Python 3.12 indir
    echo   2^) Kurulumda "Add python.exe to PATH" ISARETLI olsun
    echo   3^) "Customize" ^> "tcl/tk and IDLE" ISARETLI olsun
    echo   4^) Kur, sonra bu dosyaya tekrar cift tikla.
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

:: ---- yardimci: aday calisiyorsa PYTHON'a ata (bozuk/eksik yollar temiz atlanir) ----
:try
if defined PYTHON exit /b
set "CAND=%*"
:: Tam yol ise ve dosya yoksa hic deneme (0x80070002 gurultusunu onler)
echo %CAND% | findstr "\\" >nul 2>&1 && ( if not exist %CAND% exit /b )
%CAND% --version >nul 2>&1 && set "PYTHON=%CAND%"
exit /b
