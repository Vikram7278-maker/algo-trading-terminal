import yfinance as yf
import pandas as pd
import numpy as np

# Fetch 1 year of daily historical data
symbol = "RELIANCE.NS"
df = yf.download(symbol, period="1y", interval="1d")

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Calculate SMA Indicators
df['SMA5'] = df['Close'].rolling(window=5).mean()
df['SMA20'] = df['Close'].rolling(window=20).mean()

# Position logic: 1 when holding long, 0 when out of market
df['Position'] = 0
df.loc[df['SMA5'] > df['SMA20'], 'Position'] = 1

# Daily Stock Percentage Return
df['Market_Return'] = df['Close'].pct_change()

# Strategy Return = Position from previous day * Today's Market Return
df['Strategy_Return'] = df['Position'].shift(1) * df['Market_Return']

# Cumulative Returns calculation
df['Cumulative_Market'] = (1 + df['Market_Return']).cumprod()
df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()

# Performance Metrics Calculation
total_market_return = (df['Cumulative_Market'].iloc[-1] - 1) * 100
total_strategy_return = (df['Cumulative_Strategy'].iloc[-1] - 1) * 100

# Drawdown Calculation
peak = df['Cumulative_Strategy'].cummax()
drawdown = (df['Cumulative_Strategy'] - peak) / peak
max_drawdown = drawdown.min() * 100

print("=== BACKTEST PERFORMANCE REPORT (1 YEAR) ===")
print(f"Stock Symbol            : {symbol}")
print(f"Buy & Hold Market Return: {total_market_return:.2f}%")
print(f"Strategy Total Return   : {total_strategy_return:.2f}%")
print(f"Maximum Drawdown (Risk) : {max_drawdown:.2f}%")