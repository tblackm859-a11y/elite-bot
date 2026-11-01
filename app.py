from flask import Flask, jsonify
import os
import time
import threading
import requests

app = Flask(__name__)

METAAPI_ACCOUNT_ID = "ad531acb-5260-4c48-ab1c-9542482132b4"
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")

bot_running = False

def execute_trading_strategy():
    global bot_running
    print("[BOT] Strategy worker started...")
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
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
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"[BOT] Trade response: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"[BOT] Error executing trade: {e}")
        
        time.sleep(60)

@app.route('/')
def index():
    return "MT5 Stacking Bot is Live & Ready!"

@app.route('/start', methods=['GET', 'POST'])
def start_bot():
    global bot_running
    if not METAAPI_TOKEN:
        return jsonify({"status": "error", "message": "METAAPI_TOKEN missing"}), 400
    if not bot_running:
        bot_running = True
        threading.Thread(target=execute_trading_strategy, daemon=True).start()
        return jsonify({"status": "success", "message": "Bot started successfully"})
    return jsonify({"status": "running", "message": "Bot is already running"})

@app.route('/stop', methods=['GET', 'POST'])
def stop_bot():
    global bot_running
    bot_running = False
    return jsonify({"status": "success", "message": "Bot stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                
