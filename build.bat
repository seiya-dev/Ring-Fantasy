@echo off

%~d0
cd %~dp0
rmdir "game/__pycache__" /s /q
pyinstaller --onefile --noconsole --icon "./assets/icon.ico" --add-data "game;game" --add-data "assets;assets" "game.py"
del game.spec
rmdir "build" /s /q
rmdir "game/__pycache__" /s /q

pause
