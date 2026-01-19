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

  useEffect(() => {
    if (awsCredentials) {
      loadEvaluations()
    }
  }, [awsCredentials])

  const loadEvaluations = async () => {
    if (!awsCredentials) return
    
    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8002/security/evaluate-real', {
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
      const data = await response.json()
      if (data.success && data.evaluation) {
        // Map questions_evaluated to questions for consistency
        const evaluation = data.evaluation
        if (evaluation.questions_evaluated && !evaluation.questions) {
          evaluation.questions = evaluation.questions_evaluated
        }
        setEvaluations([evaluation])
        setSelectedEvaluation(evaluation)
      } else {
        console.error('Evaluation error:', data.error)
      }
    } catch (error) {
      console.error('Error loading evaluations:', error)
      setEvaluations([])
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
      {loading && selectedEvaluation === null && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Evaluating all 11 Security questions (63 BPs)...</p>
        </div>
      )}
      <Navigation currentView={currentView} onViewChange={setCurrentView} credentials={awsCredentials} onLogout={() => setAwsCredentials(null)} />
      <main className="main-content">
        {renderView()}
      </main>
    </div>
  )
}
