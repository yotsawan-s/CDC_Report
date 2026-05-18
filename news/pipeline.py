"""
build_daily_news() — orchestrates fetch → rank → body → summarize → cache.

Failure modes:
  - Anthropic key missing or any unexpected error → returns whatever cached
    summarized items we have for today (HTML can hide the section if empty).
  - Per-article TokenLimitDeferred → that article is stored as 'pending';
    the rest still get summarized; retry workflow finishes them later.
"""

from config import NEWS_COUNT, NEWS_ASSET_ALIASES
from .sources import fetch_all_rss
from .rank import pick_top
from .fetch import extract_body
from .summarize import summarize
from .exceptions import TokenLimitDeferred, SummarizeError, FetchError
from . import cache as cache_mod


def build_daily_news():
    state = cache_mod.load()
    cache_mod.trim(state)

    try:
        rss = fetch_all_rss()
    except Exception as e:
        print(f"  ⚠️ RSS fetch failed: {e}")
        cache_mod.save(state)
        return _render_payload(state)

    # Skip items we've already processed (cached) or that are currently pending
    known = cache_mod.existing_ids(state)
    fresh = [it for it in rss if it["id"] not in known]
    print(f"  📰 {len(fresh)} ใหม่จาก {len(rss)} ทั้งหมด")

    picked = pick_top(fresh, n=NEWS_COUNT, diverse_sources=True)
    print(f"  🎯 เลือก {len(picked)} ข่าวสำหรับสรุป")

    asset_keys = list(NEWS_ASSET_ALIASES.keys())

    try:
        client = _make_client()
    except SummarizeError as e:
        print(f"  ⚠️ ข้าม news section: {e}")
        cache_mod.save(state)
        return _render_payload(state)

    for item in picked:
        print(f"  → {item['source']}: {item['title'][:60]}")
        try:
            body = extract_body(item["url"], fallback=item.get("summary", ""))
        except FetchError as e:
            print(f"    ⚠️ {e}")
            continue

        try:
            result = summarize(item, body, asset_keys, client=client)
            cache_mod.mark_summarized(state, item, result)
            cache_mod.save(state)         # persist incrementally — survives crashes
            print(f"    ✅ {result.get('title_th', '')[:60]}")
        except TokenLimitDeferred as e:
            print(f"    🔄 deferred ({e.retry_after_seconds}s) — retry workflow will pick up")
            cache_mod.mark_pending(state, item, body, e.retry_after_seconds)
            cache_mod.save(state)
        except SummarizeError as e:
            print(f"    ⚠️ summarize failed: {e}")
            # don't cache — try again next run

    return _render_payload(state)


def resume_pending():
    """Entry point for the retry workflow — process any due-pending items."""
    state = cache_mod.load()
    cache_mod.trim(state)
    due = cache_mod.due_pending(state)
    if not due:
        print("  ✓ ไม่มี pending news ต้องประมวลผล")
        return _render_payload(state)

    print(f"  🔄 resume {len(due)} pending items")
    asset_keys = list(NEWS_ASSET_ALIASES.keys())
    try:
        client = _make_client()
    except SummarizeError as e:
        print(f"  ⚠️ {e}")
        return _render_payload(state)

    for item in due:
        body = item.get("body", "")
        print(f"  → {item['source']}: {item['title'][:60]}")
        try:
            result = summarize(item, body, asset_keys, client=client)
            cache_mod.mark_summarized(state, item, result)
            cache_mod.save(state)
            print(f"    ✅ resumed")
        except TokenLimitDeferred as e:
            print(f"    🔄 still deferred ({e.retry_after_seconds}s)")
            cache_mod.mark_pending(state, item, body, e.retry_after_seconds)
            cache_mod.save(state)
        except SummarizeError as e:
            print(f"    ⚠️ {e}")

    return _render_payload(state)


def _make_client():
    from .summarize import _client
    return _client()


def _render_payload(state):
    return {
        "items":         cache_mod.summarized_today(state),
        "pending_count": cache_mod.pending_count(state),
    }
