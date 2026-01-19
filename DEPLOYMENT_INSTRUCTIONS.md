# 📦 Instrucciones de Deployment - Security Pillar Reorganizado

## Estado Actual

✅ **Código listo para deployment**
- Frontend compilado exitosamente
- Backend validado
- 63 BPs correctamente distribuidos
- Multiidioma completamente funcional

---

## 🔧 Instalación y Ejecución Local

### Requisitos Previos

```bash
# Node.js v18+
node --version

# Python 3.9+
python --version

# npm/pip actualizados
npm --version
pip --version
```

### Paso 1: Instalar Dependencias

**Backend:**
```bash
cd c:\AAM\autowar-dynamodb
pip install -r requirements.txt
```

**Frontend:**
```bash
cd c:\AAM\autowar-dynamodb\web
npm install
```

### Paso 2: Compilar Frontend (Opcional - ya compilado)

```bash
cd c:\AAM\autowar-dynamodb\web
npm run build
```

**Output esperado:**
```
vite v5.4.21 building for production...
transforming...
✓ 47 modules transformed
dist/assets/index-CLp_FkC9.js   251.51 kB
dist/assets/index-C6GWeIv2.css   22.60 kB
✓ built in 2.34s
```

### Paso 3: Iniciar Servicios

**Terminal 1 - Backend (FastAPI en puerto 8002):**
```bash
cd c:\AAM\autowar-dynamodb
uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8002
```

**Output esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8002
INFO:     Application startup complete
```

**Terminal 2 - Frontend (Vite en puerto 5174):**
```bash
cd c:\AAM\autowar-dynamodb\web
npm run dev
```

**Output esperado:**
```
  VITE v5.4.21  ready in 245 ms

  ➜  Local:   http://localhost:5174/
  ➜  Press q to quit
```

### Paso 4: Acceder a la Aplicación

```
http://localhost:5174
```

---

## 🧪 Testing Checklist

### 1. Verificación de Estructura

- [ ] **Dashboard visible**
  - URL: http://localhost:5174/dashboard
  - Debe mostrar: "Evaluating all 11 Security questions (63 BPs)..."
  
- [ ] **11 Preguntas de Seguridad**
  ```
  SEC01: Fundamentos de Seguridad (8 BPs)
  SEC02: Autenticación (6 BPs)
  SEC03: Permisos (9 BPs)
  SEC04: Detección (4 BPs)
  SEC05: Protección de Red (4 BPs)
  SEC06: Protección de Recursos (5 BPs)
  SEC07: Clasificación de Datos (4 BPs)
  SEC08: Datos en Reposo (4 BPs)
  SEC09: Datos en Tránsito (3 BPs)
  SEC10: Respuesta a Incidentes (8 BPs)
  SEC11: Seguridad de Aplicaciones (8 BPs)
  ```
  Total: **63 BPs**

### 2. Verificación de Multiidioma

- [ ] **Language Selector funciona**
  - Click en 🇺🇸 EN
  - Click en 🇪🇸 ES
  - Interfaz actualiza correctamente

- [ ] **Español completo**
  - Dashboard: "Evaluación del Pilar de Seguridad"
  - Preguntas: Todos los títulos en español
  - Hallazgos: "Hallazgo", "Riesgo", "Remediación", "Evidencia"

- [ ] **Inglés completo**
  - Dashboard: "Security Pillar Evaluation"
  - Preguntas: All titles in English
  - Findings: "Finding", "Risk", "Remediation", "Evidence"

### 3. Verificación de Traducción Dinámica

- [ ] **Cambiar idioma y ver BPs**
  1. Seleccionar pregunta SEC01
  2. Cambiar a ESP
  3. Verificar que los hallazgos cambien a español
  4. Cambiar a EN
  5. Verificar que vuelvan a inglés

### 4. Verificación de Datos Backend

**En navegador, abrir DevTools (F12):**

1. **Network → XHR** y buscar `/evaluate`
2. **Response debe contener:**
   ```json
   {
     "overall_score": 78.5,
     "total_findings": 24,
     "total_best_practices": 63,
     "questions": [
       {
         "question_id": "SEC01",
         "bps_evaluated": 8,
         "findings": [...]
       },
       // ... 10 más (SEC02-SEC11)
     ]
   }
   ```

### 5. Verificación de BPs

En **Analyst View**, verificar cada pregunta:
```
SEC01 → 8 BPs ✓
SEC02 → 6 BPs ✓
SEC03 → 9 BPs ✓
SEC04 → 4 BPs ✓
SEC05 → 4 BPs ✓
SEC06 → 5 BPs ✓
SEC07 → 4 BPs ✓
SEC08 → 4 BPs ✓
SEC09 → 3 BPs ✓
SEC10 → 8 BPs ✓
SEC11 → 8 BPs ✓
Total: 63 ✓
```

---

## 🐛 Solución de Problemas

### Problema: Puerto 5174 en uso

**Síntoma:** `Error: EADDRINUSE: address already in use :::5174`

**Solución:**
```bash
# Encontrar proceso en puerto 5174
netstat -ano | findstr :5174

# Terminar proceso
taskkill /PID <PID> /F

# O cambiar puerto en vite.config.js
```

### Problema: Puerto 8002 en uso

**Síntoma:** `OSError: [Errno 10048] Only one usage of each socket address`

**Solución:**
```bash
# Terminar proceso anterior
lsof -i :8002
kill -9 <PID>

# O especificar puerto diferente
uvicorn src.app.main:app --port 8001
```

### Problema: Módulos de Python no encontrados

**Síntoma:** `ModuleNotFoundError: No module named 'fastapi'`

**Solución:**
```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

### Problema: npm install falla

**Síntoma:** `npm ERR! code ERESOLVE`

**Solución:**
```bash
# Limpiar cache y reinstalar
npm cache clean --force
rm -r node_modules
rm package-lock.json
npm install
```

### Problema: Traducciones no cargan

**Síntoma:** Todo en inglés, selector de idioma no responde

**Solución:**
```bash
# Limpiar localStorage del navegador
# F12 → Console → localStorage.clear()

# Recargar página
```

---

## 📊 Verificación de Compilación

```bash
# Verificar que i18n.js no tiene errores
cd c:\AAM\autowar-dynamodb\web
npm run build 2>&1 | grep -i error

# Verificar Python
python -m py_compile ../src/app/mock_security_evaluator.py

# Verificar mock data
python << EOF
from src.app.mock_security_evaluator import MockSecurityEvaluator
m = MockSecurityEvaluator()
data = m.evaluate_all()
total = sum(q["bps_evaluated"] for q in data["questions"])
print(f"Questions: {len(data['questions'])}, Total BPs: {total}")
EOF
```

---

## 🔐 Credenciales para Testing

### Opción 1: Credenciales AWS Reales
```
Access Key ID: [Tu AWS Access Key]
Secret Access Key: [Tu AWS Secret Key]
Account ID: [Tu AWS Account ID]
Region: [us-east-1, etc.]
```

### Opción 2: LocalStack (Opcional)
Si tienes LocalStack en localhost:4566:
```
Access Key ID: test
Secret Access Key: test
Account ID: 000000000000
Region: us-east-1
Endpoint: http://localhost:4566 (en config de boto3)
```

---

## 📈 Monitoreo de Rendimiento

### Frontend
- **Build time**: ~2.3 segundos
- **JS bundle**: 251.51 KB (77.58 KB gzipped)
- **CSS**: 22.60 KB
- **Initial load**: < 1 segundo

### Backend
- **Evaluación mock**: < 100ms
- **Traducción dinámica**: < 50ms
- **Total round-trip**: < 200ms

---

## 🚀 Deployment a Producción

### 1. Build Optimizado

```bash
# Frontend
cd web
npm run build

# Backend (crear requirements de producción)
pip install --upgrade pip
pip freeze > requirements-prod.txt
```

### 2. Servir Frontend (Nginx/Apache)

**Nginx config ejemplo:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /app/web/dist;
        try_files $uri /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8002;
    }
}
```

### 3. Ejecutar Backend (Gunicorn)

```bash
gunicorn src.app.main:app --workers 4 --bind 0.0.0.0:8002
```

### 4. Variables de Entorno

```bash
# .env
AWS_REGION=us-east-1
CORS_ALLOWED_ORIGINS=https://your-domain.com
DEBUG=False
LOG_LEVEL=info
```

---

## 📝 Logs Útiles

### Backend Logs
```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Nivel DEBUG
export LOG_LEVEL=debug
uvicorn src.app.main:app --log-level debug
```

### Frontend Console
```javascript
// F12 → Console
// Ver logs de i18n
localStorage.setItem('i18nextDebug', 'true');
location.reload();
```

---

## ✅ Checklist de Deployment Final

```
Pre-Deployment:
☐ Todos los tests pasaron
☐ Frontend compila sin errores
☐ Backend validado
☐ 63 BPs correctamente distribuidos
☐ Multiidioma funcionando
☐ Documentación actualizada

Deployment:
☐ Dependencias instaladas
☐ Puertos disponibles (5174, 8002)
☐ Frontend sirviéndose correctamente
☐ Backend respondiendo en /api endpoints
☐ Traducción funciona EN/ES

Post-Deployment:
☐ URL accesible
☐ Dashboard carga correctamente
☐ 11 preguntas visibles
☐ 63 BPs totales
☐ Multiidioma funciona
☐ No hay errores en console
```

---

## 📚 Documentación Relacionada

- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Referencia rápida de cambios
- [SECURITY_PILLAR_REORGANIZATION.md](SECURITY_PILLAR_REORGANIZATION.md) - Detalles técnicos
- [REORGANIZATION_STATUS.md](REORGANIZATION_STATUS.md) - Estado general

---

**¡Listo para deployment! 🚀**

Contactar si hay problemas durante el deployment.
