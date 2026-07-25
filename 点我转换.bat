@echo off
rem ASCII only. Do NOT put Chinese characters in this file:
rem cmd.exe reads .bat with the OEM codepage and UTF-8 text breaks parsing.
cd /d "%~dp0"

echo.
echo   Folder: %CD%
echo.

set "SCRIPT="
for %%F in (*.py) do set "SCRIPT=%%F"
if not defined SCRIPT goto noscript
echo   Script: %SCRIPT%

set "PY="
if exist "%USERPROFILE%\anaconda3\python.exe" set "PY=%USERPROFILE%\anaconda3\python.exe"
if not defined PY if exist "%USERPROFILE%\miniconda3\python.exe" set "PY=%USERPROFILE%\miniconda3\python.exe"
if not defined PY goto trypy
goto run

:trypy
where py >nul 2>nul
if not %errorlevel%==0 goto trypython
set "PY=py"
goto run

:trypython
where python >nul 2>nul
if not %errorlevel%==0 goto nopython
set "PY=python"
goto run

:run
echo   Python: %PY%
echo.
"%PY%" "%SCRIPT%"
echo.
echo   ---- finished, exit code %errorlevel% ----
goto end

:noscript
echo.
echo   ERROR: no .py file found in this folder.
echo   Keep this .bat and the .py script in the SAME folder.
goto end

:nopython
echo.
echo   ERROR: Python not found.
echo   Install Python 3 from https://www.python.org/downloads/
echo   IMPORTANT: tick "Add Python to PATH" during setup.
goto end

:end
echo.
pause
