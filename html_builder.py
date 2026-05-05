import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# =========================
# CONFIG
# =========================
FAST_EMA = 12
SLOW_EMA = 26
HISTORY_DAYS = 14


# =========================
# Helper functions
# =========================
def format_price(p):
    if p >= 1000:
        return f"{p:,.2f}"
    elif p >= 1:
        return f"{p:,.4f}"
    else:
        return f"{p:.8f}"


def format_date_short(date_str):
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


def build_sparkline(history):
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

    last_sig = history[-1]["signal"]
    color = {"BUY": "#22c55e", "SELL": "#ef4444", "HOLD": "#eab308"}.get(last_sig, "#94a3b8")

    last_x, last_y = pts[-1].split(",")

    return (
        f'<svg width="{width}" height="{height}">'
        f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>'
        f'</svg>'
    )


def build_history_cells(history):
    cells = []
    for h in history:
        cls = f"hcell-{h['signal'].lower()}"
        letter = h['signal'][0]
        cells.append(f'<div class="hcell {cls}" title="{h["date"]}: {h["signal"]}">{letter}</div>')
    return "".join(cells)


# =========================
# MAIN FUNCTION
# =========================
def build_html(all_results):

    bkk_now = datetime.now(timezone(timedelta(hours=7)))
    date_str = bkk_now.strftime("%Y-%m-%d %H:%M")

    # === summary ===
    latest = [r["history"][-1] for r in all_results if r.get("history")]
    buys = sum(1 for r in latest if r["signal"] == "BUY")
    sells = sum(1 for r in latest if r["signal"] == "SELL")
    holds = sum(1 for r in latest if r["signal"] == "HOLD")

    # === fresh signal ===
    fresh = []
    for r in all_results:
        if not r.get("history"):
            continue
        last = r["history"][-1]
        if last.get("fresh_buy"):
            fresh.append((r["name"], "BUY"))
        elif last.get("fresh_sell"):
            fresh.append((r["name"], "SELL"))

    # =========================
    # BUILD ROWS
    # =========================
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

        sparkline_svg = build_sparkline(r["history"])

        chart_id = (
            r["name"]
            .replace("/", "_")
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
        )

        date_short, ago, days_ago = format_date_short(last["date"])
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

    # =========================
    # ALERT
    # =========================
    alert_html = ""
    if fresh:
        items = " · ".join(f"<strong>{n}</strong> {s}" for n, s in fresh)
        alert_html = f"""
        <div class="alert">
          <div class="alert-title">🚨 สัญญาณใหม่วันนี้</div>
          <div class="alert-body">{items}</div>
        </div>"""

    # =========================
    # LOAD TEMPLATE
    # =========================
    template_path = Path("CDC_Report/template.html")
    template = template_path.read_text(encoding="utf-8")

    # =========================
    # INJECT DATA
    # =========================
    html = (
        template
        .replace("{{DATE}}", date_str)
        .replace("{{BUYS}}", str(buys))
        .replace("{{HOLDS}}", str(holds))
        .replace("{{SELLS}}", str(sells))
        .replace("{{ALERT}}", alert_html)
        .replace("{{ROWS}}", rows_html)
    )

    return html


# =========================
# SAVE FUNCTION
# =========================
def build_and_save(all_results):
    html = build_html(all_results)

    output_path = Path("docs/index.html")
    output_path.write_text(html, encoding="utf-8")

    print(f"✅ HTML generated: {output_path.resolve()}")