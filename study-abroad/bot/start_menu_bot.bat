@echo off
REM Double-click to run the Path Abroad menu bot on this PC. Close the window to stop it.
cd /d "%~dp0"
python menu_bot.py --listen
pause
