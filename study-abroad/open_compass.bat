@echo off
rem Pulls the latest Study Europe Compass from GitHub and opens it in your browser.
cd /d "%~dp0.."
git pull --quiet origin claude/friendly-cerf-x5ro5z
start "" "%~dp0site\index.html"
