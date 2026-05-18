"""
Binance public market data.

Uses data-api.binance.vision because api.binance.com blocks US IPs (GitHub
Actions runs on Microsoft US infra → returns 451 otherwise).
"""

import pandas as pd
import requests

from config import LOOKBACK_DAYS


def fetch_binance(symbol, days=LOOKBACK_DAYS):
    r = requests.get(
        "https://data-api.binance.vision/api/v3/klines",
        params={"symbol": symbol, "interval": "1d", "limit": days},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbav", "tqv", "ignore",
    ])
    df["close"] = df["close"].astype(float)
    df["date"]  = pd.to_datetime(df["close_time"], unit="ms")
    return df[["date", "close"]].reset_index(drop=True)
