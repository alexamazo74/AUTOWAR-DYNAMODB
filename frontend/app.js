document.getElementById('evaluateSecurity').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const body = {
    evaluation_id: document.getElementById('securityEvalId').value,
    question_id: document.getElementById('questionId').value
  };
  try {
    const res = await fetch(base + '/security/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('getSecurityEvaluation').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('getSecurityEvalId').value;
  const questionId = document.getElementById('getSecurityQuestionId').value;
  try {
    const res = await fetch(base + '/security/evaluations/' + encodeURIComponent(evalId) + '/' + encodeURIComponent(questionId));
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('listSecurityEvaluations').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('listSecurityEvalId').value;
  try {
    const res = await fetch(base + '/security/evaluations?evaluation_id=' + encodeURIComponent(evalId));
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('generateReport').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('reportEvalId').value;
  try {
    const res = await fetch(base + '/security/reports/' + encodeURIComponent(evalId));
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e.message + '\n\nPosibles causas:\n- El servidor backend no está ejecutándose\n- Problema de conexión CORS\n- URL incorrecta del backend';
  }
});

document.getElementById('postScore').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const body = {
    evaluation_id: document.getElementById('evaluationId').value,
    bp_id: document.getElementById('bpId').value,
    scores: JSON.parse(document.getElementById('scores').value || '{}')
  };
  try {
    const res = await fetch(base + '/scores', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('listScores').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('listEvalId').value;
  try {
    const res = await fetch(base + '/evaluations/' + encodeURIComponent(evalId) + '/scores');
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e;
  }
});

document.getElementById('testConnection').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const statusIndicator = document.getElementById('backendStatus');
  const statusText = document.getElementById('statusText');
  
  statusIndicator.className = 'status-indicator';
  statusText.textContent = 'Verificando...';
  
  try {
    const res = await fetch(base + '/health');
    if (res.ok) {
      statusIndicator.classList.add('status-online');
      statusText.textContent = 'Conectado ✓';
    } else {
      statusIndicator.classList.add('status-offline');
      statusText.textContent = 'Error de conexión';
    }
  } catch (e) {
    statusIndicator.classList.add('status-offline');
    statusText.textContent = 'No conectado ✗';
  }
});

// Auto-test connection on page load
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('testConnection').click();
});

document.getElementById('getRisks').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('riskEvalId').value;
  const questionId = document.getElementById('riskQuestionId').value;
  try {
    const res = await fetch(base + '/security/risks/' + encodeURIComponent(evalId) + '/' + encodeURIComponent(questionId));
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e.message + '\n\nPosibles causas:\n- El servidor backend no está ejecutándose\n- Problema de conexión CORS\n- URL incorrecta del backend';
  }
});

document.getElementById('getRemediation').addEventListener('click', async () => {
  const base = document.getElementById('baseUrl').value.replace(/\/$/, '');
  const evalId = document.getElementById('remediationEvalId').value;
  const questionId = document.getElementById('remediationQuestionId').value;
  try {
    const res = await fetch(base + '/security/remediation/' + encodeURIComponent(evalId) + '/' + encodeURIComponent(questionId));
    const json = await res.json();
    document.getElementById('result').textContent = res.status + '\n' + JSON.stringify(json, null, 2);
  } catch (e) {
    document.getElementById('result').textContent = 'Error: ' + e.message + '\n\nPosibles causas:\n- El servidor backend no está ejecutándose\n- Problema de conexión CORS\n- URL incorrecta del backend';
  }
});
