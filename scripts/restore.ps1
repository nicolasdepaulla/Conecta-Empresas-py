<#
.SYNOPSIS
    Restaura um backup criado pelo backup.ps1.

    Por padrão, restaura para um banco de TESTE (<nome>_restore_test), pra
    você confirmar que o backup é válido sem tocar nos dados reais. Só mexe
    no banco de verdade se você passar -Producao (e confirmar).

.EXAMPLE
    .\scripts\restore.ps1 -Arquivo backup_conecta_empresas_20260927_140000.gz
    .\scripts\restore.ps1 -Arquivo backup_conecta_empresas_20260927_140000.gz -Producao
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Arquivo,
    [switch]$Producao
)

$ErrorActionPreference = "Stop"

$dbName = "conecta_empresas"
if (Test-Path ".env") {
    $linha = Get-Content ".env" | Where-Object { $_ -match "^MONGO_DB_NAME=" }
    if ($linha) {
        $dbName = ($linha -split "=", 2)[1].Trim()
    }
}

if (-not (Test-Path "backups/$Arquivo")) {
    Write-Error "Arquivo backups/$Arquivo não encontrado. Rode 'docker compose exec mongo ls /backups' pra ver os disponíveis."
    exit 1
}

if ($Producao) {
    Write-Host "ATENÇÃO: isso vai SOBRESCREVER o banco '$dbName' de verdade com o conteúdo de $Arquivo." -ForegroundColor Red
    $confirmacao = Read-Host "Digite 'restaurar' para confirmar"
    if ($confirmacao -ne "restaurar") {
        Write-Host "Cancelado."
        exit 0
    }
    docker compose exec mongo sh -c "mongorestore --archive=/backups/$Arquivo --gzip --drop"
} else {
    $dbTeste = "${dbName}_restore_test"
    Write-Host "Restaurando em banco de teste '$dbTeste' (não mexe nos dados reais)..."
    docker compose exec mongo sh -c "mongorestore --archive=/backups/$Arquivo --gzip --drop --nsFrom='$dbName.*' --nsTo='$dbTeste.*'"

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Restauração de teste concluída. Pra conferir o conteúdo:"
        Write-Host "  docker compose exec mongo mongosh $dbTeste --quiet --eval `"db.getCollectionNames()`""
        Write-Host ""
        Write-Host "Pra apagar o banco de teste depois de conferir:"
        Write-Host "  docker compose exec mongo mongosh $dbTeste --quiet --eval `"db.dropDatabase()`""
    }
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "mongorestore falhou (código $LASTEXITCODE)."
    exit 1
}
