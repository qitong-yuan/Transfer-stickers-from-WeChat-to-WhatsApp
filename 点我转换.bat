@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=C:\Users\29786\anaconda3\python.exe
if not exist "%PY%" set PY=python
"%PY%" "%~dp0表情转换.py"
if errorlevel 1 pause
