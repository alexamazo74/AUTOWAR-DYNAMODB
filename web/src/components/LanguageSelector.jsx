import React from 'react'
import { useTranslation } from 'react-i18next'

export default function LanguageSelector() {
  const { i18n } = useTranslation()
  
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng)
  }
  
  return (
    <div className="language-selector">
      <button 
        className={`lang-btn ${i18n.language === 'en' ? 'active' : ''}`}
        onClick={() => changeLanguage('en')}
        title="English"
      >
        🇺🇸 EN
      </button>
      <button 
        className={`lang-btn ${i18n.language === 'es' ? 'active' : ''}`}
        onClick={() => changeLanguage('es')}
        title="Español"
      >
        🇪🇸 ES
      </button>
    </div>
  )
}
