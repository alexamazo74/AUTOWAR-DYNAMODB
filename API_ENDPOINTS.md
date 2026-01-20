# AutoWAR API Endpoints

## 1. Endpoint: POST `/security/evaluate-real`

### Propósito
Realiza evaluación completa de seguridad en los 11 pilares (63 Best Practices) contra una cuenta AWS real.

### Request
```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "session_token": "optional",
  "account_id": "123456789012",
  "regions": ["us-east-1", "us-west-2"]
}
```

### Response
```json
{
  "success": true,
  "evaluation": {
    "id": "security-eval-...",
    "account_id": "123456789012",
    "questions_evaluated": [
      {
        "question_id": "SEC01",
        "question": "Fundamentos de seguridad - Operación segura",
        "findings": [
          {
            "bp": "SEC01-BP01",
            "status": "COMPLIANT|NON_COMPLIANT|PENDING_REVIEW",
            "finding": "...",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "risk": "...",
            "remediation": "...",
            "evidence": "..."
          }
        ],
        "score": 85.5,
        "bps_evaluated": 8
      }
    ],
    "overall_score": 72.3
  }
}
```

### Timeout
- **Timeout total del endpoint**: 60 segundos
- **Timeout por AWS call**: 5 segundos conexión + 10 segundos lectura
- **Si hay timeout**: El finding quedará con `status: PENDING_REVIEW` y `evidence: "Evaluation timeout..."`

---

## 2. Endpoint: POST `/security/re-evaluate-bp`

### Propósito
Re-evalúa solo BPs específicas sin ejecutar la evaluación completa. Ideal para:
- Reintentar BPs que quedaron en timeout
- Resolver un subset de BPs rápidamente
- Actualizar información de BPs específicas

### Request
```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "session_token": "optional",
  "account_id": "123456789012",
  "regions": ["us-east-1"],
  "bp_ids": ["SEC01-BP01", "SEC02-BP03", "SEC05-BP02"]
}
```

### Response
```json
{
  "success": true,
  "evaluated": [
    {
      "success": true,
      "bp_id": "SEC01-BP01",
      "question_id": "SEC01",
      "finding": {
        "bp": "SEC01-BP01",
        "status": "COMPLIANT",
        "finding": "...",
        "severity": "NONE",
        "risk": "N/D",
        "remediation": "N/D",
        "evidence": "..."
      },
      "message": "BP evaluation successful"
    }
  ],
  "failed": [
    {
      "bp_id": "SEC02-BP03",
      "error": "Invalid BP ID"
    }
  ],
  "summary": {
    "evaluated_count": 2,
    "failed_count": 1,
    "timestamp": "2026-01-19T..."
  }
}
```

### Ventajas
- ⚡ **Mucho más rápido** que re-evaluar todo (10-30 segundos vs 60 segundos)
- 🎯 Solo re-procesa las BPs que necesitas
- 💾 No requiere guardar estado de evaluación anterior
- 🔄 Puedes reintentar BPs que tuvieron timeout

### Formato BP ID
Los BP IDs siguen el formato: `SEC##-BP##`
- Ejemplo: `SEC01-BP01`, `SEC02-BP03`, `SEC11-BP08`
- Valid SEC sections: SEC01 → SEC11 (11 pilares)
- Valid BP numbers: varían por sección (BP01 → BP08 máximo)

---

## 3. Endpoint: GET `/security/evaluate-mock`

### Propósito
Retorna datos de evaluación de demostración (sin credenciales AWS reales).

### Response
Misma estructura que `/security/evaluate-real` pero con datos de ejemplo.

### Ventajas
- ✅ No requiere credenciales AWS válidas
- ✅ Responde instantáneamente
- ✅ Ideal para testing/demostración de UI

---

## 4. Entendiendo los estados N/D

Hay **diferentes razones** por las que un finding puede quedar N/D:

### Tipo 1: No hay recursos implementados
```json
{
  "bp": "SEC01-BP03",
  "status": "PENDING_REVIEW",
  "finding": "AWS Config not enabled",
  "risk": "Unable to assess - no resources configured",
  "remediation": "N/D",
  "evidence": "No AWS Config recorders found"  // ← Indica específicamente: no resources
}
```

### Tipo 2: Timeout en evaluación
```json
{
  "bp": "SEC01-BP01",
  "status": "PENDING_REVIEW",
  "finding": "Unable to verify AWS Organizations",
  "risk": "N/D",
  "remediation": "Re-run evaluation to get accurate assessment",
  "evidence": "Evaluation timeout - unable to query AWS Organizations in time limit"  // ← Indica: timeout
}
```

### Tipo 3: Credenciales o permisos insuficientes
```json
{
  "bp": "SEC02-BP01",
  "status": "PENDING_REVIEW",
  "finding": "Unable to verify authentication",
  "risk": "N/D",
  "remediation": "Re-run evaluation to get accurate assessment",
  "evidence": "Evaluation timeout - unable to query IAM in time limit"
}
```

### Cómo distinguir en la UI
- 📍 **Mirar el campo `evidence`**:
  - Si dice `"No ... found"` → No hay recursos implementados
  - Si dice `"Evaluation timeout"` → Hubo timeout, reintentar con `/re-evaluate-bp`
  - Si dice `"N/D"` → Información genérica, requiere investigación

---

## 5. Flujo recomendado de uso

### Evaluación inicial completa
```
POST /security/evaluate-real
  ↓
[Esperar 60 segundos]
  ↓
Revisar resultados
  ↓
¿Hay BPs en PENDING_REVIEW?
  ├─ SI (por timeout) → Ir al paso 2
  └─ NO → Análisis completo
```

### Reintentar BPs específicas
```
POST /security/re-evaluate-bp
  (solo BPs con status PENDING_REVIEW)
  ↓
[Esperar 10-30 segundos]
  ↓
Actualizar UI con nuevos resultados
```

---

## 6. Ejemplos de uso

### Ejemplo 1: Evaluación completa
```bash
curl -X POST http://localhost:8002/security/evaluate-real \
  -H "Content-Type: application/json" \
  -d '{
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "account_id": "123456789012",
    "regions": ["us-east-1"]
  }'
```

### Ejemplo 2: Re-evaluar BPs específicas que tuvieron timeout
```bash
curl -X POST http://localhost:8002/security/re-evaluate-bp \
  -H "Content-Type: application/json" \
  -d '{
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "account_id": "123456789012",
    "regions": ["us-east-1"],
    "bp_ids": ["SEC01-BP01", "SEC02-BP03", "SEC05-BP02"]
  }'
```

### Ejemplo 3: Evaluación de demostración
```bash
curl http://localhost:8002/security/evaluate-mock
```

---

## 7. Scoring y puntuación

### Cálculo de score por Sección (SEC)
```
Score = (BPs COMPLIANT * 100 + BPs PARTIALLY_COMPLIANT * 50) / (Total BPs * 100) * 100

Ejemplos:
- 8/8 COMPLIANT = 100%
- 7/8 COMPLIANT = 87.5%
- 6/8 COMPLIANT, 1/8 PENDING = 75% (PENDING/N/D cuenta como 0%)
- 4/8 COMPLIANT, 4/8 PENDING = 50%
```

### Score general
```
Overall Score = Promedio de los 11 scores SEC01-SEC11
```

### N/D no afecta puntuación negativamente
- BPs con `status: PENDING_REVIEW` (N/D) cuentan como **0 puntos** de esa BP
- No penalizan el score general más allá de su propio valor
- Ejemplo: Si SEC01 tiene 1 BP en timeout de 8 BPs, pierde 12.5 puntos (1/8)

---

## 8. Codes de error comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `InvalidClientTokenId` | Credenciales inválidas | Verificar AWS Access Key ID y Secret |
| `UnrecognizedClientException` | Token expirado | Renovar session token |
| `AccessDenied` | Permisos insuficientes | Agregar IAM permissions necesarios |
| `Evaluation timeout` | AWS call tardó >15 segundos | Reintentar con `/re-evaluate-bp` |
| `Account ID mismatch` | ID de cuenta no coincide | Verificar Account ID enviado |

---

## 9. Headers recomendados

Todos los endpoints aceptan:
```
Content-Type: application/json
```

---

## 10. Rate limiting

Actualmente sin limites. En producción se recomienda:
- Max 1 evaluación completa por cliente por minuto
- Max 10 re-evaluaciones por cliente por minuto
