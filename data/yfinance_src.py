"""Yahoo Finance via the yfinance library."""

import pandas as pd
import yfinance as yf

from config import LOOKBACK_DAYS


def fetch_yfinance(symbol, days=LOOKBACK_DAYS):
    ticker = yf.Ticker(symbol)
    hist   = ticker.history(period=f"{days}d", interval="1d", auto_adjust=False)
    if hist.empty:
        raise RuntimeError(f"yfinance empty for {symbol}")
    df = pd.DataFrame({
        "date":  hist.index,
        "close": hist["Close"].astype(float).values,
    })
    return df.reset_index(drop=True)
