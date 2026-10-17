# Design Document: Refinar Remediaciones del Pilar de Seguridad

## Overview

Este diseño describe cómo refinar las 63 Best Practices del pilar de Seguridad actualizando sus remediaciones basándose en la guía oficial de AWS Well-Architected Framework. El proceso es similar al ya realizado exitosamente con el pilar de Optimización de Costos.

El sistema actual tiene:
- 2 BPs inline en `handler.py` (SEC01-BP01, SEC01-BP02)
- 61 BPs en `all_bp_evaluations.py` (resto de las BPs)
- Algunas BPs con evaluaciones reales (consultan APIs de AWS)
- Algunas BPs con estado PENDING (no evaluables automáticamente)

El objetivo es actualizar todas las remediaciones para que sean específicas, accionables y alineadas con la columna "¿Cómo evaluar?" de la guía oficial.

## Architecture

### Componentes Principales

1. **Security Evaluator Handler** (`lambda/evaluators/security/handler.py`)
   - Contiene la clase `SecurityEvaluator`
   - Tiene 2 métodos inline: `_evaluate_sec01_bp01()` y `_evaluate_sec01_bp02()`
   - Orquesta la evaluación de las 11 preguntas del pilar

2. **BP Evaluations Module** (`lambda/evaluators/security/all_bp_evaluations.py`)
   - Contiene 61 funciones de evaluación (SEC01-BP03 a SEC11-BP08)
   - Cada función retorna un diccionario con: bp, status, severity, finding, evidence, remediation, risk

3. **Official Guide** (`docs/Kiro/Seguridad.md`)
   - Documento markdown con tabla de BPs
   - Columna "¿Cómo evaluar?" contiene las remediaciones oficiales
   - Fuente de verdad para las remediaciones

### Flujo de Datos

```
Official Guide (Seguridad.md)
    ↓
[Extracción de Remediaciones]
    ↓
[Mapeo BP → Remediation]
    ↓
[Actualización de Funciones]
    ↓
handler.py (2 BPs) + all_bp_evaluations.py (61 BPs)
```

## Components and Interfaces

### 1. Estructura de Retorno de BP

Cada función de evaluación retorna un diccionario con esta estructura:

```python
{
    'bp': str,              # ID de la BP (ej: 'SEC01-BP01')
    'status': str,          # 'COMPLIANT', 'NON_COMPLIANT', 'PENDING_REVIEW'
    'seve