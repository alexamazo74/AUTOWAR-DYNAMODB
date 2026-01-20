import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import LanguageSelector from './LanguageSelector';
import '../styles.css';

const CredentialsForm = ({ onConnect }) => {
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState({
    accessKeyId: '',
    secretAccessKey: '',
    sessionToken: '',
    accountId: '',
    regions: 'us-east-1'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const validateInputs = () => {
    if (!credentials.accessKeyId.trim()) {
      setError('Access Key ID no puede estar vacío');
      return false;
    }
    if (!credentials.secretAccessKey.trim()) {
      setError('Secret Access Key no puede estar vacío');
      return false;
    }
    if (!credentials.accountId.trim()) {
      setError('Account ID no puede estar vacío');
      return false;
    }
    if (!credentials.regions.trim()) {
      setError('Región(es) no puede(n) estar vacío(s)');
      return false;
    }
    
    // Validar que regionsSea una lista válida de regiones
    const validRegions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'];
    const regionsArray = credentials.regions.split(',').map(r => r.trim());
    for (let region of regionsArray) {
      if (!validRegions.includes(region)) {
        setError(`Región inválida: ${region}. Use formato: us-east-1,eu-west-1`);
        return false;
      }
    }
    
    return true;
  };

  const handleConnect = async () => {
    setError('');
    
    if (!validateInputs()) {
      return;
    }

    setLoading(true);

    try {
      // Enviar credenciales al backend para validar con AWS STS
      const response = await fetch('http://127.0.0.1:8002/security/validate-credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_key_id: credentials.accessKeyId,
          secret_access_key: credentials.secretAccessKey,
          session_token: credentials.sessionToken || null,
          account_id: credentials.accountId,
          regions: credentials.regions.split(',').map(r => r.trim())
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error validando credenciales con AWS');
      }

      const data = await response.json();
      
      if (data.success) {
        // Guardar credenciales en sesión (en el estado de la app)
        onConnect({
          accessKeyId: credentials.accessKeyId,
          secretAccessKey: credentials.secretAccessKey,
          sessionToken: credentials.sessionToken || null,
          accountId: credentials.accountId,
          regions: credentials.regions.split(',').map(r => r.trim()),
          validatedAt: new Date().toISOString()
        });
      } else {
        setError(data.error || 'No se pudo validar las credenciales');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
      console.error('Credentials validation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleConnect();
    }
  };

  const handleLoadMockData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://127.0.0.1:8002/security/evaluate-mock');
      const data = await response.json();
      
      if (data.success && data.evaluation) {
        // Mock credentials object with demo data
        onConnect({
          accessKeyId: 'DEMO-KEY',
          secretAccessKey: 'DEMO-SECRET',
          sessionToken: null,
          accountId: data.evaluation.account_id,
          regions: data.evaluation.regions,
          validatedAt: new Date().toISOString(),
          isMockData: true
        });
      } else {
        setError('Error loading mock data from backend');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
      console.error('Mock data load error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="credentials-form-container">
      <div className="credentials-form">
        <div className="credentials-header">
          <LanguageSelector />
          <h1>{t('credentials.title')}</h1>
          <p>{t('credentials.subtitle')}</p>
        </div>

        <div className="form-group">
          <label htmlFor="accessKeyId">{t('credentials.accessKey')}</label>
          <input
            type="password"
            id="accessKeyId"
            name="accessKeyId"
            value={credentials.accessKeyId}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="AKIAIOSFODNN7EXAMPLE"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="secretAccessKey">{t('credentials.secretKey')}</label>
          <input
            type="password"
            id="secretAccessKey"
            name="secretAccessKey"
            value={credentials.secretAccessKey}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="sessionToken">{t('credentials.sessionToken')}</label>
          <input
            type="password"
            id="sessionToken"
            name="sessionToken"
            value={credentials.sessionToken}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="FwoGZXIvYXdzEHQa..."
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="accountId">{t('credentials.accountId')}</label>
          <input
            type="text"
            id="accountId"
            name="accountId"
            value={credentials.accountId}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="123456789012"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="regions">{t('credentials.region')}</label>
          <input
            type="text"
            id="regions"
            name="regions"
            value={credentials.regions}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="us-east-1,eu-west-1"
            disabled={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            <span>⚠️ {error}</span>
          </div>
        )}

        <button
          className="connect-button"
          onClick={handleConnect}
          disabled={loading}
        >
          {loading ? `🔄 ${t('credentials.connecting')}` : `🔐 ${t('credentials.connect')}`}
        </button>

        <button
          className="connect-button"
          style={{ backgroundColor: '#3498db', marginTop: '10px' }}
          onClick={handleLoadMockData}
          disabled={loading}
        >
          {loading ? '⏳ Loading...' : '📊 Load Demo Data'}
        </button>

        <div className="security-note">
          <p><small>💡 {t('credentials.demoNote')}</small></p>
          <p><small>Or click <strong>Load Demo Data</strong> to test the UI with mock evaluation results</small></p>
        </div>
      </div>
    </div>
  );
};

export default CredentialsForm;
