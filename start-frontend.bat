@echo off
chcp 65001 >nul
title Campus RAG - Frontend

set "NODE=C:\Program Files\nodejs\node.exe"
set "PATH=C:\Program Files\nodejs;%PATH%"

echo ========================================
echo   Campus RAG Assistant - Frontend
echo   Node:   %NODE%
echo ========================================
echo.

cd /d "%~dp0frontend"
"%NODE%" node_modules\next\dist\bin\next dev
pause