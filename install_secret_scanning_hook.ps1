$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot

if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    Write-Error 'Pasta .git nao encontrada. Inicialize ou abra o repositorio Git antes de instalar o hook.'
}

$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Error 'Git nao encontrado no PATH.'
}

$hooksDir = Join-Path $repoRoot '.git\hooks'
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir | Out-Null
}

$hookPath = Join-Path $hooksDir 'pre-push'
$hookContent = @'
#!/usr/bin/env sh
set -eu

ZERO="0000000000000000000000000000000000000000"

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[SECRET-SCAN] ERRO: gitleaks nao encontrado."
  echo "[SECRET-SCAN] Instale o gitleaks e tente novamente."
  echo "[SECRET-SCAN] Windows (winget): winget install gitleaks.gitleaks"
  exit 1
fi

CONFIG_ARGS=""
if [ -f ".gitleaks.toml" ]; then
  CONFIG_ARGS="--config .gitleaks.toml"
fi

RANGES=""
while read local_ref local_sha remote_ref remote_sha
do
  if [ "$local_sha" = "$ZERO" ]; then
    continue
  fi

  if [ "$remote_sha" = "$ZERO" ]; then
    RANGE="$local_sha"
  else
    RANGE="$remote_sha..$local_sha"
  fi

  if [ -z "$RANGES" ]; then
    RANGES="$RANGE"
  else
    RANGES="$RANGES $RANGE"
  fi
done

if [ -z "$RANGES" ]; then
  exit 0
fi

echo "[SECRET-SCAN] Iniciando varredura de segredos antes do push..."

for RANGE in $RANGES
do
  if ! gitleaks git --log-opts "$RANGE" $CONFIG_ARGS --redact --no-banner; then
    echo "[SECRET-SCAN] PUSH BLOQUEADO: segredo potencial detectado."
    echo "[SECRET-SCAN] Corrija o vazamento antes de enviar ao remoto."
    exit 1
  fi
done

echo "[SECRET-SCAN] OK: nenhum segredo detectado nos commits do push."
exit 0
'@

$hookContent = $hookContent -replace "`r`n", "`n"
Set-Content -Path $hookPath -Value $hookContent -NoNewline -Encoding utf8

Write-Output "Hook instalado em: $hookPath"
Write-Output 'Para testar: git push (com alteracoes) ou gitleaks git --log-opts "HEAD~1..HEAD" --redact --no-banner'
