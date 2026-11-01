from flask import Flask, jsonify, render_template_string
import os
import time
import threading
import requests

app = Flask(__name__)

METAAPI_ACCOUNT_ID = "ad531acb-5260-4c48-ab1c-9542482132b4"
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")

bot_running = False
latest_bid = 0.0
latest_ask = 0.0

# Tier 1 Milestones ($10 -> $1,300 target)
TARGET_MILESTONE = 1300.0

def get_market_price():
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/symbols/XAUUSDm/current-price"
    headers = {"auth-token": METAAPI_TOKEN}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("bid"), data.get("ask")
    except Exception as e:
        print(f"[BOT] Price fetch error: {e}")
    return None, None

def get_account_info():
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/account-information"
    headers = {"auth-token": METAAPI_TOKEN}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"[BOT] Account info error: {e}")
    return None

def close_all_positions():
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {"actionType": "POSITION_CLOSE_ALL"}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"[BOT] Wave profit target locked! Closed all positions: {res.status_code}")
    except Exception as e:
        print(f"[BOT] Error closing positions: {e}")

def execute_tier1_compounding():
    global bot_running, latest_bid, latest_ask
    print("[BOT] Starting Tier 1 Compounding ($10 -> $1,300 Goal)...")
    trade_url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }
    
    last_price = None
    
    while bot_running:
        try:
            account_info = get_account_info()
            if account_info:
                equity = account_info.get("equity", 10.0)
                floating_profit = account_info.get("profit", 0.0)
                
                # Check if total milestone ($1,300) is reached
                if equity >= TARGET_MILESTONE:
                    print("[BOT] Tier 1 Target of $1,300 REACHED! Stopping bot.")
                    close_all_positions()
                    bot_running = False
                    break
                
                # Dynamic wave profit lock based on current equity scale
                wave_target = max(2.0, equity * 0.15) # Takes profit dynamically as account grows
                if floating_profit >= wave_target:
                    close_all_positions()
                    time.sleep(3)
                    continue

                # Calculate lot size based on equity growth
                lot_size = 0.01 if equity < 50 else round(min(0.10, equity / 1000.0), 2)

            bid, ask = get_market_price()
            if bid and ask:
                latest_bid = bid
                latest_ask = ask
                if last_price is not None:
                    price_diff = bid - last_price
                    
                    # Rapid Sell Stack
                    if price_diff < -0.20:
                        payload = {
                            "actionType": "ORDER_TYPE_SELL",
                            "symbol": "XAUUSDm",
                            "volume": lot_size,
                            "comment": f"Tier1 SELL {lot_size}"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=10)
                        print(f"[BOT] Fast SELL executed: {res.status_code}")
                        time.sleep(2)
                        
                    # Rapid Buy Stack
                    elif price_diff > 0.20:
                        payload = {
                            "actionType": "ORDER_TYPE_BUY",
                            "symbol": "XAUUSDm",
                            "volume": lot_size,
                            "comment": f"Tier1 BUY {lot_size}"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=10)
                        print(f"[BOT] Fast BUY executed: {res.status_code}")
                        time.sleep(2)
                
                last_price = bid
            
            time.sleep(8)
            
        except Exception as e:
            print(f"[BOT] Compounding loop error: {e}")
            time.sleep(10)

# HTML Dashboard Interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MT5 Compounding Dashboard</title>
    <style>
        body { background-color: #0b0e11; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 15px; }
        .card { background-color: #181a20; border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #2b2f36; }
        .status-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: bold; margin-bottom: 10px; }
        .badge-connected { color: #0ecb81; background: rgba(14, 203, 129, 0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid #0ecb81; }
        .analysis-box { background: #121418; border-radius: 8px; padding: 10px; margin-top: 10px; }
        .item { display: flex; justify-content: space-between; align-items: center; margin: 8px 0; font-size: 13px; color: #848e9c; }
        .dot { width: 8px; height: 8px; background-color: #0ecb81; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #0ecb81; }
        .btn-group { display: flex; gap: 10px; margin-top: 15px; }
        .btn { flex: 1; padding: 14px; border: none; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; text-align: center; }
        .btn-start { background-color: #0ecb81; color: #000; }
        .btn-stop { background-color: #f6465d; color: #fff; }
        .price-display { text-align: center; font-size: 22px; font-weight: bold; color: #f0b90b; margin: 10px 0; }
        .target-box { background: #1e2329; padding: 10px; border-radius: 6px; text-align: center; color: #0ecb81; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>

    <div class="card">
        <div class="status-header">
            <span>MT5 ACCOUNT</span>
            <span class="badge-connected">● CONNECTED (JustMarkets)</span>
        </div>
        <div class="target-box">TIER 1 GOAL: $10 ➔ $1,300</div>
        <div class="price-display">XAUUSDm: <span id="price">Fetching...</span></div>
        <div class="analysis-box">
            <div class="item"><span>Momentum Stacking</span> <span class="dot"></span></div>
            <div class="item"><span>Dynamic Auto-Scaling</span> <span class="dot"></span></div>
            <div class="item"><span>Profit Target Lock ($1,300)</span> <span class="dot"></span></div>
        </div>
    </div>

    <div class="card">
        <div class="status-header">BOT CONTROL</div>
        <div class="item"><span>Bot Status</span> <strong id="bot-status" style="color: #f6465d;">STOPPED</strong></div>
        <div class="btn-group">
            <button class="btn btn-start" onclick="startBot()">START BOT</button>
            <button class="btn btn-stop" onclick="stopBot()">STOP BOT</button>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('bot-status').innerText = data.running ? 'RUNNING' : 'STOPPED';
                    document.getElementById('bot-status').style.color = data.running ? '#0ecb81' : '#f6465d';
                    if (data.bid) {
                        document.getElementById('price').innerText = data.bid;
                    }
                });
        }

        function startBot() {
            fetch('/start').then(() => updateStatus());
        }

        function stopBot() {
            fetch('/stop').then(() => updateStatus());
        }

        setInterval(updateStatus, 3000);
        updateStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def status_api():
    return jsonify({
        "running": bot_running,
        "bid": latest_bid,
        "ask": latest_ask
    })

@app.route('/start', methods=['GET', 'POST'])
def start_bot():
    global bot_running
    if not METAAPI_TOKEN:
        return jsonify({"status": "error", "message": "METAAPI_TOKEN missing"}), 400
    if not bot_running:
        bot_running = True
        threading.Thread(target=execute_tier1_compounding, daemon=True).start()
        return jsonify({"status": "success", "message": "Tier 1 bot started successfully"})
    return jsonify({"status": "running", "message": "Bot is already running"})

@app.route('/stop', methods=['GET', 'POST'])
def stop_bot():
    global bot_running
    bot_running = False
    return jsonify({"status": "success", "message": "Bot stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                        
