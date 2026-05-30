@echo off
cd /d "%~dp0"
title EXON - Tani (cokme sebebi)
echo Python ile tani calistiriliyor...
echo.
python tani.py || py tani.py
pause
