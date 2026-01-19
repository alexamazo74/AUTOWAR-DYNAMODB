Quick frontend demo for AutoWAR Security Evaluations

Run the backend locally (from repo root):

```powershell
# from repository root
python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8002 --log-level info
```

Serve the frontend and open it in a browser:

```powershell
# from repository root
cd frontend
python -m http.server 8080
# then open http://127.0.0.1:8080 in your browser
```

## Available Security Questions & Best Practices

### SEC01 - ¿Cómo opera usted su carga de trabajo de forma segura?
- **SEC01-BP01**: Proteger el usuario raíz de la cuenta y sus propiedades
- **SEC01-BP02**: Usar roles de IAM en lugar de credenciales de largo plazo
- **SEC01-BP03**: Conceder el menor privilegio de acceso
- **SEC01-BP04**: Usar políticas de IAM para el acceso a recursos de AWS
- **SEC01-BP05**: Usar credenciales temporales
- **SEC01-BP06**: Usar políticas administradas de AWS cuando sea posible
- **SEC01-BP07**: Usar el Analizador de acceso de IAM para generar políticas de menor privilegio
- **SEC01-BP08**: Usar credenciales para acceso humano
- **SEC01-BP09**: Usar credenciales para acceso programático

### SEC02 - ¿Cómo gestiona las identidades de personas y máquinas?
- **SEC02-BP01**: Usar proveedores de identidad
- **SEC02-BP02**: Usar credenciales temporales para acceso humano

### SEC03 - ¿Cómo protege los datos confidenciales?
- **SEC03-BP01**: Usar autenticación multifactor (MFA)
- **SEC03-BP02**: Usar cifrado en reposo

### SEC04 - ¿Cómo detecta y investiga los eventos de seguridad?
- **SEC04-BP01**: Usar AWS Config para monitorear configuraciones de recursos

### SEC05 - ¿Cómo protege sus recursos de red?
- **SEC05-BP01**: Usar Amazon GuardDuty para detección de amenazas

## How to Test the Security Evaluations

1. **Open the frontend** at http://127.0.0.1:8080

2. **Evaluate a Security Question:**
   - Select a Question ID from the dropdown
   - Click "POST /security/evaluate"
   - See detailed results with BP descriptions

3. **List Security Evaluations:**
   - Shows all evaluated questions for the evaluation

4. **Get Specific Evaluation:**
   - Get details of a specific question evaluation

5. **Generate Report:**
   - Creates a comprehensive JSON report

## Response Format

Each evaluation returns:
- Question text and description
- Individual BP results with descriptions
- Compliance scores and evidence
- Overall scoring summary

The page provides a complete UI to interact with the Security Service API.
