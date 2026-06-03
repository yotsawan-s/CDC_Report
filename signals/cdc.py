"""
CDC ActionZone V3 — pure signal calculations.

Logic ported from the Pine Script of piriya33 (TradingView). MPL 2.0.
"""

from config import FAST_EMA, SLOW_EMA, SMOOTH, HISTORY_DAYS


def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()


def rsi(series, period=14):
    """Wilder's RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _classify(price, fast, slow):
    """Map one bar's price/EMA values to (zone, signal, color)."""
    bull = fast > slow
    bear = fast < slow

    if bull and price > fast:
        return "Green", "BUY", "🟢"
    elif bear and price < fast:
        return "Red", "SELL", "🔴"
    elif bull and price < fast and price > slow:
        return "Yellow", "HOLD", "🟡"
    elif bull and price < fast and price < slow:
        return "Orange", "HOLD", "🟠"
    elif bear and price > fast and price > slow:
        return "Blue", "HOLD", "🔵"
    elif bear and price > fast and price < slow:
        return "LightBlue", "HOLD", "🩵"
    else:
        return "Neutral", "HOLD", "⚪"


def calculate_signals_history(df, n_history=HISTORY_DAYS):
    """Compute the CDC signal for the last n_history bars in df."""
    if len(df) < SLOW_EMA + 5:
        raise ValueError(f"ข้อมูลไม่พอ ({len(df)} แท่ง)")

    x_price = ema(df["close"], SMOOTH)
    fast_ma = ema(x_price, FAST_EMA)
    slow_ma = ema(x_price, SLOW_EMA)
    rsi_series = rsi(df["close"])

    history = []
    for i in range(max(0, len(df) - n_history), len(df)):
        price = float(x_price.iloc[i])
        fast  = float(fast_ma.iloc[i])
        slow  = float(slow_ma.iloc[i])
        bull  = fast > slow
        bear  = fast < slow

        zone, signal, color = _classify(price, fast, slow)

        rsi_val = rsi_series.iloc[i]
        history.append({
            "date":        df["date"].iloc[i].strftime("%Y-%m-%d"),
            "close":       float(df["close"].iloc[i]),
            "fast_ma":     fast,
            "slow_ma":     slow,
            "zone":        zone,
            "signal":      signal,
            "color_emoji": color,
            "trend":       "Bullish" if bull else "Bearish" if bear else "Sideways",
            "rsi":         round(float(rsi_val), 2) if rsi_val == rsi_val else 50.0,
        })

    # "New" = the latest actionable signal (BUY/SELL) flips relative to the last
    # remembered BUY/SELL — ignoring HOLD days in between. e.g. S,B,H,H,B → the
    # final B is NOT new (last B/S was already B); only a real B↔S switch is New.
    latest = history[-1]
    latest["fresh_buy"]  = False
    latest["fresh_sell"] = False

    if latest["signal"] in ("BUY", "SELL"):
        # Walk back over the FULL series (not just the n_history window) so that a
        # long HOLD stretch can't make us forget the previous BUY/SELL.
        prev_action = None
        for j in range(len(df) - 2, -1, -1):
            _, sig_j, _ = _classify(
                float(x_price.iloc[j]), float(fast_ma.iloc[j]), float(slow_ma.iloc[j])
            )
            if sig_j in ("BUY", "SELL"):
                prev_action = sig_j
                break

        if prev_action != latest["signal"]:
            if latest["signal"] == "BUY":
                latest["fresh_buy"] = True
            else:
                latest["fresh_sell"] = True

    return history
