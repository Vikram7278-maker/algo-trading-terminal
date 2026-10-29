import yfinance as yf
import pandas as pd

# Fetch 1 year data
symbol = "RELIANCE.NS"
df = yf.download(symbol, period="1y", interval="1d")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Indicators
df['SMA5'] = df['Close'].rolling(window=5).mean()
df['SMA20'] = df['Close'].rolling(window=20).mean()

# Parameters
STOP_LOSS = 0.015   # 1.5% Stop Loss
TAKE_PROFIT = 0.03  # 3.0% Target Profit

in_position = False
entry_price = 0
trades = []

for i in range(1, len(df)):
    current_price = df['Close'].iloc[i]
    prev_sma5 = df['SMA5'].iloc[i-1]
    prev_sma20 = df['SMA20'].iloc[i-1]
    curr_sma5 = df['SMA5'].iloc[i]
    curr_sma20 = df['SMA20'].iloc[i]

    # BUY Signal Crossover
    if not in_position and (prev_sma5 <= prev_sma20) and (curr_sma5 > curr_sma20):
        in_position = True
        entry_price = current_price
        entry_date = df.index[i]

    # Manage Active Trade
    elif in_position:
        pnl_pct = (current_price - entry_price) / entry_price

        # Check Stop Loss, Take Profit, or SELL Crossover
        if pnl_pct <= -STOP_LOSS or pnl_pct >= TAKE_PROFIT or (curr_sma5 < curr_sma20):
            exit_price = current_price
            exit_date = df.index[i]
            trades.append({
                'Entry Date': entry_date,
                'Exit Date': exit_date,
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Return %': pnl_pct * 100
            })
            in_position = False

trades_df = pd.DataFrame(trades)

print("=== RISK-MANAGED STRATEGY PERFORMANCE ===")
if not trades_df.empty:
    win_rate = (len(trades_df[trades_df['Return %'] > 0]) / len(trades_df)) * 100
    print(f"Total Trades Executed : {len(trades_df)}")
    print(f"Win Rate              : {win_rate:.2f}%")
    print(f"Total Strategy Return : {trades_df['Return %'].sum():.2f}%")
    print("\n--- Recent Trades ---")
    print(trades_df.tail(5))
else:
    print("No trades generated.")