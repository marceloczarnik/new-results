$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    Write-Error 'Pasta .git nao encontrada. Inicialize ou abra o repositorio Git antes de instalar o pre-commit.'
}

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Error 'Git nao encontrado no PATH.'
}

$preCommitCmd = Get-Command pre-commit -ErrorAction SilentlyContinue
if (-not $preCommitCmd) {
    Write-Error 'pre-commit nao encontrado no PATH. Instale com: pip install pre-commit'
}

$gitleaksCmd = Get-Command gitleaks -ErrorAction SilentlyContinue
if (-not $gitleaksCmd) {
    Write-Error 'gitleaks nao encontrado no PATH. Instale com: winget install gitleaks.gitleaks'
}

pre-commit install
pre-commit install --hook-type pre-push

Write-Output 'pre-commit instalado com sucesso (hooks: pre-commit e pre-push).'
Write-Output 'Teste sugerido: pre-commit run --all-files'
