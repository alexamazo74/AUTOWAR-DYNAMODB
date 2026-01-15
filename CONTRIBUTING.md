# Contributing to AutoWAR

Gracias por contribuir. Este documento describe las prácticas y pasos mínimos para preparar cambios y abrir PRs.

1) Entorno local
- Crear y activar un virtualenv (Windows PowerShell):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

2) Formateo y lint
- Ejecuta antes de crear commits:
  ```powershell
  ruff check src tests
  black src tests
  ```
- Asegúrate de que `black` no modifica archivos antes de subir (el CI puede pedirlo).

3) Tipado y tests
- Ejecuta `mypy` y las pruebas:
  ```powershell
  mypy src tests --config-file mypy.ini
  pytest -q
  ```

4) Preparar cambios y commits
- Usa ramas descriptivas: `feature/<short-desc>` o `fix/<short-desc>`.
- Mensajes de commit claros y cortos. Referencia issues si aplica.

5) Pull Request
- Usa la plantilla de PR; completa la checklist (format, lint, mypy, tests).
- Describe cómo probar los cambios localmente.

6) Endpoints y credenciales
- Para endpoints que interactúan con AWS, configura `.env` con `AWS_*` o utiliza una cuenta de prueba.
- No incluyas claves en commits ni en el cuerpo del PR.

7) CDK y despliegue (opcional)
- El infra se encuentra en `cdk/`. Para desplegar:
  ```powershell
  cd cdk
  npm install
  cdk bootstrap
  cdk deploy --all
  ```

8) Contacto
- Si dudas, abre un issue o menciona a un revisor en el PR.

Gracias por colaborar — sigue las reglas de seguridad y privacidad.
