"""
Extract clean article bodies. Uses r.jina.ai — a free proxy that strips
boilerplate and returns Markdown, also helps with light paywalls.

Falls back to the RSS <summary> if the proxy fails.
"""

import requests

from .exceptions import FetchError

_JINA_PREFIX = "https://r.jina.ai/"
_TIMEOUT = 30
_MAX_BODY_CHARS = 12_000   # cap input tokens to Claude


def extract_body(url, fallback=""):
    """Return clean article text. Never raises — falls back gracefully."""
    try:
        r = requests.get(
            _JINA_PREFIX + url,
            headers={"Accept": "text/plain", "User-Agent": "cdc-report/1.0"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200 and len(r.text) > 200:
            return r.text[:_MAX_BODY_CHARS]
    except Exception as e:
        print(f"    ⚠️ extract_body failed: {e}")

    if fallback and len(fallback) > 100:
        return fallback[:_MAX_BODY_CHARS]
    raise FetchError(f"could not extract body for {url}")
