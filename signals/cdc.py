"""
CDC ActionZone V3 — pure signal calculations.

Logic ported from the Pine Script of piriya33 (TradingView). MPL 2.0.
"""

from config import FAST_EMA, SLOW_EMA, SMOOTH, HISTORY_DAYS


def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()


def calculate_signals_history(df, n_history=HISTORY_DAYS):
    """Compute the CDC signal for the last n_history bars in df."""
    if len(df) < SLOW_EMA + 5:
        raise ValueError(f"ข้อมูลไม่พอ ({len(df)} แท่ง)")

    x_price = ema(df["close"], SMOOTH)
    fast_ma = ema(x_price, FAST_EMA)
    slow_ma = ema(x_price, SLOW_EMA)

    history = []
    for i in range(max(0, len(df) - n_history), len(df)):
        price = float(x_price.iloc[i])
        fast  = float(fast_ma.iloc[i])
        slow  = float(slow_ma.iloc[i])
        bull  = fast > slow
        bear  = fast < slow

        if bull and price > fast:
            zone, signal, color = "Green", "BUY", "🟢"
        elif bear and price < fast:
            zone, signal, color = "Red", "SELL", "🔴"
        elif bull and price < fast and price > slow:
            zone, signal, color = "Yellow", "HOLD", "🟡"
        elif bull and price < fast and price < slow:
            zone, signal, color = "Orange", "HOLD", "🟠"
        elif bear and price > fast and price > slow:
            zone, signal, color = "Blue", "HOLD", "🔵"
        elif bear and price > fast and price < slow:
            zone, signal, color = "LightBlue", "HOLD", "🩵"
        else:
            zone, signal, color = "Neutral", "HOLD", "⚪"

        history.append({
            "date":        df["date"].iloc[i].strftime("%Y-%m-%d"),
            "close":       float(df["close"].iloc[i]),
            "fast_ma":     fast,
            "slow_ma":     slow,
            "zone":        zone,
            "signal":      signal,
            "color_emoji": color,
            "trend":       "Bullish" if bull else "Bearish" if bear else "Sideways",
        })

    if len(history) >= 2:
        latest, prev = history[-1], history[-2]
        latest["fresh_buy"]  = latest["signal"] == "BUY"  and prev["signal"] != "BUY"
        latest["fresh_sell"] = latest["signal"] == "SELL" and prev["signal"] != "SELL"
    else:
        history[-1]["fresh_buy"]  = False
        history[-1]["fresh_sell"] = False

    return history
    
