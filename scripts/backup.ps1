<#
.SYNOPSIS
    Faz backup do MongoDB (via mongodump, rodando dentro do container mongo)
    para a pasta ./backups, e apaga backups mais antigos além da retenção.

.EXAMPLE
    .\scripts\backup.ps1
    .\scripts\backup.ps1 -Retencao 30

.NOTES
    Precisa ser rodado com os containers no ar (docker compose up) e a
    partir da raiz do projeto (onde fica o docker-compose.yml).
#>
param(
    [int]$Retencao = 14  # quantos backups mais recentes manter
)

$ErrorActionPreference = "Stop"

# Lê o nome do banco do .env (com um valor padrão de fallback)
$dbName = "conecta_empresas"
if (Test-Path ".env") {
    $linha = Get-Content ".env" | Where-Object { $_ -match "^MONGO_DB_NAME=" }
    if ($linha) {
        $dbName = ($linha -split "=", 2)[1].Trim()
    }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$arquivo = "backup_${dbName}_${timestamp}.gz"

Write-Host "Fazendo backup de '$dbName' para backups/$arquivo ..."

docker compose exec mongo sh -c "mongodump --db=$dbName --archive=/backups/$arquivo --gzip"

if ($LASTEXITCODE -ne 0) {
    Write-Error "mongodump falhou (código $LASTEXITCODE). Confira se os containers estão rodando (docker compose ps)."
    exit 1
}

Write-Host "Backup criado: backups/$arquivo"

# Retenção: mantém só os N backups mais recentes desse banco
if (Test-Path "backups") {
    $backups = Get-ChildItem -Path "backups" -Filter "backup_${dbName}_*.gz" | Sort-Object LastWriteTime -Descending

    if ($backups.Count -gt $Retencao) {
        $antigos = $backups | Select-Object -Skip $Retencao
        foreach ($b in $antigos) {
            Write-Host "Removendo backup antigo (fora da retenção de $Retencao): $($b.Name)"
            Remove-Item $b.FullName
        }
    }
}
