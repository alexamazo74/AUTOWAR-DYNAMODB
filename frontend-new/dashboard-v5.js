// AutoWAR Dashboard

const API_BASE_URL = 'https://gp3ep01awc.execute-api.us-east-1.amazonaws.com/prod';

const sessionId = sessionStorage.getItem('autowar_session_id');
if (!sessionId) {
    window.location.href = 'index.html';
}

window.addEventListener('load', async () => {
    // Check if we have cached results from a previous evaluation
    const cachedPillars = sessionStorage.getItem('dashboard_pillars');
    if (cachedPillars) {
        try {
            const pillars = JSON.parse(cachedPillars);
            if (pillars && pillars.length > 0) {
                displayResults(pillars);
                return;
            }
        } catch (e) {
            console.error('Error parsing cached pillars:', e);
        }
    }
    
    // No cached data, run new evaluation
    await startEvaluation();
});

async function startEvaluation() {
    const loadingText = document.querySelector('.loading-subtext');
    
    try {
        if (!sessionId) {
            throw new Error('No hay sesion activa. Por favor, valida tus credenciales AWS nuevamente.');
        }
        
        loadingText.textContent = 'Iniciando evaluacion asincrona...';
        
        const response = await fetch(`${API_BASE_URL}/evaluate/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Session-ID': sessionId },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to start evaluation';
            try { const error = await response.json(); errorMessage = error.error || errorMessage; } catch (e) {}
            throw new Error(errorMessage);
        }
        
        const { evaluation_id } = await response.json();
        if (!evaluation_id) throw new Error('No se recibio evaluation_id del servidor');
        
        // Store evaluation_id for reference
        sessionStorage.setItem('current_evaluation_id', evaluation_id);
        
        loadingText.textContent = 'Evaluando pilares en paralelo...';
        const results = await pollEvaluationStatus(evaluation_id, loadingText);
        
        loadingText.textContent = 'Guardando evaluacion...';
        await storeEvaluation(results);
        
        displayResults(results);
        
    } catch (error) {
        console.error('Evaluation error:', error);
        let userMessage = error.message;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            userMessage = 'Error de conexion. Verifica tu conexion a internet.';
        }
        const loadingText = document.querySelector('.loading-subtext');
        loadingText.innerHTML = `
            <div style="color: #ef4444; font-weight: bold;">Error: ${userMessage}</div>
            <div style="margin-top: 10px; font-size: 12px;">
                <a href="index.html" style="color: #3b82f6; text-decoration: underline;">Volver al inicio</a>
            </div>
        `;
    }
}

async function pollEvaluationStatus(evaluationId, loadingText) {
    const maxAttempts = 120;
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        try {
            const response = await fetch(`${API_BASE_URL}/evaluate/status/${evaluationId}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', 'X-Session-ID': sessionId }
            });
            
            if (!response.ok) throw new Error('Failed to get evaluation status');
            
            const status = await response.json();
            
            if (status.progress) {
                const completed = Object.keys(status.progress).filter(k => status.progress[k] === 'COMPLETED').length;
                loadingText.textContent = `Evaluando pilares... (${completed}/6 completados)`;
            }
            
            if (status.status === 'COMPLETED' && status.results) {
                const results = typeof status.results === 'string' ? JSON.parse(status.results) : status.results;
                
                // Extract pillar data - handle different formats
                const pillars = results.map((r, index) => {
                    // Direct pillar object (has pillar_id at top level)
                    if (r.pillar_id) return r;
                    
                    // Step Functions format with Payload
                    if (r.Payload) {
                        const payload = typeof r.Payload === 'string' ? JSON.parse(r.Payload) : r.Payload;
                        if (payload.pillar_id) return payload;
                        if (payload.body) {
                            const body = typeof payload.body === 'string' ? JSON.parse(payload.body) : payload.body;
                            return body.pillar_id ? body : body;
                        }
                        return payload;
                    }
                    
                    // Lambda response format with statusCode and body
                    if (r.statusCode && r.body) {
                        const body = typeof r.body === 'string' ? JSON.parse(r.body) : r.body;
                        return body.pillar_id ? body : body;
                    }
                    
                    return r;
                });
                
                if (!pillars || pillars.length === 0) throw new Error('No se recibieron datos de pilares');
                return pillars;
            }
            
            if (status.status === 'FAILED') throw new Error('La evaluacion fallo. Revisa los logs en CloudWatch.');
            
            await new Promise(resolve => setTimeout(resolve, 5000));
            attempts++;
        } catch (error) {
            console.error('Polling error:', error);
            throw error;
        }
    }
    throw new Error('Timeout - la evaluacion tomo mas tiempo del esperado');
}

async function storeEvaluation(pillars) {
    try {
        const accountId = sessionStorage.getItem('autowar_account_id');
        if (!accountId) return;
        
        const pillarResults = {};
        pillars.forEach(pillar => { pillarResults[pillar.pillar_id] = pillar; });
        
        const response = await fetch(`${API_BASE_URL}/store-evaluation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id: accountId, pillar_results: pillarResults })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Evaluation stored:', result);
        }
    } catch (error) {
        console.error('Error storing evaluation:', error);
    }
}

function displayResults(pillars) {
    // Save ALL pillars to sessionStorage for analyst view and navigation
    sessionStorage.setItem('dashboard_pillars', JSON.stringify(pillars));
    
    // Hide loading, show dashboard
    document.getElementById('loadingContainer').style.display = 'none';
    document.getElementById('dashboardContainer').style.display = 'block';
    
    const grid = document.getElementById('pillarsGrid');
    grid.innerHTML = ''; // Clear any existing cards
    
    pillars.forEach(pillar => {
        const card = createPillarCard(pillar);
        grid.appendChild(card);
    });
    
    // Add re-evaluate button
    addReEvaluateButton();
}

function addReEvaluateButton() {
    const container = document.getElementById('dashboardContainer');
    // Check if button already exists
    if (document.getElementById('reEvaluateBtn')) return;
    
    const btnDiv = document.createElement('div');
    btnDiv.style.textAlign = 'center';
    btnDiv.style.marginTop = '20px';
    btnDiv.innerHTML = `
        <button id="reEvaluateBtn" onclick="reEvaluate()" style="
            background: #3b82f6; color: white; border: none; padding: 12px 24px;
            border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600;
        ">Ejecutar Nueva Evaluacion</button>
    `;
    container.appendChild(btnDiv);
}

async function reEvaluate() {
    sessionStorage.removeItem('dashboard_pillars');
    document.getElementById('loadingContainer').style.display = 'flex';
    document.getElementById('dashboardContainer').style.display = 'none';
    await startEvaluation();
}

function createPillarCard(pillar) {
    const card = document.createElement('div');
    card.className = 'pillar-card';
    card.style.cursor = 'pointer';
    
    const pillarName = pillar.pillar_name?.es || pillar.pillar_name || pillar.pillar_id || 'Unknown';
    const overallScore = pillar.overall_score || 0;
    const totalBestPractices = pillar.total_best_practices || 0;
    const totalFindings = pillar.total_findings || 0;
    const severityDist = pillar.severity_distribution || { critical: 0, high: 0, medium: 0, low: 0 };
    
    const scoreColor = overallScore >= 80 ? '#10b981' : overallScore >= 60 ? '#f59e0b' : '#ef4444';
    
    card.innerHTML = `
        <div class="pillar-header">
            <div class="pillar-name">${pillarName}</div>
            <div class="pillar-score" style="color: ${scoreColor}">${overallScore.toFixed(1)}%</div>
        </div>
        <div class="pillar-stats">
            <div class="stat">
                <div class="stat-value">${totalBestPractices}</div>
                <div class="stat-label">Best Practices</div>
            </div>
            <div class="stat">
                <div class="stat-value">${totalFindings}</div>
                <div class="stat-label">Hallazgos</div>
            </div>
        </div>
        <div style="margin-top: 15px;">
            ${severityDist.critical > 0 ? `<span class="severity-badge severity-critical">${severityDist.critical} Criticos</span>` : ''}
            ${severityDist.high > 0 ? `<span class="severity-badge severity-high">${severityDist.high} Altos</span>` : ''}
            ${severityDist.medium > 0 ? `<span class="severity-badge severity-medium">${severityDist.medium} Medios</span>` : ''}
        </div>
    `;
    
    card.addEventListener('click', () => {
        sessionStorage.setItem('current_pillar', JSON.stringify(pillar));
        window.location.href = 'analyst.html';
    });
    
    return card;
}
