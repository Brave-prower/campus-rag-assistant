@echo off
chcp 65001 >nul
title Campus RAG - Backend

set "PYTHON=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.exe"
set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python314;%USERPROFILE%\AppData\Local\Programs\Python\Python314\Scripts;%PATH%"

echo ========================================
echo   Campus RAG Assistant - Backend
echo ========================================
echo.

cd /d "%~dp0backend"

if not exist ".env" (
    echo  [!] 未找到 backend\.env 文件！
    echo      请复制 .env.example 为 .env，填入 DEEPSEEK_API_KEY
    echo.
)

"%PYTHON%" backend_start.py
pause