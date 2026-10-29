import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

CLIENT_ID = "YOUR_CLIENT_ID"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

SYMBOL = "RELIANCE.NS"
PAPER_BALANCE = 10000.0  # ₹10,000 Virtual Capital
POSITION = 0  # 0 = No Stock, >0 = Holding

def fetch_live_signal():
    df = yf.download(SYMBOL, period="5d", interval="15m", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Technical Indicators
    df['SMA5'] = df['Close'].rolling(window=5).mean()
    df['SMA20'] = df['Close'].rolling(window=20).mean()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Crossover Logic
    buy_signal = (prev['SMA5'] <= prev['SMA20']) and (latest['SMA5'] > latest['SMA20'])
    sell_signal = (prev['SMA5'] >= prev['SMA20']) and (latest['SMA5'] < latest['SMA20'])

    return latest['Close'], buy_signal, sell_signal

print(f"=== PAPER TRADER STARTED FOR {SYMBOL} ===")
print(f"Initial Paper Balance: ₹{PAPER_BALANCE}\n")

# Run 3 Live Checks (Interval: 10 seconds)
for i in range(1, 4):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price, buy, sell = fetch_live_signal()
    print(f"[{now}] Check #{i} | Current Price: ₹{price:.2f}")

    if buy and POSITION == 0:
        POSITION = 1
        print(f"--> [PAPER TRADE] BUY SIGNAL TRIGGERED! Bought at ₹{price:.2f}")
    elif sell and POSITION == 1:
        POSITION = 0
        print(f"--> [PAPER TRADE] SELL SIGNAL TRIGGERED! Sold at ₹{price:.2f}")
    else:
        print("--> No Trade Signal. Status: HOLDING / WAITING")
    
    time.sleep(10)