"""Pull article metadata from RSS feeds configured in config.NEWS_SOURCES."""

import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha1

import feedparser

from config import NEWS_SOURCES


def _entry_published(entry):
    for k in ("published_parsed", "updated_parsed"):
        t = entry.get(k)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    for k in ("published", "updated"):
        s = entry.get(k)
        if s:
            try:
                dt = parsedate_to_datetime(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _make_id(url):
    return sha1(url.encode("utf-8")).hexdigest()[:16]


def fetch_all_rss(max_per_source=15):
    """Return list of {id, url, source, title, summary, published}."""
    items = []
    for src in NEWS_SOURCES:
        print(f"  📡 RSS {src['name']}", flush=True)
        try:
            feed = feedparser.parse(src["rss"])
        except Exception as e:
            print(f"    ⚠️ {e}")
            continue
        for entry in feed.entries[:max_per_source]:
            url = entry.get("link")
            if not url:
                continue
            items.append({
                "id":        _make_id(url),
                "url":       url,
                "source":    src["name"],
                "title":     entry.get("title", "").strip(),
                "summary":   entry.get("summary", "").strip(),
                "published": _entry_published(entry).isoformat(),
            })
    print(f"  📡 {len(items)} entries จาก {len(NEWS_SOURCES)} แหล่ง")
    return items
