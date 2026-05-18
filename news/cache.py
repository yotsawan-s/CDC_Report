"""
Persistent state for news items — docs/news.json.

Items have a `status` field that turns the cache into a small state machine:

  "summarized" — fully processed, will render in the HTML
  "pending"    — body fetched, Claude deferred; retry workflow picks up
                 once datetime.utcnow() >= retry_after

Cache is trimmed to NEWS_CACHE_DAYS to stay small.
"""

import json
from datetime import datetime, timezone, timedelta

from config import OUTPUT_DIR, NEWS_CACHE_DAYS

CACHE_PATH = OUTPUT_DIR / "news.json"


def _now():
    return datetime.now(timezone.utc)


def load():
    if not CACHE_PATH.exists():
        return {"updated": _now().isoformat(), "items": []}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"updated": _now().isoformat(), "items": []}


def save(state):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state["updated"] = _now().isoformat()
    CACHE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def trim(state, days=NEWS_CACHE_DAYS):
    cutoff = _now() - timedelta(days=days)
    state["items"] = [
        it for it in state["items"]
        if _parse_iso(it.get("published") or it.get("fetched_at") or "") >= cutoff
    ]
    return state


def _parse_iso(s):
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return _now() - timedelta(days=365)


def existing_ids(state):
    return {it["id"] for it in state["items"]}


def mark_pending(state, item, body, retry_after_seconds):
    """Insert/update a pending entry."""
    retry_at = (_now() + timedelta(seconds=retry_after_seconds)).isoformat()
    record = {
        **{k: item[k] for k in ("id", "url", "source", "title", "published") if k in item},
        "related_assets": item.get("related_assets", []),
        "body":           body,
        "status":         "pending",
        "retry_after":    retry_at,
        "attempts":       _attempt_count(state, item["id"]) + 1,
        "fetched_at":     _now().isoformat(),
    }
    _upsert(state, record)


def mark_summarized(state, item, summary_dict):
    record = {
        **{k: item[k] for k in ("id", "url", "source", "title", "published") if k in item},
        **summary_dict,                  # title_th, summary_th, analysis_th, key_points_th, related_assets
        "status":         "summarized",
        "summarized_at":  _now().isoformat(),
    }
    _upsert(state, record)


def _upsert(state, record):
    for i, it in enumerate(state["items"]):
        if it["id"] == record["id"]:
            state["items"][i] = record
            return
    state["items"].append(record)


def _attempt_count(state, item_id):
    for it in state["items"]:
        if it["id"] == item_id:
            return it.get("attempts", 0)
    return 0


def due_pending(state):
    """Pending items whose retry_after is in the past — ready to retry."""
    now_iso = _now().isoformat()
    return [it for it in state["items"]
            if it.get("status") == "pending"
            and it.get("retry_after", "9999") <= now_iso]


def summarized_today(state, tz_offset_hours=7):
    """Items summarized within the last 24h, sorted newest-first."""
    cutoff = _now() - timedelta(hours=24)
    out = [it for it in state["items"]
           if it.get("status") == "summarized"
           and _parse_iso(it.get("summarized_at", "")) >= cutoff]
    out.sort(key=lambda x: x.get("summarized_at", ""), reverse=True)
    return out


def pending_count(state):
    return sum(1 for it in state["items"] if it.get("status") == "pending")
