from flask import Flask, jsonify
import os
import time
import threading
import requests

app = Flask(__name__)

METAAPI_ACCOUNT_ID = "ad531acb-5260-4c48-ab1c-9542482132b4"
METAAPI_TOKEN = os.getenv("METAAPI_TOKEN")

bot_running = False

def get_market_price():
    # Fetch latest price from MetaApi to evaluate momentum
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

def execute_momentum_stacking():
    global bot_running
    print("[BOT] Dynamic Momentum Stacking worker started...")
    trade_url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }
    
    last_price = None
    
    while bot_running:
        try:
            bid, ask = get_market_price()
            if bid and ask:
                if last_price is not None:
                    price_diff = bid - last_price
                    
                    # If market is dropping (Selling momentum) -> Fast Sell
                    if price_diff < -0.20:
                        payload = {
                            "actionType": "ORDER_TYPE_SELL",
                            "symbol": "XAUUSDm",
                            "volume": 0.01,
                            "comment": "Momentum FAST SELL"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=10)
                        print(f"[BOT] Drop detected! Fast SELL response: {res.status_code}, {res.text}")
                        time.sleep(5) # Fast interval during strong momentum
                        
                    # If market is rising (Buying momentum) -> Fast Buy
                    elif price_diff > 0.20:
                        payload = {
                            "actionType": "ORDER_TYPE_BUY",
                            "symbol": "XAUUSDm",
                            "volume": 0.01,
                            "comment": "Momentum FAST BUY"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=10)
                        print(f"[BOT] Surge detected! Fast BUY response: {res.status_code}, {res.text}")
                        time.sleep(5) # Fast interval during strong momentum
                
                last_price = bid
            
            # Normal resting check interval
            time.sleep(30)
            
        except Exception as e:
            print(f"[BOT] Error in momentum loop: {e}")
            time.sleep(15)

@app.route('/')
def index():
    return "Dynamic Momentum Stacking Bot is Live & Ready!"

@app.route('/start', methods=['GET', 'POST'])
def start_bot():
    global bot_running
    if not METAAPI_TOKEN:
        return jsonify({"status": "error", "message": "METAAPI_TOKEN missing"}), 400
    if not bot_running:
        bot_running = True
        threading.Thread(target=execute_momentum_stacking, daemon=True).start()
        return jsonify({"status": "success", "message": "Momentum bot started successfully"})
    return jsonify({"status": "running", "message": "Bot is already running"})

@app.route('/stop', methods=['GET', 'POST'])
def stop_bot():
    global bot_running
    bot_running = False
    return jsonify({"status": "success", "message": "Bot stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
