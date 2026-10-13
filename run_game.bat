@echo off
title Ashes of Oakhaven: The Hollow Crown
echo ========================================================
echo  Menjalankan Ashes of Oakhaven: The Hollow Crown...
echo ========================================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ada masalah saat menjalankan game. Pastikan pygame dan pillow sudah terinstall:
    echo pip install pygame pillow
    pause
)
