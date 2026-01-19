// Diccionario de traducciones para campos dinámicos de BP
export const bpTranslations = {
  en: {
    findings: {
      'Organization structure properly configured': 'Organization structure properly configured',
      'SCPs not fully implemented across all OUs': 'SCPs not fully implemented across all OUs',
      'Centralized logging configured': 'Centralized logging configured',
      'Cost allocation tags applied': 'Cost allocation tags applied',
      'AWS Config not enabled in all regions': 'AWS Config not enabled in all regions',
      'Budget alerts configured': 'Budget alerts configured',
      'Governance review needed': 'Governance review needed',
      'Account baseline applied': 'Account baseline applied',
      'Access reviews performed': 'Access reviews performed',
      'Root account access protected': 'Root account access protected',
      'Root account not used for daily tasks': 'Root account not used for daily tasks',
      'Some IAM users using long-term credentials': 'Some IAM users using long-term credentials',
      'Cross-account access properly configured': 'Cross-account access properly configured',
      'Federated access review needed': 'Federated access review needed',
      'Access tokens properly managed': 'Access tokens properly managed',
      'Account switching tracked': 'Account switching tracked',
      'Users without MFA enabled': 'Users without MFA enabled',
      'SSO implemented for federated access': 'SSO implemented for federated access',
      'Password policy incomplete': 'Password policy incomplete',
      'User lifecycle managed': 'User lifecycle managed',
      'VPN and TLS endpoints need review': 'VPN and TLS endpoints need review'
    },
    risks: {
      'No risk': 'No risk',
      'Uncontrolled resource creation': 'Uncontrolled resource creation',
      'Compliance violations not detected': 'Compliance violations not detected',
      'Policies may be outdated': 'Policies may be outdated',
      'Credential compromise exposure': 'Credential compromise exposure',
      'Unauthorized access possible': 'Unauthorized access possible',
      'Account compromise risk': 'Account compromise risk',
      'Weak password acceptance': 'Weak password acceptance',
      'Potential man-in-the-middle attacks': 'Potential man-in-the-middle attacks'
    },
    remediations: {
      'Current state compliant': 'Current state compliant',
      'Attach SCPs to remaining OUs to enforce guardrails': 'Attach SCPs to remaining OUs to enforce guardrails',
      'Enable AWS Config in all regions': 'Enable AWS Config in all regions',
      'Schedule quarterly governance review': 'Schedule quarterly governance review',
      'Migrate to temporary credentials via STS AssumeRole': 'Migrate to temporary credentials via STS AssumeRole',
      'Review and validate federated access configurations': 'Review and validate federated access configurations',
      'Enable MFA for all interactive users immediately': 'Enable MFA for all interactive users immediately',
      'Update policy to require mixed case, numbers, symbols': 'Update policy to require mixed case, numbers, symbols',
      'Use VPC Endpoints for private AWS service access': 'Use VPC Endpoints for private AWS service access',
      'Upgrade to TLS 1.2 minimum': 'Upgrade to TLS 1.2 minimum'
    },
    evidence: {
      'AWS Organizations detected with 5 accounts': 'AWS Organizations detected with 5 accounts',
      'Only 2 out of 5 OUs have SCPs attached': 'Only 2 out of 5 OUs have SCPs attached',
      'CloudTrail logs aggregated in central S3': 'CloudTrail logs aggregated in central S3',
      'All resources tagged with project and cost center': 'All resources tagged with project and cost center',
      'Config only enabled in us-east-1, not in us-west-2': 'Config only enabled in us-east-1, not in us-west-2',
      'Billing alerts set at $5000 threshold': 'Billing alerts set at $5000 threshold',
      'Last governance review was 6 months ago': 'Last governance review was 6 months ago',
      'All accounts have standard baseline config': 'All accounts have standard baseline config',
      'Quarterly access reviews completed': 'Quarterly access reviews completed',
      'MFA enabled on root account': 'MFA enabled on root account',
      'Root access logs show minimal usage': 'Root access logs show minimal usage',
      '4 users with active access keys > 90 days old': '4 users with active access keys > 90 days old',
      'Cross-account roles use external ID': 'Cross-account roles use external ID',
      '15 federated users not reviewed in 3 months': '15 federated users not reviewed in 3 months',
      'Token TTLs set appropriately': 'Token TTLs set appropriately',
      'CloudTrail logs all AssumeRole calls': 'CloudTrail logs all AssumeRole calls',
      '8 out of 22 users lack MFA enabled': '8 out of 22 users lack MFA enabled',
      'AWS SSO configured with 150 users': 'AWS SSO configured with 150 users',
      'Missing uppercase requirement in policy': 'Missing uppercase requirement in policy',
      'Offboarding process documented and tracked': 'Offboarding process documented and tracked',
      'Some endpoints using outdated TLS versions': 'Some endpoints using outdated TLS versions'
    }
  },
  es: {
    findings: {
      'Organization structure properly configured': 'Estructura organizativa configurada correctamente',
      'SCPs not fully implemented across all OUs': 'Las SCPs no están completamente implementadas en todas las OUs',
      'Centralized logging configured': 'Registro centralizado configurado',
      'Cost allocation tags applied': 'Etiquetas de asignación de costos aplicadas',
      'AWS Config not enabled in all regions': 'AWS Config no habilitado en todas las regiones',
      'Budget alerts configured': 'Alertas de presupuesto configuradas',
      'Governance review needed': 'Se necesita revisión de gobernanza',
      'Account baseline applied': 'Línea base de cuenta aplicada',
      'Access reviews performed': 'Revisiones de acceso realizadas',
      'Root account access protected': 'Acceso de cuenta raíz protegido',
      'Root account not used for daily tasks': 'La cuenta raíz no se utiliza para tareas diarias',
      'Some IAM users using long-term credentials': 'Algunos usuarios de IAM utilizan credenciales de larga duración',
      'Cross-account access properly configured': 'Acceso entre cuentas configurado correctamente',
      'Federated access review needed': 'Se necesita revisión de acceso federado',
      'Access tokens properly managed': 'Tokens de acceso gestionados correctamente',
      'Account switching tracked': 'Cambio de cuenta rastreado',
      'Users without MFA enabled': 'Usuarios sin MFA habilitado',
      'SSO implemented for federated access': 'SSO implementado para acceso federado',
      'Password policy incomplete': 'Política de contraseña incompleta',
      'User lifecycle managed': 'Ciclo de vida del usuario gestionado',
      'VPN and TLS endpoints need review': 'VPN y endpoints TLS necesitan revisión'
    },
    risks: {
      'No risk': 'Sin riesgo',
      'Uncontrolled resource creation': 'Creación sin control de recursos',
      'Compliance violations not detected': 'Violaciones de cumplimiento no detectadas',
      'Policies may be outdated': 'Las políticas pueden estar desactualizadas',
      'Credential compromise exposure': 'Exposición a compromiso de credenciales',
      'Unauthorized access possible': 'Acceso no autorizado posible',
      'Account compromise risk': 'Riesgo de compromiso de cuenta',
      'Weak password acceptance': 'Aceptación de contraseñas débiles',
      'Potential man-in-the-middle attacks': 'Potenciales ataques de intermediario'
    },
    remediations: {
      'Current state compliant': 'Estado actual conforme',
      'Attach SCPs to remaining OUs to enforce guardrails': 'Adjuntar SCPs a las OUs restantes para aplicar guardrails',
      'Enable AWS Config in all regions': 'Habilitar AWS Config en todas las regiones',
      'Schedule quarterly governance review': 'Programar revisión trimestral de gobernanza',
      'Migrate to temporary credentials via STS AssumeRole': 'Migrar a credenciales temporales a través de STS AssumeRole',
      'Review and validate federated access configurations': 'Revisar y validar configuraciones de acceso federado',
      'Enable MFA for all interactive users immediately': 'Habilitar MFA para todos los usuarios interactivos inmediatamente',
      'Update policy to require mixed case, numbers, symbols': 'Actualizar política para requerir mayúsculas, números, símbolos',
      'Use VPC Endpoints for private AWS service access': 'Usar VPC Endpoints para acceso privado a servicios AWS',
      'Upgrade to TLS 1.2 minimum': 'Actualizar a TLS 1.2 mínimo'
    },
    evidence: {
      'AWS Organizations detected with 5 accounts': 'AWS Organizations detectado con 5 cuentas',
      'Only 2 out of 5 OUs have SCPs attached': 'Solo 2 de 5 OUs tienen SCPs adjuntas',
      'CloudTrail logs aggregated in central S3': 'Registros de CloudTrail agregados en S3 central',
      'All resources tagged with project and cost center': 'Todos los recursos etiquetados con proyecto y centro de costos',
      'Config only enabled in us-east-1, not in us-west-2': 'Config solo habilitado en us-east-1, no en us-west-2',
      'Billing alerts set at $5000 threshold': 'Alertas de facturación establecidas en umbral de $5000',
      'Last governance review was 6 months ago': 'Última revisión de gobernanza hace 6 meses',
      'All accounts have standard baseline config': 'Todas las cuentas tienen configuración de línea base estándar',
      'Quarterly access reviews completed': 'Revisiones de acceso trimestrales completadas',
      'MFA enabled on root account': 'MFA habilitado en cuenta raíz',
      'Root access logs show minimal usage': 'Los registros de acceso raíz muestran uso mínimo',
      '4 users with active access keys > 90 days old': '4 usuarios con claves de acceso activas > 90 días antiguas',
      'Cross-account roles use external ID': 'Las funciones entre cuentas usan ID externo',
      '15 federated users not reviewed in 3 months': '15 usuarios federados no revisados en 3 meses',
      'Token TTLs set appropriately': 'TTLs de token establecidos apropiadamente',
      'CloudTrail logs all AssumeRole calls': 'CloudTrail registra todas las llamadas AssumeRole',
      '8 out of 22 users lack MFA enabled': '8 de 22 usuarios carecen de MFA habilitado',
      'AWS SSO configured with 150 users': 'AWS SSO configurado con 150 usuarios',
      'Missing uppercase requirement in policy': 'Falta requisito de mayúsculas en política',
      'Offboarding process documented and tracked': 'Proceso de offboarding documentado y rastreado',
      'Some endpoints using outdated TLS versions': 'Algunos endpoints usando versiones de TLS obsoletas'
    }
  }
}

export function translateBPField(fieldType, value, language = 'en') {
  if (!value) return value
  
  const translations = bpTranslations[language] || bpTranslations['en']
  const fieldTranslations = translations[fieldType] || {}
  
  return fieldTranslations[value] || value
}

export function translateFinding(finding, language = 'en') {
  if (!finding) return finding
  
  return {
    ...finding,
    finding: translateBPField('findings', finding.finding, language),
    risk: translateBPField('risks', finding.risk, language),
    remediation: translateBPField('remediations', finding.remediation, language),
    evidence: translateBPField('evidence', finding.evidence, language)
  }
}

export function translateFindings(findings, language = 'en') {
  return findings.map(f => translateFinding(f, language))
}
