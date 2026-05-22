# claire_reddit_ingest.ps1
# CLAIRE — Local Reddit ingest with git commit-back
# Schedule: Weekly, Monday 07:00 — runs only when user is logged in

Set-Location "C:\DEV\CLAIRE"

# Activate venv
.\.venv\Scripts\Activate.ps1

# Run ingest
python claire_ingest.py --source reddit
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "logs\reddit_ingest.log" -Value "$timestamp | ERROR | claire_ingest.py --source reddit exited with code $exitCode"
    exit $exitCode
}

# Commit raw_posts.json
git add data/raw_posts.json
git commit -m "Reddit ingest pre-cycle automated $(Get-Date -Format yyyy-MM-dd)"
git push

# Extract post count from ingest.log — last line matching "Reddit:"
$redditLine = (Select-String -Path "logs\ingest.log" -Pattern "Reddit:" | Select-Object -Last 1).Line

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path "logs\reddit_ingest.log" -Value "$timestamp | SUCCESS | $redditLine"
