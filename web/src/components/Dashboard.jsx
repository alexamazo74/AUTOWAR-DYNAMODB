import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'

export default function Dashboard({ evaluations, selectedEvaluation, onSelectEvaluation, credentials, loading }) {
  const { t } = useTranslation()
  const [pillarsData, setPillarsData] = useState([])
  const [selectedPillar, setSelectedPillar] = useState(null)

  useEffect(() => {
    calculatePillarsData()
  }, [evaluations, selectedEvaluation])

  const calculatePillarsData = () => {
    // Use real evaluation data if available
    if (selectedEvaluation && selectedEvaluation.overall_score !== undefined) {
      const evaluation = selectedEvaluation
      
      // Contar findings por severidad
      let criticalCount = 0
      let highCount = 0
      let mediumCount = 0
      let lowCount = 0
      let totalFindings = 0
      
      if (evaluation.questions && Array.isArray(evaluation.questions)) {
        evaluation.questions.forEach(question => {
          if (question.findings && Array.isArray(question.findings)) {
            question.findings.forEach(finding => {
              totalFindings++
              switch(finding.severity) {
                case 'CRITICAL': criticalCount++; break
                case 'HIGH': highCount++; break
                case 'MEDIUM': mediumCount++; break
                case 'LOW': lowCount++; break
              }
            })
          }
        })
      }
      
      const securityPillar = {
        id: 'security',
        name: 'Security Pillar',
        score: Math.round(evaluation.overall_score),
        questions: evaluation.questions?.length || 11,
        color: '#e74c3c',
        icon: '🔒',
        trend: 'Real-time',
        criticalIssues: criticalCount,
        findings: {
          CRITICAL: criticalCount,
          HIGH: highCount,
          MEDIUM: mediumCount,
          LOW: lowCount,
          total: totalFindings
        },
        lastUpdated: evaluation.timestamp || new Date().toISOString(),
        account: evaluation.account_id,
        regions: evaluation.regions || [],
        bps_total: evaluation.total_best_practices || 63,
        evaluation: evaluation
      }
      
      // Mostrar solo el pilar de Security con datos reales
      const mockPillars = [
        securityPillar,
        {
          id: 'reliability',
          name: 'Reliability',
          score: 82,
          questions: 4,
          color: '#f39c12',
          icon: '⚡',
          trend: '+2%',
          criticalIssues: 0,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'performance',
          name: 'Performance',
          score: 68,
          questions: 3,
          color: '#9b59b6',
          icon: '🚀',
          trend: '-3%',
          criticalIssues: 1,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'cost',
          name: 'Cost Optimization',
          score: 91,
          questions: 4,
          color: '#27ae60',
          icon: '💰',
          trend: '+8%',
          criticalIssues: 0,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'operational',
          name: 'Operational Excellence',
          score: 73,
          questions: 5,
          color: '#3498db',
          icon: '⚙️',
          trend: '+1%',
          criticalIssues: 3,
          findings: {},
          note: '(Coming soon)'
        }
      ]
      
      setPillarsData(mockPillars)
      // Auto-select Security pillar
      setSelectedPillar(securityPillar)
    } else {
      // Use mock data
      const mockPillars = [
        {
          id: 'security',
          name: 'Security Pillar',
          score: 75,
          questions: 11,
          color: '#e74c3c',
          icon: '🔒',
          trend: '+5%',
          criticalIssues: 2,
          findings: { CRITICAL: 2, HIGH: 3, MEDIUM: 5, LOW: 2, total: 12 },
          bps_total: 63
        },
        {
          id: 'reliability',
          name: 'Reliability',
          score: 82,
          questions: 4,
          color: '#f39c12',
          icon: '⚡',
          trend: '+2%',
          criticalIssues: 0,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'performance',
          name: 'Performance',
          score: 68,
          questions: 3,
          color: '#9b59b6',
          icon: '🚀',
          trend: '-3%',
          criticalIssues: 1,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'cost',
          name: 'Cost Optimization',
          score: 91,
          questions: 4,
          color: '#27ae60',
          icon: '💰',
          trend: '+8%',
          criticalIssues: 0,
          findings: {},
          note: '(Coming soon)'
        },
        {
          id: 'operational',
          name: 'Operational Excellence',
          score: 73,
          questions: 5,
          color: '#3498db',
          icon: '⚙️',
          trend: '+1%',
          criticalIssues: 3,
          findings: {},
          note: '(Coming soon)'
        }
      ]
      
      setPillarsData(mockPillars)
      setSelectedPillar(mockPillars[0])
    }
  }

  const getScoreColor = (score) => {
    if (score >= 90) return '#27ae60'
    if (score >= 75) return '#f39c12'
    if (score >= 60) return '#e67e22'
    return '#e74c3c'
  }

  const getScoreLabel = (score) => {
    if (score >= 90) return 'Excelente'
    if (score >= 75) return 'Bueno'
    if (score >= 60) return 'Regular'
    return 'Crítico'
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>{t('dashboard.title')}</h2>
        <p>{t('dashboard.subtitle')}</p>
        {selectedEvaluation && (
          <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '10px' }}>
            {t('credentials.accountId')}: {selectedEvaluation.account_id} | {t('credentials.region')}: {selectedEvaluation.regions.join(', ')} | {new Date(selectedEvaluation.timestamp).toLocaleString()}
          </div>
        )}
      </div>

      {loading && (
        <div className="loading" style={{ marginBottom: '20px' }}>
          <span>⏳ {t('dashboard.loading')}</span>
        </div>
      )}

      <div className="pillars-grid">
        {pillarsData.map(pillar => (
          <div
            key={pillar.id}
            className="pillar-card"
            onClick={() => setSelectedPillar(pillar)}
          >
            <div className="pillar-header">
              <div className="pillar-icon">{pillar.icon}</div>
              <div className="pillar-info">
                <h3>{pillar.name}</h3>
                <div className="pillar-score">
                  <span
                    className="score-value"
                    style={{ color: getScoreColor(pillar.score) }}
                  >
                    {pillar.score}%
                  </span>
                  <span className="score-label">{getScoreLabel(pillar.score)}</span>
                </div>
              </div>
            </div>

            <div className="pillar-details">
              <div className="detail-item">
                <span>Preguntas:</span>
                <span>{pillar.questions}</span>
              </div>
              <div className="detail-item">
                <span>Tendencia:</span>
                <span className={pillar.trend.startsWith('+') ? 'positive' : 'negative'}>
                  {pillar.trend}
                </span>
              </div>
              <div className="detail-item">
                <span>Issues Críticos:</span>
                <span className={pillar.criticalIssues > 0 ? 'critical' : 'good'}>
                  {pillar.criticalIssues}
                </span>
              </div>
            </div>

            <div className="pillar-progress">
              <div
                className="progress-bar"
                style={{
                  width: `${pillar.score}%`,
                  backgroundColor: getScoreColor(pillar.score)
                }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {selectedPillar && (
        <div className="pillar-detail-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>{selectedPillar.icon} {selectedPillar.name} - Detalle</h3>
              <button
                className="close-button"
                onClick={() => setSelectedPillar(null)}
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <div className="pillar-summary">
                <div className="summary-item">
                  <span>Score General:</span>
                  <span className="score-large">{selectedPillar.score}%</span>
                </div>
                <div className="summary-item">
                  <span>Preguntas Evaluadas:</span>
                  <span>{selectedPillar.questions}/11</span>
                </div>
                <div className="summary-item">
                  <span>Best Practices:</span>
                  <span>{selectedPillar.bps_total}/63</span>
                </div>
                <div className="summary-item">
                  <span>Total Findings:</span>
                  <span>{selectedPillar.findings?.total || 0}</span>
                </div>
              </div>

              {selectedPillar.findings && (
                <div className="findings-summary">
                  <h4>📊 Findings by Severity</h4>
                  <div className="severity-grid">
                    <div className="severity-item critical">
                      <span className="label">CRITICAL</span>
                      <span className="count">{selectedPillar.findings.CRITICAL || 0}</span>
                    </div>
                    <div className="severity-item high">
                      <span className="label">HIGH</span>
                      <span className="count">{selectedPillar.findings.HIGH || 0}</span>
                    </div>
                    <div className="severity-item medium">
                      <span className="label">MEDIUM</span>
                      <span className="count">{selectedPillar.findings.MEDIUM || 0}</span>
                    </div>
                    <div className="severity-item low">
                      <span className="label">LOW</span>
                      <span className="count">{selectedPillar.findings.LOW || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              {selectedPillar.evaluation && selectedPillar.evaluation.questions && (
                <div className="questions-breakdown">
                  <h4>📋 Questions Breakdown (11 Security Questions × 63 BPs)</h4>
                  <div className="questions-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Question</th>
                          <th>Score</th>
                          <th>BPs</th>
                          <th>Findings</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedPillar.evaluation.questions.map((q, idx) => (
                          <tr key={idx}>
                            <td><strong>{q.question_id}</strong></td>
                            <td>{q.score}%</td>
                            <td>{q.bps_evaluated}</td>
                            <td>{q.findings?.length || 0}</td>
                            <td>
                              <span className={`status ${q.score > 75 ? 'good' : 'attention'}`}>
                                {q.score > 75 ? '✓' : '⚠'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {selectedPillar.account && (
                <div className="account-info">
                  <h4>📍 Evaluation Details</h4>
                  <div className="info-grid">
                    <div><span>Account:</span> {selectedPillar.account}</div>
                    <div><span>Regions:</span> {selectedPillar.regions?.join(', ') || 'N/A'}</div>
                    <div><span>Updated:</span> {new Date(selectedPillar.lastUpdated).toLocaleString()}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}