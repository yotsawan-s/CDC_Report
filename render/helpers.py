"""
Presentation helpers — pure, no Jinja knowledge.
Called from templates via the global filters/funcs registered in builder.py.
"""

from datetime import datetime, timezone, timedelta


def format_price(p):
    if p >= 1000:
        return f"{p:,.2f}"
    if p >= 1:
        return f"{p:,.4f}"
    return f"{p:.8f}"


def format_date_short(date_str):
    """'2026-04-25' → ('25 Apr', 'today' | '1d ago' | 'Nd ago', days_ago_int)."""
    try:
        dt    = datetime.strptime(date_str, "%Y-%m-%d")
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
    """SVG sparkline of the last N closes, coloured by latest signal."""
    if len(history) < 2:
        return ""
    closes = [h["close"] for h in history]
    lo, hi = min(closes), max(closes)
    rng    = hi - lo if hi > lo else 1
    width, height, pad = 90, 28, 2
    pts = []
    for i, c in enumerate(closes):
        x = pad + (width  - 2 * pad) * i / (len(closes) - 1)
        y = pad + (height - 2 * pad) * (1 - (c - lo) / rng)
        pts.append(f"{x:.1f},{y:.1f}")

    last_sig = history[-1]["signal"]
    color = {"BUY": "#22c55e", "SELL": "#ef4444", "HOLD": "#eab308"}.get(last_sig, "#94a3b8")
    last_x, last_y = pts[-1].split(",")
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="2.5" fill="{color}"/>'
            f'</svg>')


def build_history_cells(history):
    """Small coloured squares — one per day, signal-coloured."""
    cells = []
    for h in history:
        cls    = f"hcell-{h['signal'].lower()}"
        letter = h["signal"][0]  # B / S / H
        cells.append(
            f'<div class="hcell {cls}" title="{h["date"]}: {h["signal"]}">{letter}</div>'
        )
    return "".join(cells)


def asset_chart_id(name):
    """Make a DOM-safe id from an asset name like 'XAU/USD (Gold)'."""
    return name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")


def pct_change(history):
    """Return (text, css_class) for the last-vs-previous close % change."""
    if len(history) < 2:
        return "–", "pct-neutral"
    prev_close = history[-2]["close"]
    last_close = history[-1]["close"]
    pct        = (last_close - prev_close) / prev_close * 100
    arrow      = "↑" if pct >= 0 else "↓"
    return f"{arrow} {abs(pct):.2f}%", ("pct-up" if pct >= 0 else "pct-down")
