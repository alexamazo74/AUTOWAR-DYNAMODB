# Evidencia de ejecución — Suite de pruebas del pilar de Seguridad (AutoWAR)

Intérprete usado (el del venv del proyecto, Python 3.14):
`c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war\.venv\Scripts\python.exe`

## Comando mandatorio (modo por defecto, integración excluida)

```
c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war\.venv\Scripts\python.exe -m pytest -q -m "not integration"
```

Equivale a `.\run-tests.ps1` (que corre `pytest -q -m "not integration"` con ese mismo venv).

### Resultado final (modo por defecto)

```
90 passed, 1 deselected, 8 xfailed, 3 warnings
RC 0
```

Desglose:
- **90 passed**: 11 de `test_calculations.py` + estructurales por-BP (59 BPs sanas en verde + invariantes de
  pilar) + 14 por-BP explícitas (`test_security_bps.py`).
- **1 deselected**: `test_integration_security.py::test_security_evaluator_against_real_account`
  (marcador `integration`, excluido por `-m "not integration"`).
- **8 xfailed** (4 bugs reales de producción, cada uno evidenciado en 2 sitios — ver
  `bugs-encontrados-seguridad.md`):
  - SEC02-BP05, SEC07-BP02, SEC09-BP01 → `UnboundLocalError` ante AccessDenied.
  - SEC10-BP08 → `description` vacía (clave ausente en `SECURITY_BP_DESCRIPTIONS`).
- **0 failed**.
- 3 warnings: `DeprecationWarning` de `datetime.utcnow()` en código de producción (no es fallo).

## Comando de integración (opcional, se auto-salta sin credenciales)

```
c:\AAM\Varios\internal-aws-solutions\GFourmis\solutions\auto-war\.venv\Scripts\python.exe -m pytest -q -m integration
```

Equivale a `.\run-tests.ps1 -Integration`.

### Resultado (sin credenciales reales en este equipo)

```
1 skipped, 98 deselected
RC 0
```

El único test de integración se SALTÓ limpiamente (no falló): tras `sts.get_caller_identity()` sin
credenciales válidas, hace `pytest.skip(...)`. No se tocó ninguna cuenta AWS.

## Nota sobre la captura de salida en este entorno

La integración de terminal de este equipo truncaba la salida de `python -m pytest` lanzado como
subproceso (devolvía código -1 antes de volcar el resumen). Para obtener el resumen de forma fiable se
ejecutó pytest **en proceso** con un script equivalente (`pytest.main([...])`, mismo venv, mismo
`pytest.ini`, mismos `testpaths=tests`), cuyo resultado es el reportado arriba (NONCE confirmando volcado
fresco). El comando mandatorio `python -m pytest -q -m "not integration"` es el que debe usar el reviewer
en una terminal normal y produce el mismo resultado.

## Archivos de la suite

- `tests/conftest.py` — mock fiel: `ScriptedSession`/`ScriptedClient` sobre clientes boto3 reales
  (preserva `client.exceptions`), fixtures `denying_session` (deny-by-default) y `scripted_session`
  (factory), `iter_bp_invokers` (registro de las 63 BPs), fixture autouse de credenciales/región ficticias.
- `tests/_helpers.py` — constantes del contrato y `assert_finding_contract`.
- `tests/test_calculations.py` — 11 pruebas puras (sin cambios; siguen en verde).
- `tests/test_security_structure.py` — contrato de pilar recorriendo las 63 BPs individualmente
  (59 sanas verdes + 4 con bug `xfail`; invariantes de 11 preguntas, 63 BPs, distribuciones y scores).
- `tests/test_security_bps.py` — rutas explícitas COMPLIANT/NON_COMPLIANT/PENDING_REVIEW/AccessDenied para
  SEC01-BP01, SEC01-BP02, SEC02-BP01 (incluye la ruta `NoSuchEntityException`), + patrón parametrizado
  reutilizable.
- `tests/test_security_bugs.py` — 4 pruebas `xfail` que evidencian los bugs reales.
- `tests/test_integration_security.py` — integración opcional (`@pytest.mark.integration`), auto-skip sin
  credenciales.
- `tests/README.md` — cómo correr la suite y cómo extenderla.
- `.agents/tasks/bugs-encontrados-seguridad.md` — 4 bugs reales documentados (archivo:línea, causa, fix
  propuesto).
