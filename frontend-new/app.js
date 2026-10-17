// AutoWAR Frontend - Credential Validation

const API_BASE_URL = 'https://gp3ep01awc.execute-api.us-east-1.amazonaws.com/prod';

const form = document.getElementById('credentialsForm');
const statusDiv = document.getElementById('status');
const submitBtn = document.getElementById('submitBtn');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Parse regions from comma-separated input
    const regionsInput = document.getElementById('regions').value;
    const regions = regionsInput.split(',').map(r => r.trim()).filter(r => r.length > 0);
    
    if (regions.length === 0) {
        showStatus('error', '✗ Debe ingresar al menos una región');
        return;
    }
    
    const credentials = {
        access_key_id: document.getElementById('accessKeyId').value,
        secret_access_key: document.getElementById('secretAccessKey').value,
        session_token: document.getElementById('sessionToken').value || null,
        account_id: document.getElementById('accountId').value,
        regions: regions  // Send array of regions
    };
    
    showStatus('loading', `Validando credenciales para ${regions.length} región(es)...`);
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/credentials/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('success', `✓ Credenciales validadas para ${regions.length} región(es). Session ID: ${data.session_id}`);
            // Store session ID, account ID, regions, and user info for subsequent requests
            sessionStorage.setItem('autowar_session_id', data.session_id);
            sessionStorage.setItem('autowar_expires_at', data.expires_at);
            sessionStorage.setItem('autowar_regions', JSON.stringify(regions));
            sessionStorage.setItem('autowar_account_id', credentials.account_id);
            
            // Store user information
            if (data.user_info) {
                sessionStorage.setItem('autowar_user_info', JSON.stringify(data.user_info));
            }
            
            // Redirect to dashboard after 2 seconds
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 2000);
        } else {
            showStatus('error', `✗ Error: ${data.message || data.error}`);
        }
    } catch (error) {
        showStatus('error', `✗ Error de conexión: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
    }
});

function showStatus(type, message) {
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
}
