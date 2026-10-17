// AutoWAR Analyst View

let pillarData = null;
let allPillars = [];
let selectedQuestion = null;

// Initialize
window.addEventListener('load', () => {
    // Try to get specific pillar from sessionStorage
    const currentPillar = sessionStorage.getItem('current_pillar');
    allPillars = JSON.parse(sessionStorage.getItem('dashboard_pillars') || '[]');
    
    if (currentPillar) {
        try {
            pillarData = JSON.parse(currentPillar);
        } catch (e) {
            console.error('Error parsing current_pillar:', e);
        }
    }
    
    if (pillarData && pillarData.questions && pillarData.questions.length > 0) {
        // Show specific pillar analysis
        showPillarAnalysis();
    } else if (allPillars.length > 0) {
        // Show pillar selector
        showPillarSelector();
    } else {
        // No data at all, redirect to dashboard
        window.location.href = 'dashboard.html';
    }
    
    displayUserInfo();
});

function showPillarAnalysis() {
    const pillarName = pillarData.pillar_name?.es || pillarData.pillar_name || pillarData.pillar_id || 'Pilar';
    document.getElementById('pillarName').textContent = `${pillarName} - Vista de Analista`;
    renderQuestionsList();
}

function showPillarSelector() {
    document.getElementById('pillarName').textContent = 'Vista de Analista - Seleccione un Pilar';
    
    const questionsList = document.getElementById('questionsList');
    questionsList.innerHTML = '';
    
    const title = document.createElement('h3');
    title.textContent = 'Pilares Evaluados';
    title.style.cssText = 'margin-bottom: 15px; color: #333; font-size: 16px;';
    questionsList.appendChild(title);
    
    allPillars.forEach(pillar => {
        const pillarName = pillar.pillar_name?.es || pillar.pillar_name || pillar.pillar_id || 'Unknown';
        const score = pillar.overall_score || 0;
        const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444';
        
        const item = document.createElement('div');
        item.className = 'question-item';
        item.style.cursor = 'pointer';
        item.innerHTML = `
            <div class="question-title" style="font-size: 15px; font-weight: 600;">${pillarName}</div>
            <div class="question-score" style="color: ${scoreColor}">${score.toFixed(1)}%</div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">${pillar.total_best_practices || 0} BPs | ${pillar.total_findings || 0} hallazgos</div>
        `;
        
        item.addEventListener('click', () => {
            pillarData = pillar;
            sessionStorage.setItem('current_pillar', JSON.stringify(pillar));
            showPillarAnalysis();
        });
        
        questionsList.appendChild(item);
    });
    
    // Clear main panel
    document.getElementById('questionTitle').textContent = 'Selecciona un pilar para ver el analisis detallado';
    document.getElementById('questionScore').textContent = '-';
    document.getElementById('bpsEvaluated').textContent = '-';
    document.getElementById('questionStatus').textContent = '-';
    document.getElementById('findingsBody').innerHTML = '';
}

function renderQuestionsList() {
    const questionsList = document.getElementById('questionsList');
    questionsList.innerHTML = '';
    
    // Add "back to all pillars" button
    const backBtn = document.createElement('div');
    backBtn.className = 'question-item';
    backBtn.style.cssText = 'background: #f0f4ff; border-left: 3px solid #3b82f6; cursor: pointer;';
    backBtn.innerHTML = '<div class="question-title" style="color: #3b82f6; font-weight: 600;">&#8592; Todos los Pilares</div>';
    backBtn.addEventListener('click', () => {
        sessionStorage.removeItem('current_pillar');
        pillarData = null;
        showPillarSelector();
    });
    questionsList.appendChild(backBtn);
    
    if (!pillarData || !pillarData.questions) return;
    
    pillarData.questions.forEach((question, index) => {
        const item = document.createElement('div');
        item.className = 'question-item';
        if (index === 0) {
            item.classList.add('active');
            selectedQuestion = question;
        }
        
        // Safe access to title
        const titleText = question.title?.es || question.title?.en || question.title || question.question_id;
        const score = typeof question.score === 'number' ? question.score.toFixed(1) : '0.0';
        
        item.innerHTML = `
            <div class="question-id">${question.question_id}</div>
            <div class="question-title">${titleText}</div>
            <div class="question-score">${score}%</div>
        `;
        
        item.addEventListener('click', () => {
            document.querySelectorAll('.question-item').forEach(q => q.classList.remove('active'));
            item.classList.add('active');
            selectedQuestion = question;
            renderQuestionDetails();
        });
        
        questionsList.appendChild(item);
    });
    
    if (pillarData.questions.length > 0) {
        renderQuestionDetails();
    }
}

function renderQuestionDetails() {
    if (!selectedQuestion) return;
    
    // Safe access to title
    const titleText = selectedQuestion.title?.es || selectedQuestion.title?.en || selectedQuestion.title || selectedQuestion.question_id;
    const score = typeof selectedQuestion.score === 'number' ? selectedQuestion.score.toFixed(1) : '0.0';
    
    document.getElementById('questionTitle').textContent = `${selectedQuestion.question_id}: ${titleText}`;
    document.getElementById('questionScore').textContent = `${score}%`;
    document.getElementById('bpsEvaluated').textContent = selectedQuestion.bps_evaluated || 0;
    
    const statusText = selectedQuestion.status === 'COMPLIANT' ? 'CUMPLE' : 
                      selectedQuestion.status === 'NON_COMPLIANT' ? 'NO CUMPLE' : 'PENDIENTE';
    document.getElementById('questionStatus').textContent = statusText;
    
    const tbody = document.getElementById('findingsBody');
    tbody.innerHTML = '';
    
    if (!selectedQuestion.findings) return;
    
    selectedQuestion.findings.forEach(finding => {
        const row = document.createElement('tr');
        
        if (finding.severity === 'CRITICAL' || finding.severity === 'HIGH') {
            row.style.background = finding.severity === 'CRITICAL' ? '#fff5f5' : '#fff8f0';
        }
        
        const statusClass = finding.status === 'COMPLIANT' ? 'status-compliant' : 
                           finding.status === 'NON_COMPLIANT' ? 'status-non-compliant' : 'status-pending';
        const statusText = finding.status === 'COMPLIANT' ? 'CUMPLE' : 
                          finding.status === 'NON_COMPLIANT' ? 'NO CUMPLE' : 'PENDIENTE';
        
        const severityClass = `severity-${(finding.severity || 'medium').toLowerCase()}`;
        const severityText = finding.severity === 'CRITICAL' ? 'CRITICO' : 
                            finding.severity === 'HIGH' ? 'ALTO' : 
                            finding.severity === 'MEDIUM' ? 'MEDIO' : 'BAJO';
        
        const bpDescription = finding.description || finding.bp || '';
        
        row.innerHTML = `
            <td>
                <span class="bp-id">${finding.bp || ''}</span>
                <div class="bp-description">${bpDescription}</div>
            </td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td><span class="severity-badge ${severityClass}">${severityText}</span></td>
            <td>${finding.finding || ''}</td>
            <td>${finding.risk || ''}</td>
            <td>${finding.remediation || ''}</td>
            <td><div class="evidence-text">${finding.evidence || ''}</div></td>
        `;
        
        tbody.appendChild(row);
    });
}

function displayUserInfo() {
    const userInfo = JSON.parse(sessionStorage.getItem('autowar_user_info') || '{}');
    const accountId = sessionStorage.getItem('autowar_account_id');
    
    const header = document.querySelector('.header');
    if (header && (accountId || userInfo.user_name)) {
        const subtitle = header.querySelector('.subtitle');
        if (subtitle && !document.getElementById('userInfoBar')) {
            const userInfoDiv = document.createElement('div');
            userInfoDiv.id = 'userInfoBar';
            userInfoDiv.style.cssText = 'margin-top: 10px; font-size: 13px; opacity: 0.9;';
            const parts = [];
            if (accountId) parts.push(`<strong>Cuenta:</strong> ${accountId}`);
            if (userInfo.user_name) parts.push(`<strong>Usuario:</strong> ${userInfo.user_name} (${userInfo.user_type || 'Unknown'})`);
            userInfoDiv.innerHTML = parts.join(' | ');
            subtitle.parentNode.insertBefore(userInfoDiv, subtitle.nextSibling);
        }
    }
}
