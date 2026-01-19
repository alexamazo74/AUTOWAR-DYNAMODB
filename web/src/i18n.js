import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Traducciones
const resources = {
  en: {
    translation: {
      // Navigation
      nav: {
        dashboard: "Dashboard",
        analyst: "Analyst View",
        client: "Client View",
        reports: "Reports",
        logout: "Logout"
      },
      
      // Credentials Form
      credentials: {
        title: "AWS Security Evaluation - AutoWAR",
        subtitle: "Enter your AWS credentials to start the security evaluation",
        accessKey: "Access Key ID",
        secretKey: "Secret Access Key",
        sessionToken: "Session Token (Optional)",
        accountId: "Account ID",
        region: "Region",
        connect: "Connect and Evaluate",
        connecting: "Connecting...",
        demoNote: "For demo: use test/test credentials"
      },
      
      // Dashboard
      dashboard: {
        title: "Security Pillar Evaluation",
        subtitle: "Well-Architected Review - Security Assessment",
        score: "Score",
        questions: "Questions",
        bps: "Best Practices",
        findings: "Findings",
        evaluated: "Evaluated",
        critical: "Critical",
        high: "High",
        medium: "Medium",
        low: "Low",
        compliant: "Compliant",
        nonCompliant: "Non-Compliant",
        pendingReview: "Pending Review",
        questionsBreakdown: "Questions Breakdown",
        question: "Question",
        status: "Status",
        noEvaluation: "No evaluation available",
        loading: "Evaluating all 11 Security questions (63 BPs)...",
        allQuestions: "All 11 Security Questions",
        totalBPs: "Total: 63 best practices"
      },
      
      // Analyst View
      analyst: {
        title: "Analyst View - AutoWAR",
        subtitle: "Detailed technical analysis by question and best practice",
        securityQuestions: "Security Questions (63 BPs)",
        total: "Total",
        findings: "findings",
        questionSummary: "Question Summary",
        bpsLabel: "BPs",
        findingsLabel: "Findings",
        statusLabel: "Status",
        good: "Good",
        improve: "Improve",
        selectQuestion: "Select a question to view detailed analysis",
        selectHelp: "Click on any question in the left panel to view its details, findings, and compliance status.",
        noFindings: "No findings - All BPs compliant",
        evidence: "Evidence",
        risk: "Risk",
        remediation: "Remediation"
      },
      
      // Client View
      client: {
        title: "Client Executive View",
        subtitle: "High-level security posture summary",
        overallScore: "Overall Score",
        totalQuestions: "Total Questions",
        totalBPs: "Best Practices",
        complianceRate: "Compliance Rate",
        keyFindings: "Key Findings",
        criticalIssues: "Critical Issues",
        recommendations: "Top Recommendations",
        noData: "No evaluation data available"
      },
      
      // Severity levels
      severity: {
        critical: "CRITICAL",
        high: "HIGH",
        medium: "MEDIUM",
        low: "LOW"
      },
      
      // Status levels
      status: {
        compliant: "COMPLIANT",
        nonCompliant: "NON_COMPLIANT",
        pendingReview: "PENDING_REVIEW"
      },
      
      // Questions titles
      questions: {
        sec01: {
          title: "Fundamentos de Seguridad - ¿Cómo opera su carga de trabajo?",
          description: "Security fundamentals and operational security"
        },
        sec02: {
          title: "Autenticación - ¿Cómo se gestiona la autenticación?",
          description: "Authentication and identity management"
        },
        sec03: {
          title: "Permisos - ¿Cómo se gestionan los permisos?",
          description: "Authorization and permission management"
        },
        sec04: {
          title: "Detección - ¿Cómo se detectan e investigan eventos?",
          description: "Event detection and investigation"
        },
        sec05: {
          title: "Protección de Red - ¿Cómo protege su red?",
          description: "Network protection and isolation"
        },
        sec06: {
          title: "Protección de Recursos - ¿Cómo protege sus recursos?",
          description: "Resource protection and hardening"
        },
        sec07: {
          title: "Clasificación de Datos - ¿Cómo clasifica sus datos?",
          description: "Data classification and organization"
        },
        sec08: {
          title: "Datos en Reposo - ¿Cómo protege sus datos en reposo?",
          description: "Data encryption at rest"
        },
        sec09: {
          title: "Datos en Tránsito - ¿Cómo protege sus datos en tránsito?",
          description: "Data encryption in transit"
        },
        sec10: {
          title: "Respuesta a Incidentes - ¿Cómo anticipa y responde a incidentes?",
          description: "Incident response and recovery"
        },
        sec11: {
          title: "Seguridad de Aplicaciones - ¿Cómo incorpora seguridad en el ciclo de vida?",
          description: "Application security and development lifecycle"
        }
      },
      
      // Table headers
      table: {
        bpId: "BP ID",
        status: "Status",
        severity: "Severity",
        finding: "Finding",
        risk: "Risk",
        remediation: "Remediation",
        evidence: "Evidence"
      },
      
      // Common
      common: {
        noRisk: "No risk",
        compliantState: "Current state compliant",
        notAvailable: "N/A"
      }
    }
  },
  es: {
    translation: {
      // Navegación
      nav: {
        dashboard: "Panel Principal",
        analyst: "Vista de Analista",
        client: "Vista de Cliente",
        reports: "Reportes",
        logout: "Cerrar Sesión"
      },
      
      // Formulario de Credenciales
      credentials: {
        title: "Evaluación de Seguridad AWS - AutoWAR",
        subtitle: "Ingrese sus credenciales AWS para iniciar la evaluación de seguridad",
        accessKey: "Access Key ID",
        secretKey: "Secret Access Key",
        sessionToken: "Session Token (Opcional)",
        accountId: "Account ID",
        region: "Región",
        connect: "Conectar y Evaluar",
        connecting: "Conectando...",
        demoNote: "Para demo: use credenciales test/test"
      },
      
      // Panel Principal
      dashboard: {
        title: "Evaluación del Pilar de Seguridad",
        subtitle: "Well-Architected Review - Evaluación de Seguridad",
        score: "Puntuación",
        questions: "Preguntas",
        bps: "Mejores Prácticas",
        findings: "Hallazgos",
        evaluated: "Evaluados",
        critical: "Crítico",
        high: "Alto",
        medium: "Medio",
        low: "Bajo",
        compliant: "Cumple",
        nonCompliant: "No Cumple",
        pendingReview: "Revisión Pendiente",
        questionsBreakdown: "Desglose de Preguntas",
        question: "Pregunta",
        status: "Estado",
        noEvaluation: "No hay evaluación disponible",
        loading: "Evaluando las 11 preguntas de Seguridad (63 BPs)...",
        allQuestions: "Las 11 Preguntas de Seguridad",
        totalBPs: "Total: 63 mejores prácticas"
      },
      
      // Vista de Analista
      analyst: {
        title: "Vista de Analista - AutoWAR",
        subtitle: "Análisis técnico detallado por pregunta y mejor práctica",
        securityQuestions: "Preguntas de Seguridad (63 BPs)",
        total: "Total",
        findings: "hallazgos",
        questionSummary: "Resumen de la Pregunta",
        bpsLabel: "BPs",
        findingsLabel: "Hallazgos",
        statusLabel: "Estado",
        good: "Bien",
        improve: "Mejorar",
        selectQuestion: "Selecciona una pregunta para ver el análisis detallado",
        selectHelp: "Haz clic en cualquier pregunta del panel izquierdo para ver sus detalles, hallazgos y estado de cumplimiento.",
        noFindings: "Sin hallazgos - Todos los BPs cumplen",
        evidence: "Evidencia",
        risk: "Riesgo",
        remediation: "Remediación"
      },
      
      // Vista de Cliente
      client: {
        title: "Vista Ejecutiva de Cliente",
        subtitle: "Resumen de alto nivel del estado de seguridad",
        overallScore: "Puntuación General",
        totalQuestions: "Total de Preguntas",
        totalBPs: "Mejores Prácticas",
        complianceRate: "Tasa de Cumplimiento",
        keyFindings: "Hallazgos Clave",
        criticalIssues: "Problemas Críticos",
        recommendations: "Principales Recomendaciones",
        noData: "No hay datos de evaluación disponibles"
      },
      
      // Niveles de severidad
      severity: {
        critical: "CRÍTICO",
        high: "ALTO",
        medium: "MEDIO",
        low: "BAJO"
      },
      
      // Niveles de estado
      status: {
        compliant: "CUMPLE",
        nonCompliant: "NO_CUMPLE",
        pendingReview: "REVISION_PENDIENTE"
      },
      
      // Títulos de preguntas
      questions: {
        sec01: {
          title: "Fundamentos de Seguridad - ¿Cómo opera su carga de trabajo?",
          description: "Fundamentos de seguridad y seguridad operacional"
        },
        sec02: {
          title: "Autenticación - ¿Cómo se gestiona la autenticación?",
          description: "Gestión de autenticación e identidad"
        },
        sec03: {
          title: "Permisos - ¿Cómo se gestionan los permisos?",
          description: "Gestión de autorización y permisos"
        },
        sec04: {
          title: "Detección - ¿Cómo se detectan e investigan eventos?",
          description: "Detección e investigación de eventos"
        },
        sec05: {
          title: "Protección de Red - ¿Cómo protege su red?",
          description: "Protección y aislamiento de red"
        },
        sec06: {
          title: "Protección de Recursos - ¿Cómo protege sus recursos?",
          description: "Protección y endurecimiento de recursos"
        },
        sec07: {
          title: "Clasificación de Datos - ¿Cómo clasifica sus datos?",
          description: "Clasificación y organización de datos"
        },
        sec08: {
          title: "Datos en Reposo - ¿Cómo protege sus datos en reposo?",
          description: "Cifrado de datos en reposo"
        },
        sec09: {
          title: "Datos en Tránsito - ¿Cómo protege sus datos en tránsito?",
          description: "Cifrado de datos en tránsito"
        },
        sec10: {
          title: "Respuesta a Incidentes - ¿Cómo anticipa y responde a incidentes?",
          description: "Respuesta a incidentes y recuperación"
        },
        sec11: {
          title: "Seguridad de Aplicaciones - ¿Cómo incorpora seguridad en el ciclo de vida?",
          description: "Seguridad de aplicaciones y ciclo de vida de desarrollo"
        }
      },
      
      // Encabezados de tabla
      table: {
        bpId: "ID BP",
        status: "Estado",
        severity: "Severidad",
        finding: "Hallazgo",
        risk: "Riesgo",
        remediation: "Remediación",
        evidence: "Evidencia"
      },
      
      // Común
      common: {
        noRisk: "Sin riesgo",
        compliantState: "Estado actual cumple",
        notAvailable: "N/D"
      }
    }
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    debug: false,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  })

export default i18n
