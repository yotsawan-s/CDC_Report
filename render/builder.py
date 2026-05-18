"""
Compose the final single-file index.html.

CSS and JS are inlined at build time so GitHub Pages serves one file —
no extra requests, easy to bookmark/share.
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import FAST_EMA, SLOW_EMA, HISTORY_DAYS
from render import helpers

_TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=False,
    lstrip_blocks=False,
)

# Helpers exposed inside templates
_env.globals.update(
    format_price=helpers.format_price,
    format_date_short=helpers.format_date_short,
    build_sparkline=helpers.build_sparkline,
    build_history_cells=helpers.build_history_cells,
    asset_chart_id=helpers.asset_chart_id,
    pct_change=helpers.pct_change,
)


def _aggregate(all_results):
    """Compute summary counts + fresh-signal list."""
    latest = [r["history"][-1] for r in all_results if r.get("history")]
    summary = {
        "buys":  sum(1 for r in latest if r["signal"] == "BUY"),
        "sells": sum(1 for r in latest if r["signal"] == "SELL"),
        "holds": sum(1 for r in latest if r["signal"] == "HOLD"),
    }
    fresh = []
    for r in all_results:
        if not r.get("history"):
            continue
        last = r["history"][-1]
        if last.get("fresh_buy"):
            fresh.append((r["name"], "BUY"))
        elif last.get("fresh_sell"):
            fresh.append((r["name"], "SELL"))
    return summary, fresh


def build_html(all_results, news=None):
    bkk_now  = datetime.now(timezone(timedelta(hours=7)))
    date_str = bkk_now.strftime("%Y-%m-%d %H:%M")
    summary, fresh = _aggregate(all_results)

    inline_css = (_TEMPLATE_DIR / "styles.css").read_text(encoding="utf-8")
    inline_js  = (_TEMPLATE_DIR / "app.js").read_text(encoding="utf-8")

    # Normalise — accept None, list, or {items, pending_count} dict
    if news is None:
        news = {"items": [], "pending_count": 0}
    elif isinstance(news, list):
        news = {"items": news, "pending_count": 0}

    template = _env.get_template("layout.html")
    return template.render(
        date_str=date_str,
        fast_ema=FAST_EMA,
        slow_ema=SLOW_EMA,
        history_days=HISTORY_DAYS,
        summary=summary,
        fresh_signals=fresh,
        assets=all_results,
        news=news,
        inline_css=inline_css,
        inline_js=inline_js,
    )
