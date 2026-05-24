# CLAIRE digest pull -- runs via Task Scheduler after Sunday GHA run
cd "C:\DEV\CLAIRE"
Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
git pull origin main
Write-Host "CLAIRE digest pulled -- $(Get-Date -Format yyyy-MM-dd HH:mm)"
