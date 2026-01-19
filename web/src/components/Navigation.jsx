import React from 'react'
import { useTranslation } from 'react-i18next'
import LanguageSelector from './LanguageSelector'

export default function Navigation({ currentView, onViewChange, onLogout }) {
  const { t } = useTranslation()
  
  const navItems = [
    { id: 'dashboard', label: t('nav.dashboard'), icon: '📊' },
    { id: 'analyst', label: t('nav.analyst'), icon: '🔍' },
    { id: 'client', label: t('nav.client'), icon: '👤' },
    { id: 'reports', label: t('nav.reports'), icon: '📥' }
  ]

  return (
    <nav className="navigation">
      <div className="nav-header">
        <h1>🔒 AutoWAR</h1>
        <p>Well-Architected Framework</p>
        <LanguageSelector />
      </div>

      <div className="nav-menu">
        {navItems.map(item => (
          <button
            key={item.id}
            className={`nav-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => onViewChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </div>

      <div className="nav-footer">
        {onLogout && (
          <button className="logout-btn" onClick={onLogout}>
            🚪 {t('nav.logout')}
          </button>
        )}
        <div className="status-indicator">
          <span className="status-dot online"></span>
          <span>Sistema Online</span>
        </div>
      </div>
    </nav>
  )
}