"""Bitkub TradingView-compatible history endpoint."""

from datetime import datetime, timezone

import pandas as pd
import requests

from config import LOOKBACK_DAYS


def fetch_bitkub(symbol, days=LOOKBACK_DAYS):
    end_ts   = int(datetime.now(timezone.utc).timestamp())
    start_ts = end_ts - days * 86400
    r = requests.get(
        "https://api.bitkub.com/tradingview/history",
        params={
            "symbol":     symbol.upper(),
            "resolution": "1D",
            "from":       start_ts,
            "to":         end_ts,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("s") != "ok":
        raise RuntimeError(f"Bitkub API error: {data}")
    df = pd.DataFrame({
        "date":  pd.to_datetime(data["t"], unit="s"),
        "close": [float(x) for x in data["c"]],
    })
    return df.reset_index(drop=True)
