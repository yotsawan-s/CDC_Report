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
# Format helpers
# ==============================================================================
def format_price(p):
    if p >= 1000:
        return f"{p:,.2f}"
    elif p >= 1:
        return f"{p:,.4f}"
    else:
        return f"{p:.8f}"


def format_date_short(date_str):
    """แปลง '2026-04-25' → '25 Apr' และคำนวณว่ากี่วันที่แล้ว"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.now(timezone(timedelta(hours=7))).date()
        delta = (today - dt.date()).days
        short = dt.strftime("%d %b")
        if delta == 0:
            ago = "today"
        elif delta == 1:
            ago = "1d ago"
        else:
            ago = f"{delta}d ago"
        return short, ago, delta
    except Exception:
        return date_str, "", 0


# ==============================================================================
# สร้าง index.html (responsive, ดูบนมือถือก็สวย)
# ==============================================================================
def build_html(all_results):
    bkk_now = datetime.now(timezone(timedelta(hours=7)))
    date_str = bkk_now.strftime("%Y-%m-%d %H:%M")

    # นับสัญญาณ
    latest = [r["history"][-1] for r in all_results if r.get("history")]
    buys = sum(1 for r in latest if r["signal"] == "BUY")
    sells = sum(1 for r in latest if r["signal"] == "SELL")
    holds = sum(1 for r in latest if r["signal"] == "HOLD")

    fresh = []
    for r in all_results:
        if not r.get("history"):
            continue
        last = r["history"][-1]
        if last.get("fresh_buy"):
            fresh.append((r["name"], "BUY"))
        elif last.get("fresh_sell"):
            fresh.append((r["name"], "SELL"))

    # === สร้างแถวตาราง ===
    rows = []
    for r in all_results:
        if r.get("error"):
            rows.append(f"""
            <tr class="row-error">
              <td>{r['name']}</td>
              <td colspan="4">⚠️ {r['error']}</td>
            </tr>""")
            continue

        last = r["history"][-1]
        sig = last["signal"]
        css_sig = sig.lower()

        fresh_badge = ""
        if last.get("fresh_buy"):
            fresh_badge = '<span class="badge badge-buy">NEW</span>'
        elif last.get("fresh_sell"):
            fresh_badge = '<span class="badge badge-sell">NEW</span>'

        # สร้าง sparkline (กราฟเส้นเล็ก) จาก history
        sparkline_svg = build_sparkline(r["history"])

        # JSON data สำหรับ chart รายวันพอกดเข้าไปดู
        chart_id = r["name"].replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
        history_json = json.dumps([
            {"d": h["date"], "c": h["close"], "s": h["signal"]} for h in r["history"]
        ])

        date_short, ago, days_ago = format_date_short(last["date"])
        # เน้นสีถ้าข้อมูลเก่ากว่า 1 วัน (เพื่อให้เห็นชัดว่าหุ้น/ทองหยุดเสาร์-อาทิตย์)
        date_class = "stale" if days_ago > 1 else ""

        rows.append(f"""
        <tr class="row-clickable" data-target="row-{chart_id}">
          <td class="cell-name">
            <span class="expand-icon">▸</span>
            {r['name']}
          </td>
          <td class="cell-price">{format_price(last['close'])}</td>
          <td class="cell-asof {date_class}">
            <div class="asof-date">{date_short}</div>
            <div class="asof-ago">{ago}</div>
          </td>
          <td class="cell-signal cell-{css_sig}">
            <span class="emoji">{last['color_emoji']}</span>
            <span class="sig-text">{sig}</span>
            {fresh_badge}
          </td>
          <td class="cell-sparkline">{sparkline_svg}</td>
        </tr>
        <tr id="row-{chart_id}" class="row-detail" style="display:none;">
          <td colspan="5">
            <div class="detail-content">
              <div class="detail-grid">
                <div><span class="lbl">Trend</span><span class="val">{last['trend']}</span></div>
                <div><span class="lbl">EMA12</span><span class="val mono">{format_price(last['fast_ma'])}</span></div>
                <div><span class="lbl">EMA26</span><span class="val mono">{format_price(last['slow_ma'])}</span></div>
              </div>
              <div class="history-strip">
                <div class="history-label">{HISTORY_DAYS} วันย้อนหลัง:</div>
                <div class="history-cells">
                  {build_history_cells(r['history'])}
                </div>
              </div>
            </div>
          </td>
        </tr>""")

    rows_html = "\n".join(rows)

    # === Alert banner ===
    alert_html = ""
    if fresh:
        items = " · ".join(f"<strong>{n}</strong> {s}" for n, s in fresh)
        alert_html = f"""
        <div class="alert">
          <div class="alert-title">🚨 สัญญาณใหม่วันนี้</div>
          <div class="alert-body">{items}</div>
        </div>"""

    # === Full HTML ===
    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="3600">
  <title>CDC ActionZone Daily Report</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📊</text></svg>">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, "Segoe UI", "Helvetica Neue", "Sukhumvit Set", sans-serif;
      background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%);
      color: #1a1a1a;
      min-height: 100vh;
      padding: 16px;
      line-height: 1.5;
    }}
    .wrap {{ max-width: 900px; margin: 0 auto; }}

    .header {{
      background: #fff;
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.04);
      margin-bottom: 16px;
    }}
    .header h1 {{ font-size: 22px; color: #1a1a1a; margin-bottom: 4px; }}
    .header .subtitle {{ color: #888; font-size: 13px; }}
    .header .meta {{ color: #aaa; font-size: 12px; margin-top: 4px; }}

    .summary {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 16px;
    }}
    .stat {{
      background: #fff;
      padding: 16px 12px;
      border-radius: 10px;
      text-align: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }}
    .stat-num {{ font-size: 28px; font-weight: 700; line-height: 1; margin-bottom: 4px; }}
    .stat-label {{ font-size: 12px; color: #666; }}
    .stat.buy .stat-num {{ color: #16a34a; }}
    .stat.hold .stat-num {{ color: #ca8a04; }}
    .stat.sell .stat-num {{ color: #dc2626; }}

    .alert {{
      background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
      border-left: 4px solid #f59e0b;
      padding: 14px 18px;
      border-radius: 10px;
      margin-bottom: 16px;
    }}
    .alert-title {{ font-weight: 700; color: #78350f; margin-bottom: 4px; font-size: 15px; }}
    .alert-body {{ color: #78350f; font-size: 14px; }}

    .table-wrap {{
      background: #fff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    thead tr {{ background: #f8fafc; }}
    th {{
      padding: 12px 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid #e2e8f0;
    }}
    th.right {{ text-align: right; }}
    th.center {{ text-align: center; }}
    td {{ padding: 14px 16px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }}

    .row-clickable {{ cursor: pointer; transition: background 0.12s; }}
    .row-clickable:hover {{ background: #f8fafc; }}
    .row-clickable.expanded {{ background: #f8fafc; }}
    .row-clickable.expanded .expand-icon {{ transform: rotate(90deg); }}

    .cell-name {{ font-weight: 600; }}
    .expand-icon {{
      display: inline-block;
      color: #94a3b8;
      font-size: 12px;
      margin-right: 6px;
      transition: transform 0.15s;
    }}
    .cell-price {{ text-align: right; font-family: ui-monospace, monospace; font-size: 13px; }}
    .cell-signal {{ text-align: center; font-weight: 700; }}
    .cell-signal .emoji {{ font-size: 16px; margin-right: 4px; }}
    .cell-buy {{ background: #ecfdf5; color: #15803d; }}
    .cell-sell {{ background: #fef2f2; color: #b91c1c; }}
    .cell-hold {{ background: #fefce8; color: #a16207; }}
    .cell-asof {{
      text-align: center;
      font-size: 12px;
      line-height: 1.3;
      color: #475569;
    }}
    .cell-asof .asof-date {{ font-weight: 600; }}
    .cell-asof .asof-ago {{ font-size: 10px; color: #94a3b8; margin-top: 1px; }}
    .cell-asof.stale {{ background: #fff7ed; }}
    .cell-asof.stale .asof-date {{ color: #c2410c; }}
    .cell-asof.stale .asof-ago {{ color: #ea580c; font-weight: 600; }}
    .cell-sparkline {{ width: 100px; padding: 8px; }}

    .badge {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 700;
      margin-left: 4px;
      vertical-align: middle;
    }}
    .badge-buy {{ background: #16a34a; color: #fff; }}
    .badge-sell {{ background: #dc2626; color: #fff; }}

    .row-detail td {{ padding: 0; background: #f8fafc; }}
    .detail-content {{ padding: 16px 20px; }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 14px;
    }}
    .detail-grid > div {{ display: flex; flex-direction: column; gap: 2px; }}
    .lbl {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
    .val {{ font-size: 14px; color: #334155; font-weight: 600; }}
    .val.mono {{ font-family: ui-monospace, monospace; font-weight: 500; }}

    .history-strip {{
      padding-top: 12px;
      border-top: 1px dashed #cbd5e1;
    }}
    .history-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px; }}
    .history-cells {{ display: flex; gap: 3px; flex-wrap: wrap; }}
    .hcell {{
      width: 22px; height: 22px;
      border-radius: 4px;
      display: flex; align-items: center; justify-content: center;
      font-size: 9px; font-weight: 700; color: #fff;
      cursor: default;
    }}
    .hcell-buy {{ background: #22c55e; }}
    .hcell-sell {{ background: #ef4444; }}
    .hcell-hold {{ background: #eab308; }}

    .row-error td {{ color: #94a3b8; font-style: italic; padding: 16px; }}

    .footer {{
      margin-top: 16px;
      padding: 16px;
      text-align: center;
      color: #94a3b8;
      font-size: 11px;
      line-height: 1.7;
    }}
    .footer a {{ color: #64748b; }}

    @media (max-width: 640px) {{
      body {{ padding: 10px; }}
      .header {{ padding: 18px; }}
      .header h1 {{ font-size: 18px; }}
      .stat-num {{ font-size: 24px; }}
      th, td {{ padding: 10px 8px; font-size: 13px; }}
      .cell-sparkline {{ display: none; }}
      th.col-spark {{ display: none; }}
      .detail-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>📊 CDC ActionZone Daily Report</h1>
      <div class="subtitle">Last updated: {date_str} </div>
      <div class="meta">Timeframe: 1D · EMA({FAST_EMA}/{SLOW_EMA}) · Logic by piriya33</div>
    </div>

    <div class="summary">
      <div class="stat buy"><div class="stat-num">{buys}</div><div class="stat-label">🟢 BUY</div></div>
      <div class="stat hold"><div class="stat-num">{holds}</div><div class="stat-label">🟡 HOLD</div></div>
      <div class="stat sell"><div class="stat-num">{sells}</div><div class="stat-label">🔴 SELL</div></div>
    </div>

    {alert_html}

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Asset</th>
            <th class="right">Close</th>
            <th class="center col-asof">As of</th>
            <th class="center">Signal</th>
            <th class="center col-spark">14D Trend</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>

    <div class="footer">
      <div>คลิกแถวเพื่อดูรายละเอียด · ประวัติย้อนหลัง 14 วัน</div>
      <div style="margin-top:6px;">
        Sources: Binance · Bitkub · Yahoo Finance · CDC ActionZone V3 by
        <a href="https://www.tradingview.com/u/piriya33/" target="_blank">piriya33</a>
      </div>
      <div style="margin-top:6px; color:#cbd5e1;">⚠️ เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน</div>
    </div>
  </div>

  <script>
    document.querySelectorAll('.row-clickable').forEach(row => {{
      row.addEventListener('click', () => {{
        const target = document.getElementById(row.dataset.target);
        if (!target) return;
        const isOpen = target.style.display !== 'none';
        target.style.display = isOpen ? 'none' : 'table-row';
        row.classList.toggle('expanded', !isOpen);
      }});
    }});
  </script>
</body>
</html>"""
    return html


def build_sparkline(history):
    """กราฟเส้นเล็กๆ 14 วัน"""
    if len(history) < 2:
        return ""
    closes = [h["close"] for h in history]
    lo, hi = min(closes), max(closes)
    rng = hi - lo if hi > lo else 1
    width, height, pad = 90, 28, 2
    pts = []
    for i, c in enumerate(closes):
        x = pad + (width - 2 * pad) * i / (len(closes) - 1)
        y = pad + (height - 2 * pad) * (1 - (c - lo) / rng)
        pts.append(f"{x:.1f},{y:.1f}")

    # สีตาม trend ล่าสุด
    last_sig = history[-1]["signal"]
    color = {"BUY": "#22c55e", "SELL": "#ef4444", "HOLD": "#eab308"}.get(last_sig, "#94a3b8")

    # จุดสุดท้าย
    last_x, last_y = pts[-1].split(",")

    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>'
            f'</svg>')


def build_history_cells(history):
    """แท่งสี่เหลี่ยมเล็กๆ แสดงสัญญาณรายวัน"""
    cells = []
    for h in history:
        cls = f"hcell-{h['signal'].lower()}"
        letter = h['signal'][0]   # B, S, H
        cells.append(f'<div class="hcell {cls}" title="{h["date"]}: {h["signal"]}">{letter}</div>')
    return "".join(cells)


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


if __name__ == "__main__":
    main()
