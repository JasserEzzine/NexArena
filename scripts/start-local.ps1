param([string]$DotnetPath = 'dotnet')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend requirements first. See README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) { throw 'Run python scripts/init-env.py first.' }
Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'backend.log') -RedirectStandardError (Join-Path $projectRoot 'backend-error.log')
Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm.cmd run dev' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'frontend.log') -RedirectStandardError (Join-Path $projectRoot 'frontend-error.log')
Write-Host 'NexArena: http://localhost:5173 | API: http://localhost:8000/docs'
Write-Host 'Logs: backend.log, backend-error.log, frontend.log, frontend-error.log'
