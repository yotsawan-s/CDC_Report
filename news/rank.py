"""
Score each RSS entry by how relevant it is to the tracked ASSETS.
Higher score = more likely to be picked into the daily 5.
"""

from config import NEWS_ASSET_ALIASES


def _matches(text, aliases):
    text_l = text.lower()
    return [a for a in aliases if a.lower() in text_l]


def score_and_tag(item):
    """Mutates `item` with `related_assets` + `score`. Returns score."""
    haystack = f"{item.get('title','')} {item.get('summary','')}"
    related = []
    score = 0
    for asset_key, aliases in NEWS_ASSET_ALIASES.items():
        hits = _matches(haystack, aliases)
        if hits:
            related.append(asset_key)
            score += len(hits)
    # Title hits weigh more
    title_l = item.get("title", "").lower()
    for aliases in NEWS_ASSET_ALIASES.values():
        for a in aliases:
            if a.lower() in title_l:
                score += 1
    item["related_assets"] = related
    item["score"] = score
    return score


def pick_top(items, n, diverse_sources=True):
    """
    Pick up to n items, preferring high score; if diverse_sources, cap
    to 2 per source so we don't end up with 5 CoinDesk stories.
    """
    for it in items:
        score_and_tag(it)
    items_sorted = sorted(items, key=lambda x: (-x["score"], x["published"]), reverse=False)
    items_sorted = sorted(items, key=lambda x: (-x["score"], -_iso_to_ts(x["published"])))

    picked, per_source = [], {}
    for it in items_sorted:
        if it["score"] <= 0:
            continue
        if diverse_sources and per_source.get(it["source"], 0) >= 2:
            continue
        picked.append(it)
        per_source[it["source"]] = per_source.get(it["source"], 0) + 1
        if len(picked) >= n:
            break

    # Fallback: if relevance filter left us short, fill from highest-scored remainder
    if len(picked) < n:
        chosen_ids = {p["id"] for p in picked}
        for it in items_sorted:
            if it["id"] in chosen_ids:
                continue
            picked.append(it)
            if len(picked) >= n:
                break
    return picked


def _iso_to_ts(iso):
    from datetime import datetime
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0
