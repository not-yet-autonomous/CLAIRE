param([string]$source = "all")
# claire_weekly.ps1
# CLAIRE + CLAIRE-A weekly pipeline runner
# Scheduled via Windows Task Scheduler
<<<<<<< HEAD
Set-Location "C:\DEV\CLAIRE"
& "C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1"

=======

Set-Location "C:\DEV\CLAIRE"
& "C:\DEV\envs\CLAIRE\.venv\Scripts\Activate.ps1"

# Explicitly load API key from .env into the process environment
# Ensures all Python scripts see it regardless of dotenv working directory
>>>>>>> 236a62f (Sanitize: fix hardcoded OneDrive paths in ps1 and scheduler XML)
$envFile = "C:\DEV\CLAIRE\.env"
Get-Content $envFile | Where-Object { $_ -match "^[^#].*=.*" } | ForEach-Object {
    $parts = $_ -split "=", 2
    [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
}

Write-Host "$(Get-Date -Format 'HH:mm:ss')  Starting CLAIRE weekly pipeline..."
python claire_ingest.py --source $source
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

# -- Build 8: Track A cost alert check --------------------------------------
$costLogPath = "data\cost_log.json"
if (Test-Path $costLogPath) {
    try {
        $costLog = Get-Content $costLogPath -Raw | ConvertFrom-Json
        $lastRun = $costLog.runs | Select-Object -Last 1
        if ($lastRun.track_a_alert -eq $true) {
            $synthCost = $lastRun.synthesis_cost_usd
            Write-Warning "Track A cost threshold reached: $([math]::Round($synthCost, 4)) -- review batch size"
        }
    } catch {
        Write-Host "$(Get-Date -Format 'HH:mm:ss')  Could not read cost_log.json for alert check: $_"
    }
}
# ---------------------------------------------------------------------------

python claire_a_runner.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_a_runner.py failed"; exit 1 }
python claire_a_scorer.py
if ($LASTEXITCODE -ne 0) { Write-Host "claire_a_scorer.py failed"; exit 1 }
Write-Host "$(Get-Date -Format 'HH:mm:ss')  CLAIRE-A complete. Weekly run done."

