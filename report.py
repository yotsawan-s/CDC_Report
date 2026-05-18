"""
CDC ActionZone V3 — Daily Report orchestrator.

Compute CDC signals for each tracked asset, render to docs/index.html, and
dump docs/data.json for debugging. Everything else lives in submodules:

    config.py            — tunable values (ASSETS, EMA params, news config)
    data/                — fetch from binance / bitkub / yfinance
    signals/cdc.py       — CDC ActionZone V3 logic
    news/                — daily news fetch + summarize + retry state
    render/              — Jinja2 templates + builder

Usage:
    python report.py              # full run: signals + news + render
    python report.py --news-only   # reuse cached signal data, refresh news + rerender
                                   # (used by the retry workflow)
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from config import ASSETS, OUTPUT_DIR, NEWS_ENABLED
from data import fetch_data
from signals.cdc import calculate_signals_history
from render.builder import build_html


def compute_signals():
    results = []
    for name, source, symbol in ASSETS:
        print(f"  → {name} ({source}: {symbol})", flush=True)
        try:
            df = fetch_data(source, symbol)
            history = calculate_signals_history(df)
            results.append({"name": name, "history": history})
            last = history[-1]
            print(f"    {last['color_emoji']} {last['signal']} "
                  f"| close={last['close']:.4f} | zone={last['zone']}")
        except Exception as e:
            print(f"    ⚠️ {e}")
            results.append({"name": name, "error": str(e)})
    return results


def load_cached_signals():
    """For --news-only: reuse the most recent data.json so we don't refetch markets."""
    p = OUTPUT_DIR / "data.json"
    if not p.exists():
        print("  ⚠️ data.json missing — falling back to full signal compute")
        return compute_signals()
    return json.loads(p.read_text(encoding="utf-8")).get("assets", [])


def build_news_safely():
    """Never let news failures break the BUY/SELL/HOLD report."""
    if not NEWS_ENABLED:
        return {"items": [], "pending_count": 0}
    try:
        from news import build_daily_news
        return build_daily_news()
    except Exception as e:
        print(f"  ⚠️ news pipeline failed — skipping news section: {e}")
        return {"items": [], "pending_count": 0}


def write_outputs(results, news):
    html_path = OUTPUT_DIR / "index.html"
    html_path.write_text(build_html(results, news=news), encoding="utf-8")
    print(f"✅ Wrote {html_path}")

    json_path = OUTPUT_DIR / "data.json"
    json_path.write_text(
        json.dumps(
            {"updated": datetime.now(timezone.utc).isoformat(), "assets": results},
            default=str,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"✅ Wrote {json_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--news-only", action="store_true",
                        help="reuse cached signals, refresh news cache, rebuild HTML")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🔄 เริ่มรัน CDC Report — {datetime.now()}"
          + (" (--news-only)" if args.news_only else ""))

    results = load_cached_signals() if args.news_only else compute_signals()
    news    = build_news_safely()

    write_outputs(results, news)


if __name__ == "__main__":
    main()
