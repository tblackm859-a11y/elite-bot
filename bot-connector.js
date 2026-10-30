const BACKEND_URL = 'https://mt5-bot-7.onrender.com';

function updateUI(status) {
    const badge = document.querySelector('.status-badge') || document.querySelector('.badge') || document.querySelector('span'); 
    // This finds your status indicator element and updates it
    const statusElements = document.querySelectorAll('.status, [class*="status"], .stopped, .running');
    
    statusElements.forEach(el => {
        if (el.innerText.includes('STOPPED') || el.innerText.includes('RUNNING')) {
            el.innerText = status.toUpperCase();
            if (status.toUpperCase() === 'RUNNING') {
                el.classList.add('active', 'running');
                el.classList.remove('stopped');
            } else {
                el.classList.remove('active', 'running');
                el.classList.add('stopped');
            }
        }
    });
}

async function startBot() {
    try {
        let response = await fetch(`${BACKEND_URL}/start`);
        let data = await response.json();
        alert(data.message);
        updateUI('RUNNING');
    } catch (error) {
        console.error('Error starting bot:', error);
    }
}

async function stopBot() {
    try {
        let response = await fetch(`${BACKEND_URL}/stop`);
        let data = await response.json();
        alert(data.message);
        updateUI('STOPPED');
    } catch (error) {
        console.error('Error stopping bot:', error);
    }
}

async function checkStatus() {
    try {
        let response = await fetch(`${BACKEND_URL}/status`);
        let data = await response.json();
        if (data.status) {
            updateUI(data.status);
        }
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

setInterval(checkStatus, 3000);
