Resumen de cambios

- Fixes: make `report_generator` compatible with test doubles (`update_item`) and fallback for real DynamoDB (`put_item`).
- Packaging: ensure Python lambda assets use `src/` and include `__init__.py` so Lambdas import correctly.
- Tests: add `pytest.ini` so `src` is on PYTHONPATH; all local tests pass (13/13).
- Infra: add `AUTOWAR_REPORT_QUEUE_URL` env for eval worker; create SQS queues and S3 reports bucket; harder IAM grants.

Evidencia (staging)

S3 report objects:
- reports/eval-e2e-20260115-002/1768509327.json
- reports/eval-e2e-20260115-003/1768509327.json

Ejemplo de items en DynamoDB `autowar-reports` (por `pk`):

- pk: eval-e2e-20260115-002
  - sk: 1768509328
  - status: COMPLETED
  - s3_key: s3://autowar-reports-102080400524-us-east-1/reports/eval-e2e-20260115-002/1768509327.json

- pk: eval-e2e-20260115-002
  - sk: meta
  - status: PENDING
  - metadata: { ... }

Notas

- Tests: ejecutar `pytest` localmente en entorno virtual con `requirements.txt`.
- Recomendación: revisar IAM en `cdk/lib/cdk-stack.ts` antes de mergear.

Cambio propuesto

1. Merge `feature/tests-and-report-fixes` → `main`
2. Run CI and validate IAM
3. Post-merge: consider integrating per-BP scoring UI

Solicitado por: Automatización y limpieza de tests
