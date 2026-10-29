import yfinance as yf
import pandas as pd

# Fetch historical daily data for a stock (e.g., RELIANCE.NS)
symbol = "RELIANCE.NS"
df = yf.download(symbol, period="6mo", interval="1d")

# Clean column headers if multi-index
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Calculate 5-day and 20-day Simple Moving Averages
df['SMA5'] = df['Close'].rolling(window=5).mean()
df['SMA20'] = df['Close'].rolling(window=20).mean()

# Signal Logic: 1 for BUY, -1 for SELL, 0 for HOLD
df['Signal'] = 0

# SMA5 > SMA20 when previous day SMA5 <= SMA20 -> BUY
df.loc[(df['SMA5'] > df['SMA20']) & (df['SMA5'].shift(1) <= df['SMA20'].shift(1)), 'Signal'] = 1

# SMA5 < SMA20 when previous day SMA5 >= SMA20 -> SELL
df.loc[(df['SMA5'] < df['SMA20']) & (df['SMA5'].shift(1) >= df['SMA20'].shift(1)), 'Signal'] = -1

# Filter only rows where Buy/Sell signals occurred
signals_df = df[df['Signal'] != 0][['Close', 'SMA5', 'SMA20', 'Signal']]

print("=== Recent Generated Signals ===")
print(signals_df.tail(10))