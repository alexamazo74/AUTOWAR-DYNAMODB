import React, { useState } from 'react'

export default function ReportGenerator() {
  const [reportType, setReportType] = useState('executive')
  const [format, setFormat] = useState('pdf')
  const [loading, setLoading] = useState(false)

  const reportTypes = [
    { id: 'executive', name: 'Resumen Ejecutivo', icon: '📋' },
    { id: 'technical', name: 'Reporte Técnico Completo', icon: '🔧' },
    { id: 'security', name: 'Informe de Seguridad', icon: '🔒' },
    { id: 'compliance', name: 'Reporte de Cumplimiento', icon: '✅' },
    { id: 'remediation', name: 'Plan de Remediación', icon: '🛠️' }
  ]

  const formats = [
    { id: 'pdf', name: 'PDF', icon: '📄' },
    { id: 'excel', name: 'Excel', icon: '📊' },
    { id: 'json', name: 'JSON', icon: '📝' }
  ]

  const handleGenerateReport = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:8002/reports/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          evaluation_id: 'test-security-eval-1',
          report_type: reportType,
          format: format
        })
      })

      if (response.ok) {
        // Download the file
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `autowar-${reportType}-${Date.now()}.${format === 'excel' ? 'xlsx' : format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        alert('✅ Reporte generado y descargado exitosamente')
      } else {
        // If endpoint not implemented, show mock data
        const mockData = generateMockReport()
        downloadMockReport(mockData)
      }
    } catch (error) {
      console.error('Error generating report:', error)
      // Generate mock report as fallback
      const mockData = generateMockReport()
      downloadMockReport(mockData)
    } finally {
      setLoading(false)
    }
  }

  const generateMockReport = () => {
    return {
      title: `AutoWAR - ${reportTypes.find(r => r.id === reportType)?.name}`,
      date: new Date().toISOString(),
      evaluation_id: 'test-security-eval-1',
      company: 'TechCorp S.A.',
      summary: {
        overall_score: 78,
        pillars: [
          { name: 'Security', score: 75, status: 'Bueno' },
          { name: 'Reliability', score: 82, status: 'Excelente' },
          { name: 'Performance', score: 68, status: 'Requiere Mejora' },
          { name: 'Cost Optimization', score: 91, status: 'Excelente' },
          { name: 'Operational Excellence', score: 73, status: 'Bueno' },
          { name: 'Sustainability', score: 85, status: 'Excelente' }
        ],
        critical_issues: 3,
        recommendations: 5
      },
      details: reportType === 'executive' 
        ? 'Resumen ejecutivo de alto nivel con métricas clave y recomendaciones prioritarias.'
        : 'Reporte técnico detallado con análisis por pregunta, BP, evidencia y remediación completa.'
    }
  }

  const downloadMockReport = (data) => {
    const content = format === 'json' 
      ? JSON.stringify(data, null, 2)
      : generateTextReport(data)
    
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `autowar-${reportType}-${Date.now()}.${format === 'json' ? 'json' : 'txt'}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    alert('✅ Reporte mock generado y descargado (PDF/Excel pendiente de implementación)')
  }

  const generateTextReport = (data) => {
    return `
===========================================
${data.title}
===========================================
Fecha: ${new Date(data.date).toLocaleString()}
Evaluación ID: ${data.evaluation_id}
Cliente: ${data.company}

RESUMEN GENERAL
===============
Score Global: ${data.summary.overall_score}%
Issues Críticos: ${data.summary.critical_issues}
Recomendaciones: ${data.summary.recommendations}

SCORES POR PILAR
================
${data.summary.pillars.map(p => `${p.name}: ${p.score}% - ${p.status}`).join('\n')}

DETALLES
========
${data.details}

-------------------------------------------
Generado por AutoWAR - AWS Well-Architected Review
    `.trim()
  }

  return (
    <div className="report-generator">
      <div className="generator-header">
        <h3>📥 Generar y Descargar Reportes</h3>
        <p>Genera reportes personalizados en diferentes formatos</p>
      </div>

      <div className="generator-content">
        <div className="form-section">
          <label>Tipo de Reporte</label>
          <div className="report-types">
            {reportTypes.map(type => (
              <button
                key={type.id}
                className={`report-type-btn ${reportType === type.id ? 'active' : ''}`}
                onClick={() => setReportType(type.id)}
              >
                <span className="type-icon">{type.icon}</span>
                <span className="type-name">{type.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="form-section">
          <label>Formato de Salida</label>
          <div className="format-options">
            {formats.map(fmt => (
              <button
                key={fmt.id}
                className={`format-btn ${format === fmt.id ? 'active' : ''}`}
                onClick={() => setFormat(fmt.id)}
              >
                <span className="format-icon">{fmt.icon}</span>
                <span className="format-name">{fmt.name}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="generator-actions">
          <button
            className="generate-btn"
            onClick={handleGenerateReport}
            disabled={loading}
          >
            {loading ? '⏳ Generando...' : '📥 Generar y Descargar Reporte'}
          </button>
        </div>

        <div className="implementation-note">
          <strong>📝 Nota:</strong> Los reportes PDF y Excel están en desarrollo.
          Actualmente se generan reportes en formato JSON y TXT como demostración.
          La generación de PDF/Excel con gráficos y formato completo se implementará
          usando bibliotecas como ReportLab (Python) o jsPDF (JavaScript).
        </div>
      </div>

      <style jsx>{`
        .report-generator {
          background: white;
          border-radius: 8px;
          padding: 30px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .generator-header {
          margin-bottom: 30px;
        }

        .generator-header h3 {
          color: #2c3e50;
          margin-bottom: 8px;
        }

        .generator-header p {
          color: #7f8c8d;
        }

        .form-section {
          margin-bottom: 25px;
        }

        .form-section label {
          display: block;
          font-weight: 600;
          color: #2c3e50;
          margin-bottom: 12px;
        }

        .report-types, .format-options {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 12px;
        }

        .report-type-btn, .format-btn {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 15px;
          background: #f8f9fa;
          border: 2px solid #e1e8ed;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .report-type-btn:hover, .format-btn:hover {
          border-color: #3498db;
          box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
        }

        .report-type-btn.active, .format-btn.active {
          border-color: #3498db;
          background: #e8f4fd;
        }

        .type-icon, .format-icon {
          font-size: 1.5rem;
        }

        .type-name, .format-name {
          font-weight: 500;
          color: #2c3e50;
        }

        .generator-actions {
          margin-top: 30px;
          text-align: center;
        }

        .generate-btn {
          background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
          color: white;
          border: none;
          padding: 15px 40px;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .generate-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
        }

        .generate-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .implementation-note {
          margin-top: 25px;
          padding: 15px;
          background: #fff3cd;
          border-left: 4px solid #f39c12;
          border-radius: 4px;
          font-size: 0.9rem;
          color: #856404;
        }

        .implementation-note strong {
          display: block;
          margin-bottom: 5px;
        }
      `}</style>
    </div>
  )
}
