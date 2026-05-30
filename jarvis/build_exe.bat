@echo off
cd /d "%~dp0"
echo ================================================
echo    EXON - tek dosya .exe derleme (EXON Robotik)
echo ================================================
echo.
echo Python surumu:
python --version
echo.
echo Derleme basliyor... (ilk sefer birkac dakika surebilir)
echo.

python build_exe.py || py build_exe.py

echo.
echo ================================================
echo  Bitti. 'dist\EXON.exe' olustu mu kontrol et.
echo  Hata varsa yukari kaydirip ERROR satirini kopyala.
echo ================================================
pause
