"""EUA (European Carbon) futures: daily and annual volatility from Yahoo Finance."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

ticker = "ECF"  # European Carbon Futures on Yahoo Finance
end = datetime.now().strftime("%Y-%m-%d")
df = yf.download(ticker, start="2005-01-01", end=end, progress=False, auto_adjust=True, threads=False)
if df.empty or len(df) < 2:
    raise SystemExit("No data")

close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
if isinstance(close.columns, pd.MultiIndex):
    close = close.iloc[:, 0]
close = close.dropna()
close = close[close > 0]
daily_returns = close.pct_change().dropna()

end_dt = close.index[-1]
r5 = daily_returns[daily_returns.index >= (end_dt - pd.DateOffset(years=5))]
r10 = daily_returns[daily_returns.index >= (end_dt - pd.DateOffset(years=10))]

def stats(r):
    daily_vol = r.std(ddof=1)
    if hasattr(daily_vol, "iloc"):
        daily_vol = float(daily_vol.iloc[0]) if daily_vol.ndim else float(daily_vol)
    else:
        daily_vol = float(daily_vol)
    annual_vol = daily_vol * np.sqrt(252)
    return len(r), daily_vol * 100, annual_vol * 100

n5, dv5, av5 = stats(r5)
n10, dv10, av10 = stats(r10)

print("Ticker:", ticker, "(EUA / European Carbon Futures, Yahoo Finance)")
print("Data range:", close.index[0].date(), "-", close.index[-1].date())
print()
print("| Period | Trading days | Daily vol (%) | Annual vol (%) |")
print("|--------|--------------|---------------|----------------|")
print("| 5Y     | {:>11} | {:>13.3f} | {:>14.3f} |".format(n5, dv5, av5))
print("| 10Y    | {:>11} | {:>13.3f} | {:>14.3f} |".format(n10, dv10, av10))
