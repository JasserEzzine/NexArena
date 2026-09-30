# Optional convenience for the local portable PostgreSQL used during development.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pgCtl = Join-Path $projectRoot '.tools\pgsql\bin\pg_ctl.exe'
$pgData = Join-Path $projectRoot '.tools\pgdata'
if (-not (Test-Path -LiteralPath $pgCtl) -or -not (Test-Path -LiteralPath $pgData)) {
    throw 'Portable PostgreSQL is not present. Use docker compose up -d db, or install PostgreSQL as described in README.md.'
}
& $pgCtl -D $pgData status
if ($LASTEXITCODE -eq 0) { Write-Host 'PostgreSQL is already running.'; exit 0 }
& $pgCtl -D $pgData -l (Join-Path $projectRoot '.tools\postgres.log') -o '-h 127.0.0.1 -p 5432' start
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL startup failed. Check .tools/postgres.log.' }
