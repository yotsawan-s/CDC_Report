"""
CDC ActionZone V3 - Daily Report (HTML Page Version)
รันทุกวัน 7:00 น. → สร้าง index.html → publish ผ่าน GitHub Pages
URL: https://YOURUSERNAME.github.io/REPONAME/

Logic port มาจาก Pine Script ของ piriya33
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from html_builder import build_html


# import for local host
import threading
import webbrowser
import time
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer



# ==============================================================================
# กำหนดสินทรัพย์
# ==============================================================================
ASSETS = [
    ("BTC/USD",        "binance",  "BTCUSDT"),
    ("BTC/THB",        "bitkub",   "BTC_THB"),
    ("DOGE/THB",       "bitkub",   "DOGE_THB"),
    ("KUB/THB",       "bitkub",   "KUB_THB"),
    ("XAU/USD (Gold)", "yfinance", "GC=F"),
    ("TSM",            "yfinance", "TSM"),
    ("AMD",            "yfinance", "AMD"),
    ("NVDA",           "yfinance", "NVDA"),
    ("TSLA",           "yfinance", "TSLA"),
    ("GOOGL",          "yfinance", "GOOGL"),
]

FAST_EMA = 12
SLOW_EMA = 26
SMOOTH = 1
LOOKBACK_DAYS = 300

OUTPUT_DIR = Path("docs")     # GitHub Pages serve จากโฟลเดอร์นี้
HISTORY_DAYS = 14             # เก็บประวัติย้อนหลังแสดงผล


# ==============================================================================
# ดึงข้อมูล (เหมือนเดิม)
# ==============================================================================
def fetch_binance(symbol, days=LOOKBACK_DAYS):
    # ใช้ data-api.binance.vision แทน api.binance.com
    # เพราะ api.binance.com บล็อก IP จาก US (GitHub Actions runs on Microsoft US servers → 451 error)
    r = requests.get(
        "https://data-api.binance.vision/api/v3/klines",
        params={"symbol": symbol, "interval": "1d", "limit": days},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbav", "tqv", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["date"] = pd.to_datetime(df["close_time"], unit="ms")
    return df[["date", "close"]].reset_index(drop=True)


def fetch_bitkub(symbol, days=LOOKBACK_DAYS):
    end_ts = int(datetime.now(timezone.utc).timestamp())
    start_ts = end_ts - days * 86400
    r = requests.get(
        "https://api.bitkub.com/tradingview/history",
        params={
            "symbol": symbol.upper(),
            "resolution": "1D",
            "from": start_ts,
            "to": end_ts,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("s") != "ok":
        raise RuntimeError(f"Bitkub API error: {data}")
    df = pd.DataFrame({
        "date": pd.to_datetime(data["t"], unit="s"),
        "close": [float(x) for x in data["c"]],
    })
    return df.reset_index(drop=True)


def fetch_yfinance(symbol, days=LOOKBACK_DAYS):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=f"{days}d", interval="1d", auto_adjust=False)
    if hist.empty:
        raise RuntimeError(f"yfinance empty for {symbol}")
    df = pd.DataFrame({
        "date": hist.index,
        "close": hist["Close"].astype(float).values,
    })
    return df.reset_index(drop=True)


def fetch_data(source, symbol):
    return {"binance": fetch_binance, "bitkub": fetch_bitkub, "yfinance": fetch_yfinance}[source](symbol)


# ==============================================================================
# CDC Logic
# ==============================================================================
def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()


def calculate_signals_history(df, n_history=HISTORY_DAYS):
    """คำนวณ signal ของแต่ละแท่ง n_history แท่งล่าสุด"""
    if len(df) < SLOW_EMA + 5:
        raise ValueError(f"ข้อมูลไม่พอ ({len(df)} แท่ง)")

    x_price = ema(df["close"], SMOOTH)
    fast_ma = ema(x_price, FAST_EMA)
    slow_ma = ema(x_price, SLOW_EMA)

    history = []
    for i in range(max(0, len(df) - n_history), len(df)):
        price, fast, slow = float(x_price.iloc[i]), float(fast_ma.iloc[i]), float(slow_ma.iloc[i])
        bull = fast > slow
        bear = fast < slow

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
            "date": df["date"].iloc[i].strftime("%Y-%m-%d"),
            "close": float(df["close"].iloc[i]),
            "fast_ma": fast,
            "slow_ma": slow,
            "zone": zone,
            "signal": signal,
            "color_emoji": color,
            "trend": "Bullish" if bull else "Bearish" if bear else "Sideways",
        })

    # fresh signals = แท่งล่าสุดเปลี่ยนจากแท่งก่อน
    if len(history) >= 2:
        latest, prev = history[-1], history[-2]
        latest["fresh_buy"] = latest["signal"] == "BUY" and prev["signal"] != "BUY"
        latest["fresh_sell"] = latest["signal"] == "SELL" and prev["signal"] != "SELL"
    else:
        history[-1]["fresh_buy"] = False
        history[-1]["fresh_sell"] = False

    return history

# ==============================================================================
# start local host
# ==============================================================================


def start_local_server(port=8000, directory="docs", open_browser=True):
    """
    Serve static files from `directory` on http://localhost:{port}
    - ไม่เปลี่ยน cwd ของโปรเซส
    - reuse port ได้
    - รอ server พร้อมก่อนเปิด browser
    """
    class ReusableTCPServer(TCPServer):
        allow_reuse_address = True

    handler_cls = lambda *args, **kwargs: SimpleHTTPRequestHandler(
        *args, directory=directory, **kwargs
    )

    httpd = ReusableTCPServer(("127.0.0.1", port), handler_cls)

    def run():
        print(f"🌐 Serving '{directory}' at http://localhost:{port}")
        try:
            httpd.serve_forever()
        finally:
            httpd.server_close()

    thread = threading.Thread(target=run, daemon=False)
    thread.start()

    # รอให้ bind เสร็จก่อน (กันเปิด browser แล้วเข้าไม่ได้)
    time.sleep(0.5)

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")

    return httpd, thread


# ==============================================================================
# Main
# ==============================================================================
def main():
    print(f"🔄 เริ่มรัน CDC Report — {datetime.now()}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []
    for name, source, symbol in ASSETS:
        print(f"  → {name} ({source}: {symbol})", flush=True)
        try:
            df = fetch_data(source, symbol)
            history = calculate_signals_history(df)
            all_results.append({"name": name, "history": history})
            last = history[-1]
            print(f"    {last['color_emoji']} {last['signal']} | close={last['close']:.4f} | zone={last['zone']}")
        except Exception as e:
            print(f"    ⚠️ {e}")
            all_results.append({"name": name, "error": str(e)})

    html = build_html(all_results)
    out_path = OUTPUT_DIR / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Wrote {out_path} ({len(html):,} bytes)")

    # เก็บ JSON สำหรับ debug หรือทำ history ในอนาคต
    json_path = OUTPUT_DIR / "data.json"
    json_path.write_text(
        json.dumps({"updated": datetime.now(timezone.utc).isoformat(), "assets": all_results}, default=str, indent=2),
        encoding="utf-8",
    )
    print(f"✅ Wrote {json_path}")

    httpd, thread = start_local_server(port=8000, directory="docs")

    # กันโปรแกรมจบทันที (ไม่งั้น server ดับ)
    try:
        thread.join()
        print(f"loacal host go live!!")
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        httpd.shutdown()
        


if __name__ == "__main__":
    main()
