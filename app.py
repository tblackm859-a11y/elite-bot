from flask import Flask, jsonify, render_template_string, request
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

bot_status_message = "Elite Bot is monitoring your MT5 account"
last_action = "Ready"

account_config = {
    "login": "1200453988",
    "password": "********",
    "server": "JustMarkets-Demo3",
    "type": "Demo",
    "balance": 0.0,
    "equity": 0.0
}

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
    global account_config
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/account-information"
    headers = {"auth-token": METAAPI_TOKEN}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            info = res.json()
            account_config["login"] = str(info.get("login", account_config["login"]))
            account_config["server"] = info.get("server", account_config["server"])
            account_config["balance"] = info.get("balance", 0.0)
            account_config["equity"] = info.get("equity", 0.0)
            return info
    except Exception as e:
        print(f"[BOT] Account info error: {e}")
    return None

def close_all_positions():
    global last_action
    url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {"actionType": "POSITION_CLOSE_ALL"}
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
        last_action = "Target Profit Wave Hit - Closed All Positions!"
    except Exception as e:
        print(f"[BOT] Close error: {e}")

def execute_momentum_stacking():
    global bot_running, latest_bid, latest_ask, bot_status_message, last_action
    trade_url = f"https://mt-client-api-v1.new-york.agiliumtrade.ai/users/current/accounts/{METAAPI_ACCOUNT_ID}/trade"
    headers = {
        "auth-token": METAAPI_TOKEN,
        "Content-Type": "application/json"
    }
    
    last_price = None
    bot_status_message = "Fast Stacking Strategy Executing..."
    
    while bot_running:
        try:
            account_info = get_account_info()
            if account_info:
                equity = account_info.get("equity", 10.0)
                floating_profit = account_info.get("profit", 0.0)
                
                if equity >= TARGET_MILESTONE:
                    close_all_positions()
                    bot_status_message = "Target Goal Achieved ($1,300)!"
                    bot_running = False
                    break
                
                wave_target = max(2.0, equity * 0.15)
                if floating_profit >= wave_target:
                    close_all_positions()
                    last_action = f"Locked Profit Wave: ${floating_profit:.2f}"
                    time.sleep(2)
                    continue

                lot_size = 0.01 if equity < 50 else round(min(0.10, equity / 1000.0), 2)

            bid, ask = get_market_price()
            if bid and ask:
                latest_bid = bid
                latest_ask = ask
                
                if last_price is not None:
                    price_diff = bid - last_price
                    
                    if price_diff <= -0.15:
                        payload = {
                            "actionType": "ORDER_TYPE_SELL",
                            "symbol": "XAUUSDm",
                            "volume": lot_size,
                            "comment": "Fast Momentum SELL"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=5)
                        if res.status_code in [200, 201]:
                            last_action = f"Auto-SOLD {lot_size} lots at {bid}"
                        time.sleep(1)
                        
                    elif price_diff >= 0.15:
                        payload = {
                            "actionType": "ORDER_TYPE_BUY",
                            "symbol": "XAUUSDm",
                            "volume": lot_size,
                            "comment": "Fast Momentum BUY"
                        }
                        res = requests.post(trade_url, headers=headers, json=payload, timeout=5)
                        if res.status_code in [200, 201]:
                            last_action = f"Auto-BOUGHT {lot_size} lots at {ask}"
                        time.sleep(1)
                
                last_price = bid
            
            time.sleep(2)
            
        except Exception as e:
            bot_status_message = f"Loop Exception: {str(e)[:25]}"
            time.sleep(3)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Elite MT5 Bot Dashboard</title>
    <style>
        body { background-color: #0b0f0d; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 12px; }
        .card { background-color: #121814; border-radius: 16px; padding: 16px; margin-bottom: 15px; border: 1px solid #1c2720; box-shadow: 0 6px 16px rgba(0,0,0,0.7); }
        .header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .connected-title { display: flex; align-items: center; gap: 6px; color: #10b981; font-weight: bold; font-size: 13px; letter-spacing: 0.5px; }
        .connected-sub { font-size: 11px; color: #047857; margin-top: 2px; margin-bottom: 12px; font-style: italic; }
        .edit-btn { background: #18221c; border: 1px solid #28382e; color: #10b981; padding: 4px 12px; border-radius: 8px; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 4px; }
        
        .section-header { display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: bold; color: #f59e0b; margin-bottom: 12px; letter-spacing: 0.5px; }
        .clear-btn { background: #261416; border: 1px solid #451a1d; color: #f87171; padding: 3px 10px; border-radius: 8px; font-size: 10px; cursor: pointer; }
        
        .info-row { display: flex; justify-content: space-between; margin: 9px 0; font-size: 12px; color: #6b7280; font-style: italic; }
        .info-row span.val { color: #e5e7eb; font-weight: 500; font-style: normal; }
        
        .chart-box { background: #080c0a; border-radius: 12px; padding: 12px; border: 1px solid #151e18; margin: 12px 0; text-align: center; }
        .sparkline { width: 100%; height: 45px; stroke: #f59e0b; stroke-width: 2.5; fill: none; }
        
        .analysis-box { background: #121915; border: 1px solid #1f2c24; padding: 12px 14px; border-radius: 20px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #10b981; font-style: italic; }
        .dot { width: 8px; height: 8px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
        
        .sub-footer { font-size: 11px; color: #10b981; text-align: center; margin-top: 14px; margin-bottom: 4px; font-style: italic; opacity: 0.8; }
        
        .status-badge-stopped { color: #f87171; background: rgba(239, 68, 68, 0.1); border: 1px solid #7f1d1d; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        .status-badge-running { color: #10b981; background: rgba(16, 185, 129, 0.1); border: 1px solid #065f46; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        
        .btn-container { display: flex; gap: 12px; margin-top: 14px; }
        .btn { flex: 1; padding: 12px; border-radius: 12px; font-weight: bold; font-size: 12px; cursor: pointer; text-align: center; border: none; letter-spacing: 0.5px; }
        .btn-start { background-color: #064e3b; color: #34d399; border: 1px solid #047857; }
        .btn-stop { background-color: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; }

        #edit-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 100; justify-content: center; align
    
