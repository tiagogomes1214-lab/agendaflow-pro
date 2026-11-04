# Cria backup manual do PostgreSQL antes de atualizar ou implantar.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (!(Test-Path '.env')) { throw 'Arquivo .env nao encontrado.' }
$today = Get-Date -Format 'yyyyMMdd-HHmmss'
if (!(Test-Path 'backups')) { New-Item -ItemType Directory -Path 'backups' | Out-Null }
Write-Host "Criando backup PostgreSQL..." -ForegroundColor Cyan
# Executa pg_dump dentro do container; usa credenciais ja disponiveis no DB.
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/agendaflow.backup'
if ($LASTEXITCODE -ne 0) { throw 'pg_dump falhou. Backup nao foi criado.' }
$target = "backups/agendaflow-$today.backup"
docker compose cp 'db:/tmp/agendaflow.backup' $target
if ($LASTEXITCODE -ne 0) { throw 'Falha ao copiar backup.' }
docker compose exec -T db rm -f /tmp/agendaflow.backup | Out-Null
Write-Host "Backup salvo em: $target" -ForegroundColor Green
