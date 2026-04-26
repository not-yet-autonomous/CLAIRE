# claire_weekly.ps1
# CLAIRE + CLAIRE-A weekly pipeline runner
# Scheduled via Windows Task Scheduler

Set-Location "C:\Users\<redacted>\OneDrive\Claude Projects\CLAIRE"
& "C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1"

Write-Host "$(Get-Date -Format 'HH:mm:ss')  Starting CLAIRE weekly pipeline..."

python claire_ingest.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_ingest.py failed"; exit 1 }

python claire_triage.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_triage.py failed"; exit 1 }

python claire_synthesize.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_synthesize.py failed"; exit 1 }

python claire_output.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_output.py failed"; exit 1 }

Write-Host "$(Get-Date -Format 'HH:mm:ss')  CLAIRE complete. Starting CLAIRE-A shadow run..."

python claire_a_assembler.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_a_assembler.py failed"; exit 1 }

python claire_a_runner.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_a_runner.py failed"; exit 1 }

Write-Host "$(Get-Date -Format 'HH:mm:ss')  CLAIRE-A complete. Weekly run done."
