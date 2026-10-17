/**
 * Reports Page JavaScript
 * Handles report generation interface
 */

// API Configuration
const API_BASE_URL = 'https://gp3ep01awc.execute-api.us-east-1.amazonaws.com/prod';

// State
let evaluations = [];
let selectedEvaluation = null;

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
});

async function initializePage() {
    // Load evaluations
    await loadEvaluations();
    
    // Setup event listeners
    setupEventListeners();
    
    // Display user info
    displayUserInfo();
    
    // Initialize i18n
    if (typeof initI18n === 'function') {
        initI18n();
    }
}

function setupEventListeners() {
    // Evaluation selector
    document.getElementById('evaluation-select').addEventListener('change', handleEvaluationChange);
    
    // Pilar checkboxes
    const pilarCheckboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');
    pilarCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', validateForm);
    });
    
    // Report type radio buttons
    const reportTypeRadios = document.querySelectorAll('input[name="reportType"]');
    reportTypeRadios.forEach(radio => {
        radio.addEventListener('change', validateForm);
    });
    
    // Generate button
    document.getElementById('generate-report-btn').addEventListener('click', handleGenerateReport);
}

async function loadEvaluations() {
    try {
        // Get account ID from session storage
        const accountId = sessionStorage.getItem('autowar_account_id');
        
        if (!accountId) {
            showError('No se encontró información de la cuenta. Por favor, inicie sesión nuevamente.');
            return;
        }
        
        // Fetch evaluations from API
        const response = await fetch(`${API_BASE_URL}/reports/list?accountId=${accountId}`);
        
        if (!response.ok) {
            throw new Error('Error al cargar evaluaciones');
        }
        
        const data = await response.json();
        evaluations = data.evaluations || [];
        
        // Populate dropdown
        populateEvaluationSelect();
        
    } catch (error) {
        console.error('Error loading evaluations:', error);
        showError('Error al cargar las evaluaciones. Por favor, intente nuevamente.');
    }
}

function populateEvaluationSelect() {
    const select = document.getElementById('evaluation-select');
    
    // Clear existing options (except placeholder)
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // Add evaluation options
    evaluations.forEach(evaluation => {
        const option = document.createElement('option');
        option.value = evaluation.timestamp;
        option.textContent = formatDate(evaluation.timestamp);
        option.dataset.evaluation = JSON.stringify(evaluation);
        select.appendChild(option);
    });
    
    if (evaluations.length === 0) {
        showError('No se encontraron evaluaciones. Por favor, realice una evaluación primero.');
    }
}

function handleEvaluationChange(event) {
    const select = event.target;
    const selectedOption = select.options[select.selectedIndex];
    
    if (select.value && selectedOption.dataset.evaluation) {
        selectedEvaluation = JSON.parse(selectedOption.dataset.evaluation);
        showEvaluationDetails(selectedEvaluation);
    } else {
        selectedEvaluation = null;
        hideEvaluationDetails();
    }
    
    validateForm();
}

function showEvaluationDetails(evaluation) {
    const detailsDiv = document.getElementById('evaluation-details');
    
    document.getElementById('detail-account').textContent = evaluation.accountId;
    document.getElementById('detail-date').textContent = formatDate(evaluation.timestamp);
    document.getElementById('detail-total-bps').textContent = evaluation.totalBestPractices || 0;
    
    detailsDiv.style.display = 'block';
}

function hideEvaluationDetails() {
    document.getElementById('evaluation-details').style.display = 'none';
}

function validateForm() {
    const evaluationSelected = document.getElementById('evaluation-select').value !== '';
    const pilaresSelected = getSelectedPilares().length > 0;
    const reportTypeSelected = document.querySelector('input[name="reportType"]:checked') !== null;
    
    const generateBtn = document.getElementById('generate-report-btn');
    generateBtn.disabled = !(evaluationSelected && pilaresSelected && reportTypeSelected);
}

function getSelectedPilares() {
    const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

async function handleGenerateReport() {
    try {
        // Hide previous messages
        hideError();
        hideSuccess();
        
        // Show loading indicator
        showLoading();
        
        // Get form data
        const accountId = sessionStorage.getItem('autowar_account_id');
        const evaluationTimestamp = document.getElementById('evaluation-select').value;
        const pilares = getSelectedPilares();
        const reportType = document.querySelector('input[name="reportType"]:checked').value;
        const userInfo = JSON.parse(sessionStorage.getItem('autowar_user_info') || '{}');
        
        // Prepare request payload
        const payload = {
            accountId: accountId,
            evaluationTimestamp: evaluationTimestamp,
            pilares: pilares,
            reportType: reportType,
            userInfo: userInfo  // Include user information
        };
        
        // Call API
        const response = await fetch(`${API_BASE_URL}/reports/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al generar el reporte');
        }
        
        const data = await response.json();
        
        // Hide loading
        hideLoading();
        
        // Trigger download
        if (data.reportUrl) {
            downloadReport(data.reportUrl);
            showSuccess('Reporte generado exitosamente. La descarga comenzará automáticamente.');
        } else {
            throw new Error('No se recibió la URL del reporte');
        }
        
    } catch (error) {
        console.error('Error generating report:', error);
        hideLoading();
        showError(`Error al generar el reporte: ${error.message}`);
    }
}

function downloadReport(url) {
    // Create temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function showLoading() {
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('generate-report-btn').disabled = true;
}

function hideLoading() {
    document.getElementById('loading-indicator').style.display = 'none';
    validateForm(); // Re-enable button if form is valid
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}

function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        hideSuccess();
    }, 5000);
}

function hideSuccess() {
    document.getElementById('success-message').style.display = 'none';
}

function formatDate(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return isoString;
    }
}

function displayUserInfo() {
    const userInfo = JSON.parse(sessionStorage.getItem('autowar_user_info') || '{}');
    const accountId = sessionStorage.getItem('autowar_account_id');
    
    // Update page header with user info
    const pageHeader = document.querySelector('.page-header');
    if (pageHeader && userInfo.user_name) {
        const userInfoDiv = document.createElement('div');
        userInfoDiv.style.marginTop = '10px';
        userInfoDiv.style.fontSize = '14px';
        userInfoDiv.style.color = 'rgba(255,255,255,0.9)';
        userInfoDiv.innerHTML = `
            <strong>Cuenta:</strong> ${accountId} | 
            <strong>Usuario:</strong> ${userInfo.user_name} (${userInfo.user_type})
        `;
        pageHeader.appendChild(userInfoDiv);
    }
}
