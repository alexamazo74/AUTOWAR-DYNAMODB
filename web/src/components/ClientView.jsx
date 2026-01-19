import React, { useState, useEffect } from 'react'

export default function ClientView({ evaluation }) {
  const [selectedReport, setSelectedReport] = useState('executive')
  const [clientData, setClientData] = useState(null)

  useEffect(() => {
    loadClientData()
  }, [])

  const loadClientData = () => {
    // Mock client data - in real implementation this would come from backend
    setClientData({
      company: 'TechCorp S.A.',
      industry: 'Tecnología',
      contact: 'Juan Pérez',
      lastEvaluation: '2024-01-15',
      complianceLevel: 78,
      criticalIssues: 3,
      recommendations: [
        {
          priority: 'high',
          title: 'Implementar MFA obligatorio',
          description: 'Configurar autenticación multifactor para todos los usuarios con acceso administrativo',
          impact: 'Alto',
          effort: 'Medio',
          timeline: '2 semanas'
        },
        {
          priority: 'high',
          title: 'Revisar permisos IAM',
          description: 'Auditar y reducir permisos excesivos en roles y políticas IAM',
          impact: 'Alto',
          effort: 'Alto',
          timeline: '4 semanas'
        },
        {
          priority: 'medium',
          title: 'Habilitar CloudTrail en todas las regiones',
          description: 'Configurar logging centralizado para monitoreo de actividades',
          impact: 'Medio',
          effort: 'Bajo',
          timeline: '1 semana'
        }
      ]
    })
  }

  const reports = [
    {
      id: 'executive',
      title: 'Resumen Ejecutivo',
      icon: '📋',
      description: 'Vista general del estado de cumplimiento WAF'
    },
    {
      id: 'security',
      title: 'Informe de Seguridad',
      icon: '🔒',
      description: 'Análisis detallado del pilar de seguridad'
    },
    {
      id: 'action-plan',
      title: 'Plan de Acción',
      icon: '🎯',
      description: 'Recomendaciones priorizadas para mejora'
    },
    {
      id: 'compliance',
      title: 'Estado de Cumplimiento',
      icon: '✅',
      description: 'Métricas de cumplimiento por componente'
    }
  ]

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#e74c3c'
      case 'medium': return '#f39c12'
      case 'low': return '#27ae60'
      default: return '#95a5a6'
    }
  }

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'high': return '🔴'
      case 'medium': return '🟡'
      case 'low': return '🟢'
      default: return '⚪'
    }
  }

  const renderExecutiveSummary = () => (
    <div className="executive-summary">
      <div className="summary-header">
        <h3>Resumen Ejecutivo - {clientData.company}</h3>
        <p>Evaluación Well-Architected Framework - {clientData.lastEvaluation}</p>
      </div>

      <div className="key-metrics">
        <div className="metric-card">
          <div className="metric-value">{clientData.complianceLevel}%</div>
          <div className="metric-label">Cumplimiento General</div>
          <div className="metric-status">Bueno</div>
        </div>

        <div className="metric-card">
          <div className="metric-value">{clientData.criticalIssues}</div>
          <div className="metric-label">Issues Críticos</div>
          <div className="metric-status">Requiere Atención</div>
        </div>

        <div className="metric-card">
          <div className="metric-value">6</div>
          <div className="metric-label">Pilares Evaluados</div>
          <div className="metric-status">Completo</div>
        </div>
      </div>

      <div className="pillars-overview">
        <h4>Estado por Pilar</h4>
        <div className="pillars-grid">
          {[
            { name: 'Security', score: 75, status: 'Requiere Mejora' },
            { name: 'Reliability', score: 82, status: 'Bueno' },
            { name: 'Performance', score: 68, status: 'Requiere Atención' },
            { name: 'Cost', score: 91, status: 'Excelente' },
            { name: 'Operational', score: 73, status: 'Requiere Mejora' },
            { name: 'Sustainability', score: 85, status: 'Bueno' }
          ].map(pillar => (
            <div key={pillar.name} className="pillar-summary">
              <div className="pillar-name">{pillar.name}</div>
              <div className="pillar-score">{pillar.score}%</div>
              <div className="pillar-status">{pillar.status}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const renderActionPlan = () => (
    <div className="action-plan">
      <div className="plan-header">
        <h3>Plan de Acción Priorizado</h3>
        <p>Recomendaciones para mejorar el cumplimiento WAF</p>
      </div>

      <div className="recommendations-list">
        {clientData.recommendations.map((rec, index) => (
          <div key={index} className="recommendation-card">
            <div className="recommendation-header">
              <div className="priority-indicator">
                <span className="priority-icon">{getPriorityIcon(rec.priority)}</span>
                <span
                  className="priority-label"
                  style={{ color: getPriorityColor(rec.priority) }}
                >
                  {rec.priority.toUpperCase()}
                </span>
              </div>
              <div className="recommendation-meta">
                <span>Impacto: {rec.impact}</span>
                <span>Esfuerzo: {rec.effort}</span>
                <span>Tiempo: {rec.timeline}</span>
              </div>
            </div>

            <div className="recommendation-content">
              <h4>{rec.title}</h4>
              <p>{rec.description}</p>
            </div>

            <div className="recommendation-actions">
              <button className="action-btn primary">Ver Detalles</button>
              <button className="action-btn secondary">Marcar como Completado</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  const renderReportContent = () => {
    switch (selectedReport) {
      case 'executive':
        return renderExecutiveSummary()
      case 'action-plan':
        return renderActionPlan()
      case 'security':
        return (
          <div className="security-report">
            <h3>Informe de Seguridad</h3>
            <p>Contenido detallado del informe de seguridad próximamente...</p>
          </div>
        )
      case 'compliance':
        return (
          <div className="compliance-report">
            <h3>Estado de Cumplimiento</h3>
            <p>Métricas detalladas de cumplimiento próximamente...</p>
          </div>
        )
      default:
        return renderExecutiveSummary()
    }
  }

  if (!clientData) {
    return <div className="loading">Cargando datos del cliente...</div>
  }

  return (
    <div className="client-view">
      <div className="view-header">
        <h2>Vista de Cliente - AutoWAR</h2>
        <p>Reportes y recomendaciones personalizadas para {clientData.company}</p>
      </div>

      <div className="client-info">
        <div className="client-details">
          <h3>{clientData.company}</h3>
          <div className="client-meta">
            <span>Industria: {clientData.industry}</span>
            <span>Contacto: {clientData.contact}</span>
            <span>Última Evaluación: {clientData.lastEvaluation}</span>
          </div>
        </div>
      </div>

      <div className="client-content">
        <div className="reports-menu">
          <h3>Reportes Disponibles</h3>
          <div className="reports-list">
            {reports.map(report => (
              <button
                key={report.id}
                className={`report-item ${selectedReport === report.id ? 'active' : ''}`}
                onClick={() => setSelectedReport(report.id)}
              >
                <span className="report-icon">{report.icon}</span>
                <div className="report-info">
                  <div className="report-title">{report.title}</div>
                  <div className="report-description">{report.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="report-content">
          {renderReportContent()}
        </div>
      </div>
    </div>
  )
}