<#
.SYNOPSIS
    Ejecuta la suite de pruebas automatizadas de AutoWAR.

.DESCRIPTION
    Comando único para correr todas las pruebas (unitarias + estructurales) con
    mocks, sin depender de la cuenta AWS real. Usa el entorno virtual .venv del
    proyecto si existe; si no, usa el python del PATH.

    Por defecto NO corre las pruebas marcadas como 'integration' (que requieren
    credenciales reales). Para incluirlas, pasar -Integration.

.EXAMPLE
    .\run-tests.ps1
    Corre toda la suite con mocks.

.EXAMPLE
    .\run-tests.ps1 -Integration
    Incluye además las pruebas de integración contra la cuenta real.
#>
param(
    [switch]$Integration
)

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot

# Elegir intérprete: .venv del proyecto si existe.
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Write-Host "Usando Python: $python" -ForegroundColor Cyan

if ($Integration) {
    Write-Host "Modo: TODAS las pruebas (incluye integración con AWS real)" -ForegroundColor Yellow
    & $python -m pytest -q
} else {
    Write-Host "Modo: solo pruebas con mocks (integración omitida)" -ForegroundColor Green
    & $python -m pytest -q -m "not integration"
}

exit $LASTEXITCODE
