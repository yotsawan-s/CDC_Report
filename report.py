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
    ("Micron",          "yfinance", "MU"),
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
# สร้าง index.html — Premium Finance Dashboard
# ==============================================================================
def build_html(all_results):
    bkk_now = datetime.now(timezone(timedelta(hours=7)))
    date_str = bkk_now.strftime("%Y-%m-%d %H:%M")

    latest = [r["history"][-1] for r in all_results if r.get("history")]
    buys  = sum(1 for r in latest if r["signal"] == "BUY")
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

    rows = []
    for r in all_results:
        if r.get("error"):
            rows.append(f"""
            <tr class="row-error">
              <td>{r['name']}</td><td colspan="5">⚠️ {r['error']}</td>
            </tr>""")
            continue

        last    = r["history"][-1]
        sig     = last["signal"]
        css_sig = sig.lower()

        # % Change
        if len(r["history"]) >= 2:
            prev_close = r["history"][-2]["close"]
            pct = (last["close"] - prev_close) / prev_close * 100
            arrow   = "↑" if pct >= 0 else "↓"
            pct_str = f"{arrow} {abs(pct):.2f}%"
            pct_cls = "pct-up" if pct >= 0 else "pct-down"
        else:
            pct_str, pct_cls = "–", "pct-neutral"

        fresh_badge = ""
        if last.get("fresh_buy"):
            fresh_badge = '<span class="badge badge-buy">NEW</span>'
        elif last.get("fresh_sell"):
            fresh_badge = '<span class="badge badge-sell">NEW</span>'

        sparkline_svg = build_sparkline(r["history"])
        chart_id = r["name"].replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")

        date_short, ago, days_ago = format_date_short(last["date"])
        date_class = "stale" if days_ago > 1 else ""

        trend = last["trend"]
        trend_icon = "📈" if trend == "Bullish" else "📉" if trend == "Bearish" else "➡️"
        trend_cls  = "trend-bull" if trend == "Bullish" else "trend-bear" if trend == "Bearish" else "trend-side"

        rows.append(f"""
        <tr class="row-clickable" data-target="row-{chart_id}">
          <td class="cell-name">
            <span class="expand-icon">▸</span>{r['name']}
          </td>
          <td class="cell-price">{format_price(last['close'])}</td>
          <td class="cell-pct {pct_cls}">{pct_str}</td>
          <td class="cell-asof {date_class}">
            <div class="asof-date">{date_short}</div>
            <div class="asof-ago">{ago}</div>
          </td>
          <td class="cell-signal">
            <span class="sig-pill sig-pill-{css_sig}"><span class="sig-dot"></span>{sig}</span>
            {fresh_badge}
          </td>
          <td class="cell-sparkline">{sparkline_svg}</td>
        </tr>
        <tr id="row-{chart_id}" class="row-detail" style="display:none;">
          <td colspan="6">
            <div class="detail-card">
              <div class="detail-header-row">
                <span class="detail-asset-name">{r['name']}</span>
                <span class="sig-pill sig-pill-{css_sig}"><span class="sig-dot"></span>{sig}</span>
              </div>
              <div class="detail-divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="lbl">Trend</div>
                  <div class="val {trend_cls}">{trend_icon} {trend}</div>
                </div>
                <div class="detail-item">
                  <div class="lbl">EMA12 (Fast)</div>
                  <div class="val mono">{format_price(last['fast_ma'])}</div>
                </div>
                <div class="detail-item">
                  <div class="lbl">EMA26 (Slow)</div>
                  <div class="val mono">{format_price(last['slow_ma'])}</div>
                </div>
              </div>
              <div class="history-strip">
                <div class="history-label">{HISTORY_DAYS} วันย้อนหลัง</div>
                <div class="history-row">
                  <span class="hist-dir">← อดีต</span>
                  <div class="history-cells">{build_history_cells(r['history'])}</div>
                  <span class="hist-dir">ปัจจุบัน →</span>
                </div>
              </div>
            </div>
          </td>
        </tr>""")

    rows_html = "\n".join(rows)

    alert_html = ""
    if fresh:
        items = " · ".join(f"<strong>{n}</strong> {s}" for n, s in fresh)
        alert_html = f"""
        <div class="alert">
          <div class="alert-title">🚨 สัญญาณใหม่วันนี้</div>
          <div class="alert-body">{items}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="th" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="3600">
  <title>CDC ActionZone Daily Report</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📊</text></svg>">
  <style>
    /* ===== Design Tokens ===== */
    :root {{
      --bg-page:    #edf2f7;
      --bg-surface: #ffffff;
      --bg-thead:   #f0f4f9;
      --bg-alt:     #f7f9fc;
      --bg-hover:   #ebf3ff;
      --bg-detail:  #f0f4f9;
      --text-1:  #0f172a;
      --text-2:  #334155;
      --text-3:  #64748b;
      --text-th: #475569;
      --border-strong: #c2cedd;
      --border-soft:   #dde4ef;
      --shadow-card: 0 2px 8px rgba(15,23,42,0.08), 0 1px 3px rgba(15,23,42,0.05);
      --shadow-lg:   0 8px 32px rgba(15,23,42,0.10), 0 2px 8px rgba(15,23,42,0.06);
      --accent: #2563eb;
      --buy-bg:#f0fdf4;  --buy-text:#166534;  --buy-border:#86efac;  --buy-dot:#22c55e;
      --sell-bg:#fff1f2; --sell-text:#9f1239; --sell-border:#fda4af; --sell-dot:#f43f5e;
      --hold-bg:#fffbeb; --hold-text:#92400e; --hold-border:#fcd34d; --hold-dot:#f59e0b;
      --pct-up:#16a34a;  --pct-dn:#dc2626;
      --stale-date:#b45309; --stale-ago:#d97706;
      --btn-bg:#e2e8f0; --btn-text:#334155; --btn-border:#cbd5e1;
      --hist-dir:#94a3b8;
    }}
    [data-theme="dark"] {{
      --bg-page:    #080e1a;
      --bg-surface: #0f1e32;
      --bg-thead:   #0b1829;
      --bg-alt:     #0d1b2e;
      --bg-hover:   #0f2340;
      --bg-detail:  #0b1829;
      --text-1:  #e2e8f0;
      --text-2:  #94a3b8;
      --text-3:  #475569;
      --text-th: #64748b;
      --border-strong: #1e3a58;
      --border-soft:   #162d48;
      --shadow-card: 0 2px 8px rgba(0,0,0,0.35);
      --shadow-lg:   0 8px 32px rgba(0,0,0,0.45);
      --accent: #3b82f6;
      --buy-bg:#052e16;  --buy-text:#4ade80;  --buy-border:#166534;  --buy-dot:#4ade80;
      --sell-bg:#3b0a0a; --sell-text:#f87171; --sell-border:#7f1d1d; --sell-dot:#f87171;
      --hold-bg:#3d2000; --hold-text:#fbbf24; --hold-border:#78350f; --hold-dot:#fbbf24;
      --pct-up:#4ade80;  --pct-dn:#f87171;
      --stale-date:#fbbf24; --stale-ago:#f59e0b;
      --btn-bg:#162d48; --btn-text:#94a3b8; --btn-border:#1e3a58;
      --hist-dir:#334155;
    }}

    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
      font-family: -apple-system,"Segoe UI","Helvetica Neue","Sukhumvit Set",sans-serif;
      background: var(--bg-page);
      color: var(--text-1);
      min-height: 100vh;
      padding: 20px 16px;
      line-height: 1.5;
      transition: background .3s, color .3s;
    }}
    .wrap {{ max-width: 940px; margin: 0 auto; }}

    /* ── Header ── */
    .header {{
      background: var(--bg-surface);
      padding: 22px 28px;
      border-radius: 16px;
      box-shadow: var(--shadow-lg);
      margin-bottom: 16px;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      border-top: 4px solid var(--accent);
    }}
    .header-left {{ flex:1; min-width:0; }}
    .header h1 {{
      font-size: 21px;
      font-weight: 800;
      color: var(--text-1);
      letter-spacing: -.3px;
      margin-bottom: 5px;
    }}
    .header .subtitle {{ color: var(--text-2); font-size: 13px; }}
    .header .meta {{
      color: var(--text-3);
      font-size: 11px;
      margin-top: 3px;
      font-family: ui-monospace,monospace;
      letter-spacing: .3px;
    }}
    .theme-btn {{
      flex-shrink: 0;
      padding: 8px 16px;
      border-radius: 8px;
      border: 1px solid var(--btn-border);
      background: var(--btn-bg);
      color: var(--btn-text);
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      transition: all .2s;
      align-self: flex-start;
    }}
    .theme-btn:hover {{ opacity:.8; transform:translateY(-1px); }}

    /* ── Summary Cards ── */
    .summary {{
      display: grid;
      grid-template-columns: repeat(3,1fr);
      gap: 10px;
      margin-bottom: 16px;
    }}
    .stat {{
      background: var(--bg-surface);
      padding: 18px 16px 16px;
      border-radius: 14px;
      text-align: center;
      box-shadow: var(--shadow-card);
      position: relative;
      overflow: hidden;
    }}
    .stat::after {{
      content: '';
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 3px;
    }}
    .stat.buy::after  {{ background: #22c55e; }}
    .stat.hold::after {{ background: #f59e0b; }}
    .stat.sell::after {{ background: #f43f5e; }}
    .stat-num {{ font-size: 34px; font-weight: 800; line-height:1; margin-bottom:5px; }}
    .stat-label {{
      font-size: 11px;
      color: var(--text-3);
      text-transform: uppercase;
      letter-spacing: 1px;
      font-weight: 700;
    }}
    .stat.buy .stat-num  {{ color:#16a34a; }}
    .stat.hold .stat-num {{ color:#d97706; }}
    .stat.sell .stat-num {{ color:#e11d48; }}

    /* ── Alert ── */
    .alert {{
      background: linear-gradient(135deg,#fffbf0,#fef3c7);
      border-left: 4px solid #f59e0b;
      padding: 14px 20px;
      border-radius: 12px;
      margin-bottom: 16px;
      box-shadow: var(--shadow-card);
    }}
    .alert-title {{ font-weight:700; color:#78350f; margin-bottom:3px; font-size:14px; }}
    .alert-body  {{ color:#78350f; font-size:13px; }}

    /* ── Table ── */
    .table-wrap {{
      background: var(--bg-surface);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: var(--shadow-lg);
      border: 1px solid var(--border-soft);
    }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    thead tr {{ background: var(--bg-thead); }}
    th {{
      padding: 13px 16px;
      text-align: left;
      font-size: 11px;
      font-weight: 700;
      color: var(--text-th);
      text-transform: uppercase;
      letter-spacing: .8px;
      border-bottom: 2px solid var(--border-strong);
    }}
    th.right  {{ text-align:right; }}
    th.center {{ text-align:center; }}

    /* Row separators — clearly visible */
    tbody .row-clickable {{
      border-bottom: 1.5px solid var(--border-strong);
      border-left: 3px solid transparent;
      cursor: pointer;
      transition: background .15s, border-left-color .15s;
    }}
    tbody .row-clickable.row-stripe {{ background: var(--bg-alt); }}
    tbody .row-clickable:hover {{
      background: var(--bg-hover) !important;
      border-left-color: var(--accent);
    }}
    tbody .row-clickable.expanded {{
      background: var(--bg-hover) !important;
      border-left-color: var(--accent);
    }}
    tbody .row-clickable.expanded .expand-icon {{ transform:rotate(90deg); }}

    td {{
      padding: 13px 16px;
      vertical-align: middle;
      color: var(--text-1);
    }}
    .cell-name {{ font-weight:700; font-size:14px; }}
    .expand-icon {{
      display: inline-block;
      color: var(--text-3);
      font-size: 11px;
      margin-right: 8px;
      transition: transform .2s;
    }}
    .cell-price {{
      text-align: right;
      font-family: ui-monospace,monospace;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-2);
    }}

    /* % Change */
    .cell-pct {{
      text-align: right;
      font-family: ui-monospace,monospace;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .pct-up      {{ color:var(--pct-up); }}
    .pct-down    {{ color:var(--pct-dn); }}
    .pct-neutral {{ color:var(--text-3); }}

    /* Date */
    .cell-asof {{ text-align:center; font-size:12px; line-height:1.4; }}
    .cell-asof .asof-date {{ font-weight:600; color:var(--text-2); }}
    .cell-asof .asof-ago  {{ font-size:10px; color:var(--text-3); margin-top:1px; }}
    .cell-asof.stale .asof-date {{ color:var(--stale-date); }}
    .cell-asof.stale .asof-ago  {{ color:var(--stale-ago); font-weight:600; }}

    /* Signal pill */
    .cell-signal {{ text-align:center; }}
    .sig-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 13px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .8px;
      text-transform: uppercase;
    }}
    .sig-dot {{
      width: 7px; height: 7px;
      border-radius: 50%;
      flex-shrink: 0;
    }}
    .sig-pill-buy  {{ background:var(--buy-bg);  color:var(--buy-text);  border:1px solid var(--buy-border);  }}
    .sig-pill-sell {{ background:var(--sell-bg); color:var(--sell-text); border:1px solid var(--sell-border); }}
    .sig-pill-hold {{ background:var(--hold-bg); color:var(--hold-text); border:1px solid var(--hold-border); }}
    .sig-pill-buy  .sig-dot {{ background:var(--buy-dot);  }}
    .sig-pill-sell .sig-dot {{ background:var(--sell-dot); }}
    .sig-pill-hold .sig-dot {{ background:var(--hold-dot); }}

    .cell-sparkline {{ width:115px; padding:8px 12px; }}

    .badge {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 9px;
      font-weight: 800;
      margin-left: 5px;
      vertical-align: middle;
      letter-spacing: .5px;
    }}
    .badge-buy  {{ background:#166534; color:#fff; }}
    .badge-sell {{ background:#9f1239; color:#fff; }}

    /* ── Detail Row ── */
    .row-detail td {{
      padding: 4px 16px 16px;
      border-bottom: 2px solid var(--border-strong);
      background: var(--bg-detail);
    }}
    .detail-card {{
      background: var(--bg-surface);
      border-radius: 12px;
      border: 1px solid var(--border-soft);
      box-shadow: var(--shadow-card);
      overflow: hidden;
    }}
    .detail-header-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 16px 20px 12px;
    }}
    .detail-asset-name {{
      font-size: 16px;
      font-weight: 800;
      color: var(--text-1);
      letter-spacing: -.3px;
    }}
    .detail-divider {{
      height: 1px;
      background: var(--border-soft);
      margin: 0 0 14px;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(3,1fr);
      border-top: 1px solid var(--border-soft);
      margin: 0 20px 16px;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid var(--border-soft);
    }}
    .detail-item {{
      padding: 14px 18px;
      border-right: 1px solid var(--border-soft);
      background: var(--bg-detail);
    }}
    .detail-item:last-child {{ border-right:none; }}
    .lbl {{
      font-size: 10px;
      color: var(--text-3);
      text-transform: uppercase;
      letter-spacing: .8px;
      font-weight: 700;
      margin-bottom: 6px;
    }}
    .val {{ font-size:15px; color:var(--text-2); font-weight:700; }}
    .val.mono {{ font-family:ui-monospace,monospace; font-weight:600; font-size:14px; }}
    .trend-bull {{ color:var(--buy-dot);  }}
    .trend-bear {{ color:var(--sell-dot); }}
    .trend-side {{ color:var(--text-3);   }}

    /* ── History Strip ── */
    .history-strip {{
      padding: 14px 20px 18px;
      border-top: 1px dashed var(--border-soft);
    }}
    .history-label {{
      font-size: 10px;
      color: var(--text-3);
      text-transform: uppercase;
      letter-spacing: .8px;
      font-weight: 700;
      margin-bottom: 8px;
    }}
    .history-row {{ display:flex; align-items:center; gap:8px; }}
    .hist-dir {{
      font-size: 10px;
      color: var(--hist-dir);
      white-space: nowrap;
      font-style: italic;
      flex-shrink: 0;
    }}
    .history-cells {{ display:flex; gap:3px; flex-wrap:wrap; flex:1; }}
    .hcell {{
      width: 26px; height: 26px;
      border-radius: 6px;
      display: flex; align-items:center; justify-content:center;
      font-size: 9px; font-weight: 800; color: rgba(255,255,255,.95);
      cursor: default;
    }}
    .hcell-buy  {{ background:#22c55e; }}
    .hcell-sell {{ background:#f43f5e; }}
    .hcell-hold {{ background:#f59e0b; }}

    .row-error td {{
      color: var(--text-3);
      font-style: italic;
      padding: 16px;
      border-bottom: 1.5px solid var(--border-strong);
    }}

    /* ── Footer ── */
    .footer {{
      margin-top: 18px;
      padding: 16px;
      text-align: center;
      color: var(--text-3);
      font-size: 11px;
      line-height: 1.8;
    }}
    .footer a {{ color:var(--text-2); text-decoration:none; }}
    .footer a:hover {{ text-decoration:underline; }}

    @media (max-width:640px) {{
      body {{ padding:12px 10px; }}
      .header {{ padding:16px; flex-direction:column; gap:10px; }}
      .header h1 {{ font-size:18px; }}
      .theme-btn {{ align-self:flex-end; }}
      .stat-num {{ font-size:28px; }}
      th, td {{ padding:11px 10px; font-size:13px; }}
      .cell-sparkline, th.col-spark {{ display:none; }}
      .cell-pct, th.col-pct {{ display:none; }}
      .detail-grid {{ grid-template-columns:1fr 1fr; }}
      .detail-item:nth-child(2) {{ border-right:none; }}
      .detail-item:nth-child(3) {{
        grid-column:1/-1;
        border-top:1px solid var(--border-soft);
        border-right:none;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="header-left">
        <h1>📊 CDC ActionZone Daily Report</h1>
        <div class="subtitle">Last updated: {date_str}</div>
        <div class="meta">Timeframe: 1D · EMA({FAST_EMA}/{SLOW_EMA}) · Logic by piriya33</div>
      </div>
      <button class="theme-btn" id="theme-toggle">🌙 Dark</button>
    </div>

    <div class="summary">
      <div class="stat buy" ><div class="stat-num">{buys}</div> <div class="stat-label">🟢 BUY</div></div>
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
            <th class="right col-pct">% Change</th>
            <th class="center">As of</th>
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
      <div style="margin-top:4px;">
        Sources: Binance · Bitkub · Yahoo Finance · CDC ActionZone V3 by
        <a href="https://www.tradingview.com/u/piriya33/" target="_blank">piriya33</a>
      </div>
      <div style="margin-top:4px;">⚠️ เพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุน</div>
    </div>
  </div>

  <script>
    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle');
    const htmlEl   = document.documentElement;
    const saved    = localStorage.getItem('cdc-theme') || 'light';
    htmlEl.dataset.theme = saved;
    themeBtn.textContent = saved === 'dark' ? '☀️ Light' : '🌙 Dark';
    themeBtn.addEventListener('click', () => {{
      const next = htmlEl.dataset.theme === 'dark' ? 'light' : 'dark';
      htmlEl.dataset.theme = next;
      localStorage.setItem('cdc-theme', next);
      themeBtn.textContent = next === 'dark' ? '☀️ Light' : '🌙 Dark';
    }});

    // Zebra stripe — ทำให้แยกแถวชัดขึ้นอีก
    document.querySelectorAll('tbody .row-clickable').forEach((row, i) => {{
      if (i % 2 === 1) row.classList.add('row-stripe');
    }});

    // Row expand
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
