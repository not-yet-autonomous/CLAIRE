@echo off
:: CLAIRE Weekly Pipeline Runner
:: Runs all four pipeline scripts in sequence
:: Called by Windows Task Scheduler — also runnable manually

set PROJECT_ROOT=C:\DEV\CLAIRE
set LOG_FILE=%PROJECT_ROOT%\logs\scheduler.log
set PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe

cd /d "%PROJECT_ROOT%"

:: Timestamp start
echo. >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"
echo CLAIRE run started: %DATE% %TIME% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

:: Step 1 — Ingestion
echo [1/4] Ingestion starting... >> "%LOG_FILE%"
"%PYTHON%" claire_ingest.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [1/4] ERROR: Ingestion failed with code %ERRORLEVEL% >> "%LOG_FILE%"
    echo Continuing to next step... >> "%LOG_FILE%"
) else (
    echo [1/4] Ingestion complete. >> "%LOG_FILE%"
)

:: Step 2 — Triage
echo [2/4] Triage starting... >> "%LOG_FILE%"
"%PYTHON%" claire_triage.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [2/4] ERROR: Triage failed with code %ERRORLEVEL% >> "%LOG_FILE%"
    echo Continuing to next step... >> "%LOG_FILE%"
) else (
    echo [2/4] Triage complete. >> "%LOG_FILE%"
)

:: Step 3 — Synthesis
echo [3/4] Synthesis starting... >> "%LOG_FILE%"
"%PYTHON%" claire_synthesize.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [3/4] ERROR: Synthesis failed with code %ERRORLEVEL% >> "%LOG_FILE%"
    echo Continuing to next step... >> "%LOG_FILE%"
) else (
    echo [3/4] Synthesis complete. >> "%LOG_FILE%"
)

:: Step 4 — Output
echo [4/4] Output generation starting... >> "%LOG_FILE%"
"%PYTHON%" claire_output.py >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [4/4] ERROR: Output failed with code %ERRORLEVEL% >> "%LOG_FILE%"
) else (
    echo [4/4] Output complete. >> "%LOG_FILE%"
)

:: Timestamp end
echo ============================================================ >> "%LOG_FILE%"
echo CLAIRE run finished: %DATE% %TIME% >> "%LOG_FILE%"
echo ============================================================ >> "%LOG_FILE%"

exit /b 0
