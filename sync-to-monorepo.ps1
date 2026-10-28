# ============================================================================
#  sync-to-monorepo.ps1
#  Publica la version actual (HEAD) del repo AUTOWAR-DYNAMODB hacia el monorepo
#  de la empresa (gfourmis/internal-aws-solutions), rama solution/base, en la
#  ruta GFourmis/solutions/hub/soluciones/quality/auto-war.
#
#  Modelo: tu desarrollas en esta carpeta y haces push a tu origin (AUTOWAR-
#  DYNAMODB) como siempre. Cuando quieras reflejar un avance en el monorepo de
#  la empresa, ejecuta ESTE script. No desarrollas en el clon-puente.
#
#  Snapshot: exporta SOLO lo trackeado en HEAD, EXCLUYE el layer binario
#  (lambda/layers/reports/python) y .kiro/. No versiona .venv, cdk.out, etc.
#
#  Uso:  powershell -ExecutionPolicy Bypass -File .\sync-to-monorepo.ps1
#        (opcional)  -Message "feat: lo que cambiaste"
# ============================================================================
param(
    [string]$Message = "chore(quality/auto-war): sincronizar snapshot de AutoWAR"
)

$ErrorActionPreference = "Stop"
$env:GIT_TERMINAL_PROMPT = "1"   # permite el prompt de credenciales si hace falta
# Mostrar nombres de archivo no-ASCII tal cual (UTF-8), no con escapes octales.
git config --global core.quotepath false 2>$null | Out-Null

$src    = "c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war"
$bridge = "c:\AAM\Varios\_mono-gfourmis"
$prefix = "GFourmis/solutions/hub/soluciones/quality/auto-war"
$dest   = Join-Path $bridge ($prefix -replace '/', '\')
$tmpTar = Join-Path $env:TEMP ("autowar_snapshot_{0}.tar" -f (Get-Date -Format "yyyyMMddHHmmss"))

Write-Host "==> 1/6  Verificando clon-puente..." -ForegroundColor Cyan
if (-not (Test-Path $bridge)) {
    Write-Host "ERROR: no existe el clon-puente en $bridge." -ForegroundColor Red
    Write-Host "Clona primero: git clone --branch solution/base --single-branch https://github.com/gfourmis/internal-aws-solutions.git `"$bridge`"" -ForegroundColor Yellow
    exit 1
}

Write-Host "==> 2/6  Actualizando el clon-puente (git pull en solution/base)..." -ForegroundColor Cyan
Set-Location $bridge
git checkout solution/base | Out-Null
git pull origin solution/base

Write-Host "==> 3/6  Exportando snapshot de HEAD (excluye layer binario)..." -ForegroundColor Cyan
Set-Location $src
if (Test-Path $tmpTar) { Remove-Item $tmpTar -Force }
git archive --format=tar -o "$tmpTar" HEAD ":(exclude)lambda/layers/reports/python"
if (-not (Test-Path $tmpTar)) { Write-Host "ERROR: no se genero el snapshot." -ForegroundColor Red; exit 1 }

Write-Host "==> 4/6  Reemplazando contenido en el destino..." -ForegroundColor Cyan
if (Test-Path $dest) {
    Get-ChildItem $dest -Force | ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
} else {
    New-Item -ItemType Directory -Path $dest -Force | Out-Null
}
Set-Location $dest
tar --extract --file "$tmpTar"
Remove-Item $tmpTar -Force
# Excluir .kiro/ del snapshot (config local de herramienta)
if (Test-Path (Join-Path $dest ".kiro")) { Remove-Item (Join-Path $dest ".kiro") -Recurse -Force }

# Verificacion anti-mojibake: ningun nombre extraido debe tener caracteres de
# "box-drawing" (U+2500..U+257F) ni el replacement char, tipicos del mojibake de
# UTF-8 mal decodificado. Si aparece, abortar antes de commitear.
$mojibake = Get-ChildItem $dest -Recurse -Force | Where-Object { $_.Name -match '[\u2500-\u257F\uFFFD]' }
if ($mojibake) {
    Write-Host "ERROR: nombres de archivo corruptos (mojibake) tras la extraccion:" -ForegroundColor Red
    $mojibake | ForEach-Object { Write-Host ("  " + $_.FullName) -ForegroundColor Red }
    Write-Host "Aborto antes de commitear. Renombra en el repo de origen los archivos con tildes/n/caracteres especiales a ASCII y reintenta." -ForegroundColor Yellow
    exit 1
}

Write-Host "==> 5/6  Commit en el monorepo..." -ForegroundColor Cyan
Set-Location $bridge
git add -- "$prefix"
$pending = git diff --cached --name-only -- "$prefix"
if (-not $pending) {
    Write-Host "No hay cambios que publicar. El monorepo ya esta al dia." -ForegroundColor Green
    exit 0
}
git commit -m "$Message"

Write-Host "==> 6/6  Push a origin solution/base..." -ForegroundColor Cyan
git push origin solution/base

Write-Host ""
Write-Host "OK: snapshot publicado en solution/base -> $prefix" -ForegroundColor Green
git log --oneline -1 HEAD
