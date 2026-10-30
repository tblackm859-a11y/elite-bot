import os
import time
import threading
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- CONFIGURATION ---
METAAPI_ACCOUNT_ID = "ad531acb-5260-4c48-ab1c-9542482132b4"
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN", "YOUR_METAAPI_TOKEN_HERE")

bot_running = False

def execute_trading_strategy():
    global bot_running
    print("[BOT] Strategy worker started...")
    url = f"https://mt-client-api-v1.agiliumtrade.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }

    while bot_running:
        try:
            payload = {
                "actionType": "ORDER_TYPE_SELL",
                "symbol": "XAUUSDm",
                "volume": 0.01,
                "comment": "Elite bot SELL"
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"[MetaApi Response]: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[ERROR] Failed to execute trade: {e}")
            
        for _ in range(5):
            if not bot_running:
                break
            time.sleep(1)
            
    print("[BOT] Strategy worker stopped.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bot-control', methods=['POST'])
def bot_control():
    global bot_running
    data = request.get_json()
    action = data.get('action')
    
    if action == 'start':
        if not bot_running:
            bot_running = True
            threading.Thread(target=execute_trading_strategy, daemon=True).start()
        return jsonify({"status": "RUNNING", "message": "Elite Bot started successfully!"})
        
    elif action == 'stop':
        bot_running = False
        return jsonify({"status": "STOPPED", "message": "Elite Bot stopped."})
        
    return jsonify({"status": "UNKNOWN", "message": "Invalid action"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
      
