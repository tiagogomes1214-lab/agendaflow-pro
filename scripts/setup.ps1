# Gera um arquivo .env com senhas aleatorias locais. Execute apenas uma vez.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$path = Join-Path $root '.env'
if (Test-Path $path) {
  Write-Host 'O arquivo .env ja existe. Nada foi alterado.' -ForegroundColor Yellow
  exit 0
}
function New-RandomHex([int]$size) {
  $bytes = New-Object byte[] $size
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
  return ([System.BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$adminPassword = New-RandomHex 12
$jwtSecret = New-RandomHex 32
$dbPassword = New-RandomHex 16
$content = [System.IO.File]::ReadAllText((Join-Path $root '.env.example'))
$content = $content.Replace('CHANGE_ME_DB_PASSWORD', $dbPassword)
$content = $content.Replace('CHANGE_ME_ADMIN_PASSWORD', $adminPassword)
$content = $content.Replace('CHANGE_ME_WITH_RANDOM_SECRET_AT_LEAST_32_CHARACTERS', $jwtSecret)
[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))
Write-Host 'Arquivo .env criado com senhas aleatorias.' -ForegroundColor Green
Write-Host 'Usuario do painel: admin@exemplo.com'
Write-Host "Senha do painel: $adminPassword"
Write-Host 'Guarde esta senha em local seguro. NAO envie o arquivo .env ao GitHub.'
