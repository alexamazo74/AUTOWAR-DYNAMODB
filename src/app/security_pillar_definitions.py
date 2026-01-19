"""
Security Pillar - 11 Questions and 63 Best Practices
AWS Well-Architected Framework
"""

SECURITY_PILLAR_STRUCTURE = {
    'SEC01': {
        'question': '¿Cómo trabaja su organización en el pilar de seguridad?',
        'description': 'La función de seguridad organizacional',
        'best_practices': 9,
        'aws_services': ['Organizations', 'IAM', 'CloudTrail'],
        'bps': [
            {'id': 'SEC01-BP01', 'title': 'Establecer la función de seguridad organizacional', 'service': 'Organizations'},
            {'id': 'SEC01-BP02', 'title': 'Establecer un programa de capacitación en seguridad', 'service': 'IAM'},
            {'id': 'SEC01-BP03', 'title': 'Mantener la gobernanza actual a través de cambios', 'service': 'CloudTrail'},
            {'id': 'SEC01-BP04', 'title': 'Evaluar y ejecutar tareas de terceros', 'service': 'Organizations'},
            {'id': 'SEC01-BP05', 'title': 'Monitorear y supervisar el personal de seguridad', 'service': 'CloudTrail'},
            {'id': 'SEC01-BP06', 'title': 'Implementar un programa de seguridad por diseño', 'service': 'IAM'},
            {'id': 'SEC01-BP07', 'title': 'Implementar un plan de respuesta a incidentes', 'service': 'CloudTrail'},
            {'id': 'SEC01-BP08', 'title': 'Implementar un programa de seguridad del software', 'service': 'IAM'},
            {'id': 'SEC01-BP09', 'title': 'Aplicar políticas de cumplimiento y gobernanza', 'service': 'Organizations'},
        ]
    },
    'SEC02': {
        'question': '¿Cómo gestiona el acceso de cuentas de AWS?',
        'description': 'Gestión de acceso a cuentas AWS',
        'best_practices': 7,
        'aws_services': ['Organizations', 'IAM', 'STS'],
        'bps': [
            {'id': 'SEC02-BP01', 'title': 'Usar control de acceso basado en atributos (ABAC)', 'service': 'IAM'},
            {'id': 'SEC02-BP02', 'title': 'Usar cuentas de AWS en función de su requisito de carga de trabajo o seguridad', 'service': 'Organizations'},
            {'id': 'SEC02-BP03', 'title': 'Implementar permisos mínimos de acceso a la cuenta', 'service': 'IAM'},
            {'id': 'SEC02-BP04', 'title': 'Usar roles de AWS Organizations SCPs para restringir acceso', 'service': 'Organizations'},
            {'id': 'SEC02-BP05', 'title': 'Implementar el almacenamiento seguro y la rotación de acceso de cuenta', 'service': 'SecretsManager'},
            {'id': 'SEC02-BP06', 'title': 'Implementar procesos de aprovisionamiento y desaprovisionamiento regulares', 'service': 'IAM'},
            {'id': 'SEC02-BP07', 'title': 'Usar ServiceControl Policies para desabilitar ciertas capacidades de servicio', 'service': 'Organizations'},
        ]
    },
    'SEC03': {
        'question': '¿Cómo gestiona identidades de personas?',
        'description': 'Gestión de identidades humanas',
        'best_practices': 8,
        'aws_services': ['Cognito', 'IAM', 'DirectoryService', 'SSO'],
        'bps': [
            {'id': 'SEC03-BP01', 'title': 'Usar el servicio de AWS SSO o AWS Cognito de su proveedor de identidad', 'service': 'Cognito'},
            {'id': 'SEC03-BP02', 'title': 'Usar roles de AWS IAM en lugar de roles de usuarios', 'service': 'IAM'},
            {'id': 'SEC03-BP03', 'title': 'Implementar la autenticación multifactor (MFA)', 'service': 'IAM'},
            {'id': 'SEC03-BP04', 'title': 'Usar credenciales temporales de AWS STS', 'service': 'STS'},
            {'id': 'SEC03-BP05', 'title': 'Implementar un ciclo de vida de credenciales con expiración', 'service': 'IAM'},
            {'id': 'SEC03-BP06', 'title': 'Crear y mantener una lista de autorización de IP confiables', 'service': 'IAM'},
            {'id': 'SEC03-BP07', 'title': 'Usar AWS CloudTrail para monitorear acceso de identidades', 'service': 'CloudTrail'},
            {'id': 'SEC03-BP08', 'title': 'Implementar un programa de revisión de acceso periódica', 'service': 'IAM'},
        ]
    },
    'SEC04': {
        'question': '¿Cómo gestiona identidades de máquinas?',
        'description': 'Gestión de identidades y credenciales programáticas',
        'best_practices': 6,
        'aws_services': ['IAM', 'STS', 'SecretsManager', 'EC2'],
        'bps': [
            {'id': 'SEC04-BP01', 'title': 'Usar roles de IAM para sistemas EC2, Lambda y otros servicios', 'service': 'IAM'},
            {'id': 'SEC04-BP02', 'title': 'Usar credenciales temporales de AWS STS en lugar de credenciales de largo plazo', 'service': 'STS'},
            {'id': 'SEC04-BP03', 'title': 'Usar AWS Secrets Manager o Systems Manager Parameter Store para gestionar secretos', 'service': 'SecretsManager'},
            {'id': 'SEC04-BP04', 'title': 'Usar AWS Systems Manager para ejecutar comandos de administración remota', 'service': 'Systems Manager'},
            {'id': 'SEC04-BP05', 'title': 'Rotar credenciales regularmente', 'service': 'IAM'},
            {'id': 'SEC04-BP06', 'title': 'Implementar monitoreo de credenciales en tránsito', 'service': 'CloudTrail'},
        ]
    },
    'SEC05': {
        'question': '¿Cómo gestiona los permisos?',
        'description': 'Gestión de permisos y autorizaciones',
        'best_practices': 7,
        'aws_services': ['IAM', 'Organizations', 'AccessAnalyzer'],
        'bps': [
            {'id': 'SEC05-BP01', 'title': 'Usar el principio de menor privilegio', 'service': 'IAM'},
            {'id': 'SEC05-BP02', 'title': 'Usar políticas administradas de AWS', 'service': 'IAM'},
            {'id': 'SEC05-BP03', 'title': 'Usar AWS IAM Access Analyzer para validar políticas', 'service': 'AccessAnalyzer'},
            {'id': 'SEC05-BP04', 'title': 'Usar Attribute-Based Access Control (ABAC)', 'service': 'IAM'},
            {'id': 'SEC05-BP05', 'title': 'Usar Condiciones en políticas de IAM', 'service': 'IAM'},
            {'id': 'SEC05-BP06', 'title': 'Implementar una revisión de permisos periódica', 'service': 'IAM'},
            {'id': 'SEC05-BP07', 'title': 'Usar AWS Organizations SCPs para controlar permisos', 'service': 'Organizations'},
        ]
    },
    'SEC06': {
        'question': '¿Cómo detecta y investiga eventos de seguridad?',
        'description': 'Detección de amenazas y investigación de incidentes',
        'best_practices': 7,
        'aws_services': ['CloudTrail', 'Config', 'GuardDuty', 'SecurityHub'],
        'bps': [
            {'id': 'SEC06-BP01', 'title': 'Usar AWS CloudTrail para registrar todas las acciones de API', 'service': 'CloudTrail'},
            {'id': 'SEC06-BP02', 'title': 'Usar AWS Config para registrar cambios de configuración', 'service': 'Config'},
            {'id': 'SEC06-BP03', 'title': 'Usar Amazon GuardDuty para detección de amenazas', 'service': 'GuardDuty'},
            {'id': 'SEC06-BP04', 'title': 'Usar AWS Security Hub para agregación de hallazgos', 'service': 'SecurityHub'},
            {'id': 'SEC06-BP05', 'title': 'Configurar alertas para eventos sospechosos', 'service': 'CloudWatch'},
            {'id': 'SEC06-BP06', 'title': 'Usar VPC Flow Logs para registrar tráfico de red', 'service': 'VPC'},
            {'id': 'SEC06-BP07', 'title': 'Mantener un análisis histórico centralizado de logs', 'service': 'S3'},
        ]
    },
    'SEC07': {
        'question': '¿Cómo protege su infraestructura de red?',
        'description': 'Protección de la infraestructura de red',
        'best_practices': 8,
        'aws_services': ['VPC', 'SecurityGroups', 'WAF', 'Shield', 'PrivateLink'],
        'bps': [
            {'id': 'SEC07-BP01', 'title': 'Crear subredes privadas para recursos que no necesitan acceso a Internet', 'service': 'VPC'},
            {'id': 'SEC07-BP02', 'title': 'Usar grupos de seguridad para restringir tráfico de red', 'service': 'SecurityGroups'},
            {'id': 'SEC07-BP03', 'title': 'Usar listas de control de acceso de red (NACLs) para filtrar tráfico', 'service': 'VPC'},
            {'id': 'SEC07-BP04', 'title': 'Usar AWS WAF para proteger aplicaciones web', 'service': 'WAF'},
            {'id': 'SEC07-BP05', 'title': 'Usar AWS Shield para protección contra DDoS', 'service': 'Shield'},
            {'id': 'SEC07-BP06', 'title': 'Usar AWS PrivateLink para comunicación segura entre servicios', 'service': 'PrivateLink'},
            {'id': 'SEC07-BP07', 'title': 'Implementar inspección profunda de paquetes en el perímetro', 'service': 'VPC'},
            {'id': 'SEC07-BP08', 'title': 'Usar VPN o AWS Direct Connect para conexiones seguras', 'service': 'VPN'},
        ]
    },
    'SEC08': {
        'question': '¿Cómo cifra y protege sus datos en tránsito?',
        'description': 'Protección de datos en tránsito',
        'best_practices': 5,
        'aws_services': ['KMS', 'ACM', 'TLS'],
        'bps': [
            {'id': 'SEC08-BP01', 'title': 'Usar HTTPS/TLS para todo el tráfico en tránsito', 'service': 'ACM'},
            {'id': 'SEC08-BP02', 'title': 'Usar AWS Certificate Manager para gestionar certificados TLS', 'service': 'ACM'},
            {'id': 'SEC08-BP03', 'title': 'Usar VPN o AWS Direct Connect para conexiones seguras', 'service': 'VPN'},
            {'id': 'SEC08-BP04', 'title': 'Usar Transport Layer Security (TLS) 1.2 o superior', 'service': 'TLS'},
            {'id': 'SEC08-BP05', 'title': 'Usar AWS KMS para cifrar datos en aplicaciones', 'service': 'KMS'},
        ]
    },
    'SEC09': {
        'question': '¿Cómo cifra y protege sus datos en reposo?',
        'description': 'Protección de datos en reposo',
        'best_practices': 6,
        'aws_services': ['KMS', 'S3', 'RDS', 'DynamoDB', 'SecretsManager'],
        'bps': [
            {'id': 'SEC09-BP01', 'title': 'Usar AWS KMS para administrar claves de cifrado', 'service': 'KMS'},
            {'id': 'SEC09-BP02', 'title': 'Usar cifrado de lado del servidor para S3', 'service': 'S3'},
            {'id': 'SEC09-BP03', 'title': 'Usar cifrado de base de datos para RDS', 'service': 'RDS'},
            {'id': 'SEC09-BP04', 'title': 'Usar cifrado de DynamoDB', 'service': 'DynamoDB'},
            {'id': 'SEC09-BP05', 'title': 'Usar AWS Secrets Manager para secretos cifrados', 'service': 'SecretsManager'},
            {'id': 'SEC09-BP06', 'title': 'Implementar control de acceso a claves de cifrado', 'service': 'KMS'},
        ]
    },
    'SEC10': {
        'question': '¿Cómo se anticipa, responde y se recupera ante incidentes?',
        'description': 'Respuesta a incidentes y recuperación',
        'best_practices': 6,
        'aws_services': ['CloudTrail', 'CloudWatch', 'Backup', 'RecoveryServices'],
        'bps': [
            {'id': 'SEC10-BP01', 'title': 'Desarrollar un plan de respuesta a incidentes', 'service': 'CloudTrail'},
            {'id': 'SEC10-BP02', 'title': 'Implementar registro centralizado de eventos', 'service': 'CloudTrail'},
            {'id': 'SEC10-BP03', 'title': 'Configurar alertas automáticas para eventos sospechosos', 'service': 'CloudWatch'},
            {'id': 'SEC10-BP04', 'title': 'Mantener copias de seguridad regulares de datos críticos', 'service': 'Backup'},
            {'id': 'SEC10-BP05', 'title': 'Implementar un plan de recuperación ante desastres', 'service': 'RecoveryServices'},
            {'id': 'SEC10-BP06', 'title': 'Realizar pruebas periódicas del plan de respuesta a incidentes', 'service': 'CloudTrail'},
        ]
    },
    'SEC11': {
        'question': '¿Cómo cumple con los requisitos regulatorios?',
        'description': 'Cumplimiento normativo y auditoría',
        'best_practices': 3,
        'aws_services': ['Artifact', 'Config', 'Compliance'],
        'bps': [
            {'id': 'SEC11-BP01', 'title': 'Usar AWS Artifact para acceder a informes de cumplimiento', 'service': 'Artifact'},
            {'id': 'SEC11-BP02', 'title': 'Usar AWS Config Rules para validar cumplimiento continuo', 'service': 'Config'},
            {'id': 'SEC11-BP03', 'title': 'Implementar auditorías regulares de cumplimiento', 'service': 'Artifact'},
        ]
    }
}

# Total: 11 preguntas, 63 Best Practices
TOTAL_QUESTIONS = 11
TOTAL_BEST_PRACTICES = sum(q['best_practices'] for q in SECURITY_PILLAR_STRUCTURE.values())

print(f"Total Security Pillar Questions: {TOTAL_QUESTIONS}")
print(f"Total Best Practices: {TOTAL_BEST_PRACTICES}")
