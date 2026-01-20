import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { translateFindings } from '../utils/translateBP'

export default function AnalystView({ evaluation }) {
  const { t, i18n } = useTranslation()
  const [selectedQuestion, setSelectedQuestion] = useState(null)
  const [allQuestionsData, setAllQuestionsData] = useState([])
  const [loading, setLoading] = useState(false)
  const [retryingBPs, setRetryingBPs] = useState(new Set())

  // Las 11 preguntas completas de Security pillar (según documento oficial)
  const questions = [
    {
      id: 'SEC01',
      title: t('questions.sec01.title'),
      description: t('questions.sec01.description'),
      bps: 8,  // SEC01-BP01 a SEC01-BP08
      color: '#e74c3c'
    },
    {
      id: 'SEC02',
      title: t('questions.sec02.title'),
      description: t('questions.sec02.description'),
      bps: 6,  // SEC02-BP01 a SEC02-BP06
      color: '#e67e22'
    },
    {
      id: 'SEC03',
      title: t('questions.sec03.title'),
      description: t('questions.sec03.description'),
      bps: 9,  // SEC03-BP01 a SEC03-BP09
      color: '#f39c12'
    },
    {
      id: 'SEC04',
      title: t('questions.sec04.title'),
      description: t('questions.sec04.description'),
      bps: 4,  // SEC04-BP01 a SEC04-BP04
      color: '#27ae60'
    },
    {
      id: 'SEC05',
      title: t('questions.sec05.title'),
      description: t('questions.sec05.description'),
      bps: 4,  // SEC05-BP01 a SEC05-BP04
      color: '#2ecc71'
    },
    {
      id: 'SEC06',
      title: t('questions.sec06.title'),
      description: t('questions.sec06.description'),
      bps: 5,  // SEC06-BP01 a SEC06-BP05
      color: '#16a085'
    },
    {
      id: 'SEC07',
      title: t('questions.sec07.title'),
      description: t('questions.sec07.description'),
      bps: 4,  // SEC07-BP01 a SEC07-BP04
      color: '#3498db'
    },
    {
      id: 'SEC08',
      title: t('questions.sec08.title'),
      description: t('questions.sec08.description'),
      bps: 4,  // SEC08-BP01 a SEC08-BP04
      color: '#2980b9'
    },
    {
      id: 'SEC09',
      title: t('questions.sec09.title'),
      description: t('questions.sec09.description'),
      bps: 3,  // SEC09-BP01 a SEC09-BP03
      color: '#8e44ad'
    },
    {
      id: 'SEC10',
      title: t('questions.sec10.title'),
      description: t('questions.sec10.description'),
      bps: 8,  // SEC10-BP01 a SEC10-BP08
      color: '#9b59b6'
    },
    {
      id: 'SEC11',
      title: t('questions.sec11.title'),
      description: t('questions.sec11.description'),
      bps: 8,  // SEC11-BP01 a SEC11-BP08
      color: '#7f8c8d'
    }
  ]

  useEffect(() => {
    if (evaluation && evaluation.questions) {
      // Mapear datos reales del backend y traducir campos dinámicos
      const language = i18n.language || 'en'
      const translatedQuestions = evaluation.questions.map(q => ({
        ...q,
        findings: translateFindings(q.findings || [], language)
      }))
      setAllQuestionsData(translatedQuestions)
      if (!selectedQuestion && translatedQuestions.length > 0) {
        setSelectedQuestion(translatedQuestions[0])
      }
    }
  }, [evaluation, i18n.language])

  const handleQuestionSelect = (questionData) => {
    setSelectedQuestion(questionData)
  }

  const getEvidenceIcon = (evidence) => {
    if (!evidence) return '❓'
    if (evidence.includes('No ') && evidence.includes('found')) return '📦'
    if (evidence.includes('timeout') || evidence.includes('Timeout')) return '⏱️'
    if (evidence === 'N/D') return '❓'
    return '✓'
  }

  const getPendingBPs = () => {
    if (!selectedQuestion?.findings) return []
    return selectedQuestion.findings.filter(f => f.status === 'PENDING_REVIEW' || f.status === 'pending')
  }

  const handleRetryBPs = async () => {
    const pendingBPs = getPendingBPs()
    if (pendingBPs.length === 0) return

    const bpIds = pendingBPs.map(f => f.bp)
    setRetryingBPs(new Set(bpIds))
    
    try {
      const response = await fetch('http://127.0.0.1:8002/security/re-evaluate-bp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_key_id: evaluation.credentials?.accessKeyId,
          secret_access_key: evaluation.credentials?.secretAccessKey,
          session_token: evaluation.credentials?.sessionToken || null,
          account_id: evaluation.account_id,
          regions: evaluation.regions || [],
          bp_ids: bpIds
        })
      })

      const data = await response.json()
      if (data.success && data.evaluated) {
        // Update findings with new results
        const updatedFindings = selectedQuestion.findings.map(finding => {
          const updated = data.evaluated.find(e => e.bp === finding.bp)
          return updated ? { ...finding, ...updated } : finding
        })
        setSelectedQuestion({ ...selectedQuestion, findings: updatedFindings })
      }
    } catch (error) {
      console.error('Error retrying BPs:', error)
    } finally {
      setRetryingBPs(new Set())
    }
  }

  const getComplianceColor = (score) => {
    if (score >= 90) return '#27ae60'
    if (score >= 75) return '#f39c12'
    if (score >= 60) return '#e67e22'
    return '#e74c3c'
  }

  const getComplianceLabel = (score) => {
    if (score >= 90) return 'CUMPLE'
    if (score >= 75) return 'PARCIAL'
    if (score >= 60) return 'MEJORA'
    return 'NO CUMPLE'
  }

  return (
    <div className="analyst-view">
      <div className="view-header">
        <h2>{t('analyst.title')}</h2>
        <p>{t('analyst.subtitle')}</p>
      </div>

      <div className="analyst-content">
        <div className="questions-panel">
          <h3>{t('analyst.securityQuestions')}</h3>
          <div className="summary-info">
            <div>✅ {t('analyst.total')}: 11 {t('dashboard.questions')}</div>
            <div>✓ {t('analyst.total')}: 63 {t('dashboard.bps')}</div>
          </div>
          <div className="questions-list">
            {questions.map(question => {
              const realData = allQuestionsData.find(q => q.question_id === question.id)
              const score = realData?.score || 0
              return (
                <div
                  key={question.id}
                  className={`question-item ${selectedQuestion?.question_id === question.id ? 'selected' : ''}`}
                  onClick={() => handleQuestionSelect({ ...question, ...realData })}
                  style={{ borderLeftColor: question.color }}
                >
                  <div className="question-header">
                    <h4>{question.id}</h4>
                    <div className="question-score">
                      <span className="score" style={{ color: question.color }}>
                        {score}%
                      </span>
                    </div>
                  </div>
                  <p title={question.title}>{question.title}</p>
                  <div className="question-meta">
                    <span>{question.bps} {t('dashboard.bps')}</span>
                    <span>{realData?.findings?.length || 0} {t('analyst.findings')}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="detail-panel">
          {selectedQuestion ? (
            <>
              <div className="question-detail">
                <h3>{selectedQuestion.question_id}: {selectedQuestion.title || selectedQuestion.description}</h3>
                <div className="question-meta-full">
                  <span>{t('dashboard.score')}: <strong>{selectedQuestion.score || 0}%</strong></span>
                  <span>{t('analyst.bpsLabel')} {t('dashboard.evaluated')}: <strong>{selectedQuestion.bps_evaluated || 'N/A'}</strong></span>
                  <span>{t('analyst.statusLabel')}: <strong>{selectedQuestion.status || 'EVALUATED'}</strong></span>
                </div>

                <div className="findings-section">
                  <h4>📊 {t('analyst.findingsLabel')} ({selectedQuestion.findings?.length || 0})</h4>
                  {getPendingBPs().length > 0 && (
                    <div className="retry-section">
                      <div className="retry-info">
                        <span>⚠️ {getPendingBPs().length} BP(s) with N/D status</span>
                        <button 
                          className="retry-button" 
                          onClick={handleRetryBPs}
                          disabled={retryingBPs.size > 0}
                        >
                          {retryingBPs.size > 0 ? '🔄 Retrying...' : '🔄 Retry N/D BPs'}
                        </button>
                      </div>
                      <div className="nd-legend">
                        <span title="No resources implemented">📦 = No resources found</span>
                        <span title="Timeout during evaluation">⏱️ = Evaluation timeout</span>
                        <span title="Generic N/D">❓ = Unable to determine</span>
                      </div>
                    </div>
                  )}
                  {selectedQuestion.findings && selectedQuestion.findings.length > 0 ? (
                    <>
                      <div className="findings-table-container">
                        <table className="findings-table">
                          <thead>
                            <tr>
                              <th>{t('table.bpId')}</th>
                              <th>{t('table.status')}</th>
                              <th>{t('table.severity')}</th>
                              <th>{t('table.finding')}</th>
                              <th>{t('table.risk')}</th>
                              <th>{t('table.remediation')}</th>
                              <th>{t('table.evidence')}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedQuestion.findings.map((finding, idx) => (
                              <tr key={idx}>
                                <td className="bp-id"><strong>{finding.bp}</strong></td>
                                <td><div className={`finding-status ${finding.status}`}>{t(`status.${finding.status.toLowerCase()}`)}</div></td>
                                <td><div className={`severity-badge ${finding.severity || 'MEDIUM'}`}>{t(`severity.${(finding.severity || 'MEDIUM').toLowerCase()}`)}</div></td>
                                <td className="finding-text">{finding.finding}</td>
                                <td className="risk-text">{finding.risk || t('common.notAvailable')}</td>
                                <td className="remediation-text">{finding.remediation || t('common.notAvailable')}</td>
                                <td className="evidence-text">
                                  <small title={finding.evidence}>
                                    <span className="evidence-icon">{getEvidenceIcon(finding.evidence)}</span>
                                    {finding.evidence || t('common.notAvailable')}
                                  </small>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="findings-grid">
                        {selectedQuestion.findings.map((finding, idx) => (
                          <div key={idx} className={`finding-card ${retryingBPs.has(finding.bp) ? 'retrying' : ''}`}>
                            <div className="finding-header">
                              <h5>{finding.bp}</h5>
                              <div className={`severity-badge ${finding.severity || 'MEDIUM'}`}>
                                {t(`severity.${(finding.severity || 'MEDIUM').toLowerCase()}`)}
                              </div>
                            </div>
                            <div className={`finding-status ${finding.status}`}>
                              {t(`status.${finding.status.toLowerCase()}`)}
                            </div>
                            <p>{finding.finding}</p>
                            {finding.evidence && (
                              <div className="finding-evidence">
                                <small>
                                  <strong>{t('analyst.evidence')}:</strong> 
                                  <span className="evidence-icon">{getEvidenceIcon(finding.evidence)}</span>
                                  {finding.evidence}
                                </small>
                              </div>
                            )}
                            {finding.risk && (
                              <div className="finding-risk">
                                <small><strong>🚨 {t('analyst.risk')}:</strong> {finding.risk}</small>
                              </div>
                            )}
                            {finding.remediation && (
                              <div className="finding-remediation">
                                <small><strong>✅ {t('analyst.remediation')}:</strong> {finding.remediation}</small>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <p>✓ {t('analyst.noFindings')}</p>
                  )}
                </div>
              </div>
              <div className="summary-section">
                <div className="summary-card">
                  <h4>📈 {t('analyst.questionSummary')}</h4>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span>{t('dashboard.score')}</span>
                      <strong>{selectedQuestion.score || 0}%</strong>
                    </div>
                    <div className="summary-item">
                      <span>{t('analyst.bpsLabel')}</span>
                      <strong>{selectedQuestion.bps_evaluated || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>{t('analyst.findingsLabel')}</span>
                      <strong>{selectedQuestion.findings?.length || 0}</strong>
                    </div>
                    <div className="summary-item">
                      <span>{t('analyst.statusLabel')}</span>
                      <strong>{selectedQuestion.score > 75 ? `✓ ${t('analyst.good')}` : `⚠ ${t('analyst.improve')}`}</strong>
                    </div>
                  </div>
                </div>
              </div>

            </>
          ) : (
            <div className="no-selection">
              <h3>{t('analyst.selectQuestion')}</h3>
              <p>{t('analyst.selectHelp')}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}