# Requirements Document

## Introduction

Este documento especifica los requisitos para refinar las evaluaciones del pilar de Seguridad del sistema AutoWAR, actualizando las remediaciones de las 63 Best Practices (BPs) basándose en la guía oficial de AWS Well-Architected Framework. El objetivo es que todas las BPs tengan remediaciones específicas y precisas según la columna "¿Cómo evaluar?" de la guía oficial, y que las BPs con estado PENDING tengan el riesgo correcto.

## Glossary

- **BP (Best Practice)**: Una práctica recomendada del AWS Well-Architected Framework
- **Remediation**: Acción correctiva específica que se debe tomar cuando una BP no cumple
- **PENDING**: Estado de una BP que no puede ser evaluada automáticamente
- **Security_Pillar**: Pilar de Seguridad del AWS Well-Architected Framework con 11 preguntas y 63 BPs
- **Evaluation_Function**: Función Python que evalúa una BP específica consultando APIs de AWS
- **Official_Guide**: Documento en `docs/Kiro/Seguridad.md` con la columna "¿Cómo evaluar?"

## Requirements

### Requirement 1: Actualizar remediaciones de BPs con evaluaciones reales

**User Story:** Como desarrollador del sistema, quiero que las BPs con evaluaciones reales (que consultan APIs de AWS) tengan remediaciones actualizadas según la guía oficial, para que los usuarios reciban acciones correctivas precisas y alineadas con AWS.

#### Acceptance Criteria

1. WHEN una BP tiene una evaluación real (consulta APIs de AWS), THE System SHALL actualizar su campo 'remediation' con el texto de la columna "¿Cómo evaluar?" de la guía oficial
2. WHEN se actualiza una remediation, THE System SHALL mantener la lógica de evaluación existente sin cambios
3. WHEN una BP tiene múltiples estados posibles (COMPLIANT, NON_COMPLIANT, PENDING_REVIEW), THE System SHALL actualizar la remediation para cada estado según corresponda
4. FOR ALL las 63 BPs del pilar de Seguridad, THE System SHALL verificar que la remediation esté alineada con la guía oficial

### Requirement 2: Actualizar remediaciones de BPs con estado PENDING

**User Story:** Como usuario del sistema, quiero que las BPs con estado PENDING tengan remediaciones específicas de la guía oficial (no genéricas), para entender exactamente qué debo hacer para cumplir con esa BP.

#### Acceptance Criteria

1. WHEN una BP tiene estado PENDING, THE System SHALL usar la remediation específica de la columna "¿Cómo evaluar?" de la guía oficial
2. WHEN una BP tiene estado PENDING, THE System SHALL evitar remediaciones genéricas como "Check IAM permissions" o "Manual review required"
3. WHEN una BP tiene estado PENDING, THE System SHALL incluir acciones concretas y verificables en la remediation
4. FOR ALL las BPs con estado PENDING, THE System SHALL actualizar sus remediations con texto específico de la guía

### Requirement 3: Corregir el campo 'risk' de BPs con estado PENDING

**User Story:** Como usuario del sistema, quiero que las BPs con estado PENDING tengan el riesgo "Por Determinar" en lugar de "Unable to determine" o textos genéricos, para mantener consistencia con el pilar de Optimización de Costos.

#### Acceptance Criteria

1. WHEN una BP tiene estado PENDING_REVIEW, THE System SHALL establecer el campo 'risk' como "Por Determinar"
2. WHEN una BP tiene estado PENDING_REVIEW, THE System SHALL evitar textos como "Unable to determine", "Cannot determine compliance", "May not be applicable"
3. FOR ALL las BPs con estado PENDING_REVIEW, THE System SHALL usar exactamente el texto "Por Determinar" en el campo 'risk'
4. WHEN una BP tiene estado COMPLIANT o NON_COMPLIANT, THE System SHALL mantener el campo 'risk' con su valor específico actual

### Requirement 4: Mantener la estructura de archivos existente

**User Story:** Como desarrollador del sistema, quiero que las modificaciones se realicen en los archivos existentes sin cambiar su estructura, para mantener la compatibilidad con el resto del sistema.

#### Acceptance Criteria

1. WHEN se modifican las BPs, THE System SHALL actualizar únicamente los archivos `lambda/evaluators/security/handler.py` y `lambda/evaluators/security/all_bp_evaluations.py`
2. WHEN se modifica `handler.py`, THE System SHALL actualizar solo las funciones `_evaluate_sec01_bp01` y `_evaluate_sec01_bp02` que están inline
3. WHEN se modifica `all_bp_evaluations.py`, THE System SHALL actualizar las 61 funciones restantes (SEC01-BP03 a SEC11-BP08)
4. WHEN se realizan modificaciones, THE System SHALL mantener la estructura de retorno de cada función (diccionario con keys: bp, status, severity, finding, evidence, remediation, risk)

### Requirement 5: Procesar todas las 63 BPs del pilar de Seguridad

**User Story:** Como usuario del sistema, quiero que todas las 63 BPs del pilar de Seguridad sean refinadas, para tener un pilar completo y consistente con remediaciones precisas.

#### Acceptance Criteria

1. THE System SHALL procesar las 8 BPs de SEC01 (SEC01-BP01 a SEC01-BP08)
2. THE System SHALL procesar las 6 BPs de SEC02 (SEC02-BP01 a SEC02-BP06)
3. THE System SHALL procesar las 9 BPs de SEC03 (SEC03-BP01 a SEC03-BP09)
4. THE System SHALL procesar las 4 BPs de SEC04 (SEC04-BP01 a SEC04-BP04)
5. THE System SHALL procesar las 4 BPs de SEC05 (SEC05-BP01 a SEC05-BP04)
6. THE System SHALL procesar las 5 BPs de SEC06 (SEC06-BP01 a SEC06-BP05)
7. THE System SHALL procesar las 4 BPs de SEC07 (SEC07-BP01 a SEC07-BP04)
8. THE System SHALL procesar las 4 BPs de SEC08 (SEC08-BP01 a SEC08-BP04)
9. THE System SHALL procesar las 3 BPs de SEC09 (SEC09-BP01 a SEC09-BP03)
10. THE System SHALL procesar las 8 BPs de SEC10 (SEC10-BP01 a SEC10-BP08)
11. THE System SHALL procesar las 8 BPs de SEC11 (SEC11-BP01 a SEC11-BP08)

### Requirement 6: Validar consistencia con el pilar de Optimización de Costos

**User Story:** Como desarrollador del sistema, quiero que el formato y estilo de las remediaciones sea consistente con el pilar de Optimización de Costos que ya fue refinado exitosamente, para mantener uniformidad en todo el sistema.

#### Acceptance Criteria

1. WHEN se escriben remediaciones, THE System SHALL usar el mismo estilo y formato que el pilar de Optimización de Costos
2. WHEN una BP tiene estado PENDING, THE System SHALL usar "Por Determinar" en el campo 'risk' (igual que Optimización de Costos)
3. WHEN se escriben remediaciones, THE System SHALL ser específico y accionable (no genérico)
4. WHEN se completa el refinamiento, THE System SHALL tener el mismo nivel de calidad que el pilar de Optimización de Costos
