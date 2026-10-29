import sqlite3
import threading
import time
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd

app = FastAPI(title="Pro Quant Algo Engine with SQLite Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# High Volume Liquid Indian Stocks
NSE_WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "TATAMOTORS.NS", "ICICIBANK.NS"]
ROUNDTRIP_CHARGES_INR = 30.0  # Estimated Brokerage + STT + Taxes per roundtrip trade

# DB SETUP (Permanent Storage)
DB_FILE = "trades.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            date TEXT,
            symbol TEXT,
            action TEXT,
            price REAL,
            reason TEXT,
            net_pnl REAL,
            pnl_pct REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_state (
            id INTEGER PRIMARY KEY,
            balance REAL
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO account_state (id, balance) VALUES (1, 50000.0)")
    conn.commit()
    conn.close()

init_db()

algo_state = {
    "is_running": False,
    "fast_ma": 3,
    "slow_ma": 8,
    "positions": {}
}

def load_account_balance():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM account_state WHERE id = 1")
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

def update_account_balance(new_balance):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE account_state SET balance = ? WHERE id = 1", (new_balance,))
    conn.commit()
    conn.close()

def save_trade_to_db(timestamp, date_str, symbol, action, price, reason, net_pnl, pnl_pct):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trade_logs (timestamp, date, symbol, action, price, reason, net_pnl, pnl_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, date_str, symbol, action, price, reason, net_pnl, pnl_pct))
    conn.commit()
    conn.close()

def fetch_analytics():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    today_str = datetime.now().strftime("%Y-%m-%d")
    week_ago_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Today P&L
    cursor.execute("SELECT SUM(net_pnl) FROM trade_logs WHERE date = ? AND action = 'SELL'", (today_str,))
    today_pnl = cursor.fetchone()[0] or 0.0

    # Weekly P&L
    cursor.execute("SELECT SUM(net_pnl) FROM trade_logs WHERE date >= ? AND action = 'SELL'", (week_ago_str,))
    weekly_pnl = cursor.fetchone()[0] or 0.0

    # Monthly P&L
    cursor.execute("SELECT SUM(net_pnl) FROM trade_logs WHERE date >= ? AND action = 'SELL'", (month_ago_str,))
    monthly_pnl = cursor.fetchone()[0] or 0.0

    # Overall Total P&L
    cursor.execute("SELECT SUM(net_pnl) FROM trade_logs WHERE action = 'SELL'")
    total_pnl = cursor.fetchone()[0] or 0.0

    # Trade Counter Metrics
    cursor.execute("SELECT COUNT(*) FROM trade_logs WHERE action = 'SELL'")
    total_trades = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM trade_logs WHERE action = 'SELL' AND net_pnl > 0")
    winning_trades = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM trade_logs WHERE action = 'SELL' AND net_pnl <= 0")
    losing_trades = cursor.fetchone()[0] or 0

    # Fetch recent logs
    cursor.execute("SELECT timestamp, symbol, action, price, reason, net_pnl, pnl_pct FROM trade_logs ORDER BY id DESC LIMIT 50")
    raw_logs = cursor.fetchall()
    conn.close()

    formatted_logs = []
    for log in raw_logs:
        pnl_val = log[5]
        pct_val = log[6]
        formatted_logs.append({
            "time": log[0],
            "symbol": log[1],
            "action": log[2],
            "price": f"{log[3]:.2f}",
            "reason": log[4],
            "pnl": f"₹{pnl_val:+.2f}" if log[2] == "SELL" else "-",
            "pnl_pct": f"{pct_val:+.2f}%" if log[2] == "SELL" else "-"
        })

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    return {
        "today_pnl": round(today_pnl, 2),
        "weekly_pnl": round(weekly_pnl, 2),
        "monthly_pnl": round(monthly_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 1),
        "trades_log": formatted_logs
    }

def nse_auto_scanner():
    while algo_state["is_running"]:
        print("--> [NSE SCANNER RUNNING] Monitoring Market Data & Calculating Analytics...")
        for ticker in NSE_WATCHLIST:
            if not algo_state["is_running"]:
                break
            try:
                df = yf.download(ticker, period="5d", interval="1m", progress=False)
                if df.empty or len(df) < 10:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['Fast_MA'] = df['Close'].rolling(window=algo_state["fast_ma"]).mean()
                df['Slow_MA'] = df['Close'].rolling(window=algo_state["slow_ma"]).mean()

                latest = df.iloc[-1]
                prev = df.iloc[-2]

                price = float(latest['Close'])
                fast_curr = float(latest['Fast_MA'])
                slow_curr = float(latest['Slow_MA'])
                fast_prev = float(prev['Fast_MA'])
                slow_prev = float(prev['Slow_MA'])

                clean_symbol = ticker.replace(".NS", "")
                buy_signal = (fast_prev <= slow_prev) and (fast_curr > slow_curr)
                sell_signal = (fast_prev >= slow_prev) and (fast_curr < slow_curr)

                is_holding = clean_symbol in algo_state["positions"]

                now = datetime.now()
                time_str = now.strftime("%H:%M:%S")
                date_str = now.strftime("%Y-%m-%d")

                # 1. BUY SIGNAL
                if buy_signal and not is_holding:
                    algo_state["positions"][clean_symbol] = {
                        "entry_price": price,
                        "entry_time": time_str
                    }
                    save_trade_to_db(
                        timestamp=time_str,
                        date_str=date_str,
                        symbol=clean_symbol,
                        action="BUY",
                        price=round(price, 2),
                        reason=f"Bullish Crossover (MA{algo_state['fast_ma']} > MA{algo_state['slow_ma']})",
                        net_pnl=0.0,
                        pnl_pct=0.0
                    )
                    print(f"🔥 [BUY TRIGGERED] {clean_symbol} @ ₹{price:.2f}")

                # 2. SELL SIGNAL
                elif sell_signal and is_holding:
                    entry = algo_state["positions"].pop(clean_symbol)
                    entry_price = entry["entry_price"]

                    gross_pnl = price - entry_price
                    net_pnl = gross_pnl - ROUNDTRIP_CHARGES_INR  # Deducting ₹30 Taxes & Brokerage
                    pnl_pct = (net_pnl / entry_price) * 100

                    curr_balance = load_account_balance()
                    new_balance = curr_balance + net_pnl
                    update_account_balance(new_balance)

                    save_trade_to_db(
                        timestamp=time_str,
                        date_str=date_str,
                        symbol=clean_symbol,
                        action="SELL",
                        price=round(price, 2),
                        reason=f"Bearish Crossover (MA{algo_state['fast_ma']} < MA{algo_state['slow_ma']})",
                        net_pnl=round(net_pnl, 2),
                        pnl_pct=round(pnl_pct, 2)
                    )
                    print(f"📉 [SELL TRIGGERED] {clean_symbol} @ ₹{price:.2f} | Net P&L: ₹{net_pnl:+.2f}")

            except Exception as e:
                print(f"Scanner error on {ticker}:", e)

        time.sleep(5)

@app.get("/status")
def get_status():
    analytics = fetch_analytics()
    curr_balance = load_account_balance()
    return {
        "is_running": algo_state["is_running"],
        "paper_balance": round(curr_balance, 2),
        "today_pnl_fmt": f"₹{analytics['today_pnl']:+.2f}",
        "weekly_pnl_fmt": f"₹{analytics['weekly_pnl']:+.2f}",
        "monthly_pnl_fmt": f"₹{analytics['monthly_pnl']:+.2f}",
        "total_pnl_fmt": f"₹{analytics['total_pnl']:+.2f}",
        "today_pnl": analytics["today_pnl"],
        "weekly_pnl": analytics["weekly_pnl"],
        "monthly_pnl": analytics["monthly_pnl"],
        "total_pnl": analytics["total_pnl"],
        "total_trades": analytics["total_trades"],
        "winning_trades": analytics["winning_trades"],
        "losing_trades": analytics["losing_trades"],
        "win_rate": analytics["win_rate"],
        "trades_log": analytics["trades_log"]
    }

@app.post("/start-algo")
def start_algo():
    if not algo_state["is_running"]:
        algo_state["is_running"] = True
        t = threading.Thread(target=nse_auto_scanner)
        t.daemon = True
        t.start()
    return {"status": "NSE Engine Started", "running": True}

@app.post("/stop-algo")
def stop_algo():
    algo_state["is_running"] = False
    return {"status": "Engine Stopped", "running": False}