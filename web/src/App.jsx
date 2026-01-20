import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import AnalystView from './components/AnalystView'
import ClientView from './components/ClientView'
import ReportGenerator from './components/ReportGenerator'
import CredentialsForm from './components/CredentialsForm'
import Navigation from './components/Navigation'
import './styles.css'
import './i18n'

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [evaluations, setEvaluations] = useState([])
  const [selectedEvaluation, setSelectedEvaluation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [awsCredentials, setAwsCredentials] = useState(null)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [evaluationMessage, setEvaluationMessage] = useState('')
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  // Track elapsed time during evaluation
  useEffect(() => {
    if (!loading) return
    
    setElapsedSeconds(0)
    const timer = setInterval(() => {
      setElapsedSeconds(prev => prev + 1)
    }, 1000)
    
    return () => clearInterval(timer)
  }, [loading])

  useEffect(() => {
    if (awsCredentials) {
      loadEvaluations()
    }
  }, [awsCredentials])

  const loadEvaluations = async () => {
    if (!awsCredentials) return
    
    setLoading(true)
    setEvaluationComplete(false)
    setEvaluationMessage('🔄 Starting collection and evaluation of security information...')
    try {
      // Check if this is mock data
      let response
      if (awsCredentials.isMockData) {
        // Load mock evaluation
        response = await fetch('http://127.0.0.1:8002/security/evaluate-mock')
      } else {
        // Load real evaluation with credentials
        response = await fetch('http://127.0.0.1:8002/security/evaluate-real', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            access_key_id: awsCredentials.accessKeyId,
            secret_access_key: awsCredentials.secretAccessKey,
            session_token: awsCredentials.sessionToken || null,
            account_id: awsCredentials.accountId,
            regions: awsCredentials.regions
          })
        })
      }
      
      const data = await response.json()
      if (data.success && data.evaluation) {
        // Map questions_evaluated to questions for consistency
        const evaluation = data.evaluation
        if (evaluation.questions_evaluated && !evaluation.questions) {
          evaluation.questions = evaluation.questions_evaluated
        }
        setEvaluations([evaluation])
        setSelectedEvaluation(evaluation)
        setEvaluationMessage('✅ Evaluation complete! Collection, analysis and evaluation finished successfully. You can now navigate all features.')
        setEvaluationComplete(true)
        setTimeout(() => setEvaluationComplete(false), 5000)
      } else {
        console.error('Evaluation error:', data.error)
        setEvaluationMessage('❌ Evaluation error: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error loading evaluations:', error)
      setEvaluations([])
      setEvaluationMessage('❌ Error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const renderView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard evaluations={evaluations} selectedEvaluation={selectedEvaluation} onSelectEvaluation={setSelectedEvaluation} credentials={awsCredentials} loading={loading} />
      case 'analyst':
        return <AnalystView evaluation={selectedEvaluation} credentials={awsCredentials} />
      case 'client':
        return <ClientView evaluation={selectedEvaluation} credentials={awsCredentials} />
      case 'reports':
        return <ReportGenerator evaluation={selectedEvaluation} />
      default:
        return <Dashboard evaluations={evaluations} selectedEvaluation={selectedEvaluation} onSelectEvaluation={setSelectedEvaluation} credentials={awsCredentials} loading={loading} />
    }
  }

  if (!awsCredentials) {
    return (
      <CredentialsForm onConnect={setAwsCredentials} />
    )
  }

  return (
    <div className="app">
      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>{evaluationMessage}</p>
          <div className="loading-details">
            <small>⏱️ Elapsed time: {elapsedSeconds} seconds (max 300 seconds)</small>
            <div style={{marginTop: '15px', width: '200px', height: '4px', background: 'rgba(255,255,255,0.2)', borderRadius: '2px', overflow: 'hidden'}}>
              <div style={{width: `${Math.min((elapsedSeconds / 300) * 100, 100)}%`, height: '100%', background: '#3498db', transition: 'width 0.3s ease'}}></div>
            </div>
          </div>
        </div>
      )}
      {evaluationComplete && (
        <div className="completion-message">
          <div className="completion-content">
            {evaluationMessage}
          </div>
        </div>
      )}
      <Navigation currentView={currentView} onViewChange={setCurrentView} credentials={awsCredentials} onLogout={() => setAwsCredentials(null)} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  )
}
