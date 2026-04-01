$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$envFile = Join-Path $projectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Error: .env が見つかりません: $envFile" -ForegroundColor Red
    exit 1
}

$password = $null
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*POSTGRES_PASSWORD=(.+)$") {
        $password = $matches[1].Trim().Trim('"').Trim("'")
    }
}

if (-not $password) {
    Write-Host "Error: .env に POSTGRES_PASSWORD が設定されていません" -ForegroundColor Red
    exit 1
}

$escaped = $password -replace "'", "''"
$sql = "ALTER USER postgres WITH PASSWORD '$escaped';"

$sql | docker exec -i postgres_db psql -U postgres -d postgres
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "OK: postgres ユーザのパスワードを .env の POSTGRES_PASSWORD に合わせました" -ForegroundColor Green
