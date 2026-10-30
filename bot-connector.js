const BACKEND_URL = 'https://mt5-bot-7.onrender.com';

async function startBot() {
    try {
        let response = await fetch(`${BACKEND_URL}/start`, { method: 'POST' });
        let data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error('Error starting bot:', error);
    }
}

async function stopBot() {
    try {
        let response = await fetch(`${BACKEND_URL}/stop`, { method: 'POST' });
        let data = await response.json();
        alert(data.message);
    } catch (error) {
        console.error('Error stopping bot:', error);
    }
}

async function checkStatus() {
    try {
        let response = await fetch(`${BACKEND_URL}/status`);
        let data = await response.json();
        console.log("Status:", data.status, "Balance:", data.balance);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

setInterval(checkStatus, 3000);
