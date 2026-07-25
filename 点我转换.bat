@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
for %%I in (python.exe) do if exist "%%~$PATH:I" set "PY=python"
if not defined PY for %%I in (py.exe) do if exist "%%~$PATH:I" set "PY=py"

if not defined PY (
    echo.
    echo   没有找到 Python。
    echo   请先安装 Python 3: https://www.python.org/downloads/
    echo   安装时记得勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

"%PY%" "表情转换.py"
if errorlevel 1 pause
