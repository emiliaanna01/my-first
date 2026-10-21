@echo off
REM Double-click to run the opencode Telegram remote on this PC. Close the window to stop it (and opencode).
cd /d "%~dp0"
python opencode_bot.py
pause
