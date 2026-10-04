# Jani overnight research queue. Run:  powershell -ExecutionPolicy Bypass -File research\run_overnight.ps1
$py = "C:\Users\artur\miniconda3\envs\jani\python.exe"
$ml = Split-Path -Parent $PSScriptRoot
Set-Location $ml
New-Item -ItemType Directory -Force -Path "$ml\logs" | Out-Null
Write-Host "Starting research queue. Log: $ml\logs\research_sweep.log. Keep mains power on and the lid open."
& $py -u "$PSScriptRoot\sweep.py" @args *>> "$ml\logs\research_sweep.log"
Write-Host "Queue finished with exit code $LASTEXITCODE. See research\overnight\SUMMARY.md"
