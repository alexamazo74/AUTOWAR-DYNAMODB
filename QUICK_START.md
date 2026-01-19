# 🚀 Guía de Inicio - AutoWAR Multi-Language v2.0

## 📍 Acceso Rápido

### Frontend (Vite Dev Server)
- **URL correcta:** http://127.0.0.1:8080
- **NOT:** http://localhost:5173 ❌
- **Puerto:** 8080
- **Estado:** ✅ Ejecutándose

### Backend (FastAPI)
- **URL:** http://127.0.0.1:8002
- **Endpoints:** `/security/evaluate-real`
- **Estado:** ✅ Ejecutándose

## 🎯 Características Nuevas

### ✅ Multi-Idioma Implementado
- **Inglés (EN)** 🇺🇸
- **Español (ES)** 🇪🇸
- Selector visible en:
  - ✅ Formulario de credenciales
  - ✅ Barra de navegación
  - ✅ Todas las pantallas

### ✅ 63 Best Practices Completos
- Todos los BPs mostrados en tablas
- Riesgo individual por BP
- Remediación específica por BP
- 11 preguntas de seguridad

## 📝 Instrucciones de Uso

### 1. Iniciar Backend (si no está corriendo)
```bash
cd c:\AAM\autowar-dynamodb
python -m uvicorn src.app.main:app --reload --port 8002
```

### 2. Iniciar Frontend (si no está corriendo)
```bash
cd c:\AAM\autowar-dynamodb\web
npm run dev
```

### 3. Acceder a la Aplicación
1. Abre navegador: **http://127.0.0.1:8080**
2. Deberías ver la pantalla de credenciales

### 4. Seleccionar Idioma
En el formulario de credenciales:
- Haz clic en **🇺🇸 EN** para inglés
- Haz clic en **🇪🇸 ES** para español
- El cambio es instantáneo

### 5. Ingresar Credenciales (Demo)
Para ver datos de demostración:
- **Access Key:** test
- **Secret Key:** test
- **Account ID:** 123456789012
- **Region:** us-east-1

Click en "🔐 Connect and Evaluate" (EN) o "🔐 Conectar y Evaluar" (ES)

### 6. Explorar el Dashboard
**Panel Principal** muestra:
- Puntuación general (Score)
- 11 Preguntas evaluadas
- 63 Best Practices analizadas
- Hallazgos por severidad (Critical, High, Medium, Low)

### 7. Vista de Analista
Haz clic en **"Analyst View"** (EN) o **"Vista de Analista"** (ES)

Aquí verás:
- **Lista de 11 preguntas** (lado izquierdo)
- **Detalles de cada pregunta** (lado derecho)
- **Tabla con todos los BPs** (desktop)
- **Tarjetas de BPs** (móvil)

### 8. Explorar Best Practices
Cada BP muestra:
| Campo | Descripción |
|-------|-----------|
| BP ID | Identificador (ej: SEC01-BP01) |
| Status | COMPLIANT / NON_COMPLIANT / PENDING_REVIEW |
| Severity | CRITICAL / HIGH / MEDIUM / LOW |
| Finding | Descripción del hallazgo |
| Risk | **NUEVO:** Riesgo específico del BP |
| Remediation | **NUEVO:** Pasos de remediación |
| Evidence | Evidencia de AWS |

## 🌍 Ejemplo de Pantallas

### Englés (EN)
```
┌─────────────────────────────────────┐
│      🔐 AutoWAR - Security Eval     │
│                                     │
│  🇺🇸 EN  |  🇪🇸 ES  (Selector)        │
│                                     │
│  Title: AWS Security Evaluation...  │
│  Subtitle: Enter your credentials.. │
│                                     │
│  Access Key ID: [       ]           │
│  Secret Access Key: [       ]       │
│  Account ID: [       ]              │
│  Region: [       ]                  │
│                                     │
│  🔐 Connect and Evaluate            │
└─────────────────────────────────────┘
```

### Español (ES)
```
┌─────────────────────────────────────┐
│      🔐 AutoWAR - Evaluación        │
│                                     │
│  🇺🇸 EN  |  🇪🇸 ES  (Selector)        │
│                                     │
│  Título: Evaluación de Seguridad... │
│  Subtítulo: Ingrese credenciales... │
│                                     │
│  Access Key ID: [       ]           │
│  Secret Access Key: [       ]       │
│  Account ID: [       ]              │
│  Región: [       ]                  │
│                                     │
│  🔐 Conectar y Evaluar              │
└─────────────────────────────────────┘
```

## 📊 Vistas Disponibles

### 1. Dashboard (Panel Principal)
- **Idioma:** EN/ES seleccionable
- **Muestra:**
  - Puntuación general
  - Resumen de hallazgos
  - Desglose de severidades
  - Información de cuenta/región

### 2. Analyst View (Vista Analista)
- **Idioma:** EN/ES seleccionable
- **Panel Izquierdo:** Lista de 11 preguntas
- **Panel Derecho:** Detalles de pregunta seleccionada
- **Tablas:** Todos los 63 BPs con detalles completos
- **Mobile:** Cambio a tarjetas automático

### 3. Client View (Vista Cliente)
- **Idioma:** EN/ES seleccionable
- **Para:** Presentaciones ejecutivas
- **Muestra:** Resumen de alto nivel

### 4. Reports (Reportes)
- **Idioma:** EN/ES seleccionable
- **Para:** Exportar/generar reportes

## 🔄 Cambiar Idioma en Cualquier Momento

Durante la evaluación:
1. **En el Dashboard:** Haz clic en selector en la barra de navegación
2. **En Analyst View:** Haz clic en selector en la barra de navegación
3. La aplicación se actualiza inmediatamente
4. Los datos se preservan, solo cambia el idioma

## 🛠️ Troubleshooting

### Frontend no carga
**Problema:** "This site can't be reached"
**Solución:**
```bash
# Detener procesos Node
Get-Process node | Stop-Process -Force

# Reiniciar
cd c:\AAM\autowar-dynamodb\web
npm run dev
```

### Backend no responde
**Problema:** "Connection refused"
**Solución:**
```bash
# Detener Python
Get-Process python | Stop-Process -Force

# Reiniciar
cd c:\AAM\autowar-dynamodb
python -m uvicorn src.app.main:app --reload --port 8002
```

### Selector de idioma no aparece
**Problema:** No se ve el selector 🇺🇸 EN 🇪🇸 ES
**Solución:**
- Actualizar página (F5)
- Limpiar cache (Ctrl+Shift+Delete)
- Verificar que i18n.js existe en src/

### Traducciones incompletas
**Problema:** Algunos textos en inglés en pantalla española
**Solución:**
- Abrir DevTools (F12) → Console
- Verificar errores
- Revisar i18n.js

## 📈 Flujo Típico de Usuario

```
1. Abrir http://127.0.0.1:8080
              ↓
2. Ver formulario de credenciales
              ↓
3. Seleccionar idioma (EN/ES)
              ↓
4. Ingresar credenciales demo (test/test)
              ↓
5. Click "Conectar y Evaluar"
              ↓
6. Ver Dashboard con resultados
              ↓
7. Click "Vista de Analista"
              ↓
8. Explorar 11 preguntas y 63 BPs
              ↓
9. Ver tabla con todos los detalles:
   - Status individual
   - Severity
   - Risk (NUEVO)
   - Remediation (NUEVO)
   - Evidence
              ↓
10. Cambiar idioma cuando quiera
```

## 📱 Responsive Design

### Desktop (>1200px)
- ✅ Vista de tabla para 63 BPs
- ✅ Lado a lado (preguntas + detalles)
- ✅ Tabla con 7 columnas

### Tablet (768px - 1200px)
- ✅ Vista de tarjetas
- ✅ Stack vertical
- ✅ Optimizado para touch

### Mobile (<768px)
- ✅ Tarjetas expandibles
- ✅ Una columna
- ✅ Botones grandes

## ✨ Características Adicionales

### Backend en Modo Demo
Cuando usas credenciales de prueba:
- Automáticamente retorna 63 BPs
- Datos realistas por industria
- Severidades distribuidas (2 CRITICAL, 7 HIGH, 10 MEDIUM, 44 LOW)

### Persistencia
- Idioma se guarda en localStorage
- En próximas visitas, carga el idioma anterior
- También carga evaluaciones si están disponibles

### Internacionalización Completa
- ✅ Todos los labels traducidos
- ✅ Todos los títulos traducidos
- ✅ Todos los mensajes traducidos
- ✅ Valores de statuslse traducen

## 🎓 Ejemplos de BPs

### SEC03-BP01 (CRITICAL - MFA)
```
🇺🇸 EN:
BP: SEC03-BP01
Status: NON_COMPLIANT [CRITICAL]
Finding: MFA not enabled for IAM users
Risk: Account compromise risk
Remediation: Enable MFA for all interactive users immediately

🇪🇸 ES:
BP: SEC03-BP01
Estado: NO_CUMPLE [CRÍTICO]
Hallazgo: MFA no habilitado para usuarios IAM
Riesgo: Riesgo de compromiso de cuenta
Remediación: Habilitar MFA para todos los usuarios inmediatamente
```

### SEC07-BP02 (CRITICAL - SSH/RDP)
```
🇺🇸 EN:
BP: SEC07-BP02
Status: NON_COMPLIANT [CRITICAL]
Finding: Security group allows unrestricted SSH/RDP access
Risk: Unauthorized access and network compromise
Remediation: Restrict SSH/RDP to known IP ranges

🇪🇸 ES:
BP: SEC07-BP02
Estado: NO_CUMPLE [CRÍTICO]
Hallazgo: Security group permite acceso SSH/RDP sin restricción
Riesgo: Acceso no autorizado y compromiso de red
Remediación: Restringir SSH/RDP a rangos IP conocidos
```

## ✅ Estado de Implementación

| Feature | Status | Notas |
|---------|--------|-------|
| Frontend EN/ES | ✅ DONE | 200+ términos traducidos |
| Backend 63 BPs | ✅ DONE | Todos con risk y remediation |
| Selector Idioma | ✅ DONE | En todas las pantallas |
| Persistencia | ✅ DONE | localStorage + localStorage |
| Responsive | ✅ DONE | Desktop, tablet, mobile |
| API Integration | ✅ DONE | /security/evaluate-real |
| Estilos | ✅ DONE | Selector y componentes |

## 🎉 ¡Listo para Usar!

Tu aplicación AutoWAR está completamente funcional con:
- ✅ 11 preguntas de seguridad
- ✅ 63 best practices
- ✅ Soporte multi-idioma (EN/ES)
- ✅ Riesgo individual por BP
- ✅ Remediación específica por BP
- ✅ Interfaz responsive
- ✅ API backend funcionando

**Acceso:** http://127.0.0.1:8080 ✅
