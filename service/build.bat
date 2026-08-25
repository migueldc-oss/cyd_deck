@echo off
echo Compilando CYD Stream Deck...

REM Compilar el servicio
pyinstaller --onefile --noconsole --icon=icon.ico --name=CYD_StreamDeck --add-data icon.ico;. cyd_deck_service.py

echo.
echo Compilación completada. Los .exe están en la carpeta 'dist'
pause