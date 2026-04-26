@echo off
cd /d "C:\DEV\CLAIRE"
call .venv\Scripts\activate.bat
echo.
echo CLAIRE Project Root: %CD%
echo Venv: Active
echo.
cmd /k