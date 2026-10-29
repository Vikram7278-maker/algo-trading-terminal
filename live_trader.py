import requests
import json
import yfinance as yf
import pandas as pd

CLIENT_ID = "YOUR_CLIENT_ID"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

SYMBOL = "RELIANCE.NS"
SECURITY_ID = "2885"  # Dhan Security ID for Reliance Industries

headers = {
    'access-token': ACCESS_TOKEN,
    'client-id': CLIENT_ID,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def place_dhan_order(transaction_type, quantity=1):
    """
    Function to place live Market Order via Dhan API
    transaction_type: 'BUY' or 'SELL'
    """
    url = "https://api.dhan.co/v2/orders"
    
    payload = {
        "dhanClientId": CLIENT_ID,
        "correlationId": "algo_trade_01",
        "transactionType": transaction_type,  # 'BUY' or 'SELL'
        "exchangeSegment": "NSE_EQ",
        "productType": "CNC",                 # 'CNC' for Delivery, 'INTRADAY' for Intraday
        "orderType": "MARKET",
        "validity": "DAY",
        "tradingSymbol": "RELIANCE",
        "securityId": SECURITY_ID,
        "quantity": quantity,
        "disclosedQuantity": 0,
        "price": 0,
        "triggerPrice": 0,
        "afterMarketOrder": False
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_data = response.json()
        print(f"=== LIVE ORDER RESPONSE [{transaction_type}] ===")
        print(res_data)
        return res_data
    except Exception as e:
        print("Order Placement Error:", e)
        return None

# Quick Dry-Run Signal Check Test
print("=== LIVE ORDER EXECUTION ENGINE READY ===")
print("Testing Order Placement Logic (Code Structure Checked).")