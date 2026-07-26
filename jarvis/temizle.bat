@echo off
setlocal
cd /d "%~dp0"
title EXON - Temizlik

echo.
echo  EXON gereksiz klasorleri temizleniyor...
echo  (kisisel verilere - ayarlar, hafiza, gorseller - DOKUNULMAZ)
echo.

:: PyInstaller / paketleme artiklari
if exist "%~dp0build"   ( rd /s /q "%~dp0build"   & echo  - build\ silindi )
if exist "%~dp0dist"    ( rd /s /q "%~dp0dist"    & echo  - dist\ silindi )
del /q "%~dp0*.spec" >nul 2>&1 & echo  - *.spec silindi

:: Python onbellek klasorleri (tum alt klasorler)
for /d /r %%d in (__pycache__) do if exist "%%d" rd /s /q "%%d"
echo  - __pycache__ klasorleri silindi

:: Yeniden olusan calisma-zamani klasoru
if exist "%~dp0beats"   ( rd /s /q "%~dp0beats"   & echo  - beats\ silindi (yeniden olusur) )

echo.
echo  Temizlik tamamlandi. Baslatmak icin run.bat'a cift tikla.
echo.
pause
endlocal
