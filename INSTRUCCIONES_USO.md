# 🚀 Instrucciones de Uso - AutoWAR v2.0

## Estado Actual

✅ **Backend:** http://127.0.0.1:8002 (corriendo)  
✅ **Frontend:** http://localhost:5174 (corriendo)  
✅ **Multi-idioma:** Inglés/Español habilitado  
✅ **63 BPs:** Completamente implementados  

---

## 🔑 Credenciales para Probar

### Opción 1: Modo Demo (Recomendado - Sin credenciales AWS reales)

```
Access Key ID:      test
Secret Access Key:  test
Account ID:         123456789012
Región(es):         us-east-1
```

**Resultado:** Verás datos de ejemplo de 63 BPs de seguridad

### Opción 2: Credenciales AWS Reales

Si tienes credenciales AWS válidas, ingresa:
```
Access Key ID:      AKIA... (tu access key)
Secret Access Key:  wJal... (tu secret key)
Account ID:         123456789012 (el account ID real)
Región(es):         us-east-1,us-west-2 (uno o más, separadas por coma)
```

**Resultado:** Se evaluará tu cuenta AWS real contra los 63 BPs

---

## 📋 Pasos para Usar

### 1. Abre el Frontend
```
http://localhost:5174
```

### 2. Selecciona Idioma
- 🇺🇸 **EN** para Inglés
- 🇪🇸 **ES** para Español

### 3. Ingresa Credenciales
- Para **DEMO**: Usa `test` / `test` / `123456789012`
- Para **AWS Real**: Usa tus credenciales válidas

### 4. Haz Click en "Connect and Evaluate"
El sistema evaluará tu cuenta contra los 11 Security Questions y 63 Best Practices

### 5. Explora los Resultados
- **Dashboard:** Resumen general
- **Analyst View:** Detalle por pregunta con todos los BPs
- **Severity:** CRÍTICO, ALTO, MEDIO, BAJO
- **Status:** CUMPLE, NO_CUMPLE, REVISIÓN_PENDIENTE

---

## 🎯 Qué Ves en la Evaluación

### Para cada Best Practice (BP) ves:
```
┌─────────────────────────────────────────────────────┐
│ BP ID:        SEC01-BP02                           │
│ Status:       NO_CUMPLE (No Compliant)             │
│ Severity:     MEDIO (Medium)                       │
│ Finding:      Description del hallazgo             │
│ Risk:         Descripción del riesgo               │
│ Remediation:  Acciones para remediar               │
│ Evidence:     Lo que se encontró                   │
└─────────────────────────────────────────────────────┘
```

### En Modo Demo:
- ✅ 63 BPs mostrados automáticamente
- ✅ Distribuidos entre los 11 Security Questions
- ✅ Datos de ejemplo realistas
- ✅ Números de hallazgos variados

### En Modo AWS Real:
- ✅ Se conecta a tu cuenta AWS
- ✅ Valida recursos reales
- ✅ Reporta hallazgos actuales
- ❌ Si falla conexión, vuelve automáticamente a datos de ejemplo

---

## ⚠️ Errores Conocidos y Soluciones

### Error: "Credential must have exactly 5 slash-delimited elements..."
**Causa:** Se intentó validar credenciales inválidas con AWS  
**Solución:** 
- Usa credenciales demo: `test` / `test`
- O asegúrate que tus credenciales AWS sean válidas

### Error: "Port 5173 is in use"
**Causa:** Otro proceso usa puerto 5173  
**Solución:** ✅ Automático - Vite usa 5174 en su lugar

### Error: "Cannot connect to backend at 8002"
**Causa:** Backend no está corriendo  
**Solución:**
```powershell
cd c:\AAM\autowar-dynamodb
python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8002
```

---

## 🔄 Cambiar de Idioma en Cualquier Momento

El selector de idioma está en:
1. **Formulario de credenciales** (parte superior)
2. **Barra de navegación** (cuando ya estás autenticado)

Tu selección se guarda automáticamente en el navegador.

---

## 📊 Datos de Ejemplo en Modo Demo

### 11 Preguntas de Seguridad (SEC01-SEC11):
```
SEC01: Organization, Governance & Permissions
SEC02: Identity & Access Management
SEC03: Data Protection & Encryption
SEC04: Detection & Investigation
SEC05: Network Protection
SEC06: Incident Response
SEC07: Data Resilience
SEC08: Supply Chain
SEC09: AWS Account Management
SEC10: Threat Detection
SEC11: Asset Management
```

### 63 Best Practices distribuidos entre estas 11 preguntas

Cada BP incluye:
- Status (Cumple/No cumple/Revisión pendiente)
- Nivel de severidad (Crítico/Alto/Medio/Bajo)
- Hallazgo específico
- Descripción del riesgo
- Remediación recomendada
- Evidencia encontrada

---

## 🎨 Características Multi-idioma

### Traducido al Español:
- ✅ Todas las preguntas (SEC01-SEC11)
- ✅ Todos los 63 BPs
- ✅ Estados y severidades
- ✅ Navegación y controles
- ✅ Formularios
- ✅ Mensajes de error

### Traducido al Inglés:
- ✅ Interfaz completa
- ✅ Igual de completo que español

Cambiar entre idiomas es instantáneo sin recargar la página.

---

## 💾 Persistencia de Datos

- ✅ Selección de idioma: Se guarda en localStorage
- ✅ Credenciales: Se mantienen en sesión (mientras tengas la pestaña abierta)
- ✅ Evaluación: Se guarda mientras explores los datos

---

## 🚀 Próximas Acciones

### Para Probar:
1. Abre http://localhost:5174
2. Selecciona un idioma (EN o ES)
3. Usa credenciales demo: `test` / `test` / `123456789012`
4. Haz click en "Connect and Evaluate"
5. Explora los 63 BPs en la vista de Analyst

### Para Usar con AWS Real:
1. Asegúrate tener credenciales AWS válidas
2. Ingresa tu Access Key, Secret Key, y Account ID
3. Ingresa las regiones a evaluar
4. El sistema conectará a tu cuenta y realizará la evaluación

---

## 📞 URLs Rápidas

| Componente | URL | Estado |
|-----------|-----|--------|
| Frontend | http://localhost:5174 | ✅ Corriendo |
| Backend | http://127.0.0.1:8002 | ✅ Corriendo |
| Health Check | http://127.0.0.1:8002/health | ✅ Disponible |
| API Docs | http://127.0.0.1:8002/docs | ✅ Disponible |

---

## 🎯 Resumen Rápido

```
┌─────────────────────────────────────────────────┐
│ 1. Abre http://localhost:5174                  │
│ 2. Selecciona idioma (EN/ES)                   │
│ 3. Ingresa credenciales demo:                  │
│    - Access Key: test                          │
│    - Secret Key: test                          │
│    - Account ID: 123456789012                  │
│ 4. Click "Connect and Evaluate"                │
│ 5. ¡Explora los 63 BPs!                        │
└─────────────────────────────────────────────────┘
```

**¡Listo para usar!** 🚀
