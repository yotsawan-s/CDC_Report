"""
Claude Sonnet 4.6 → Thai summary + analysis + key points + related assets.

Rate-limit strategy:
  - 429 with Retry-After <= INLINE_WAIT  → sleep and retry in-process
  - 429 with Retry-After >  INLINE_WAIT  → raise TokenLimitDeferred
  - Other transient errors                → exponential backoff (up to 3 tries)
"""

import json
import os
import time
from pathlib import Path

import anthropic

from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS, CLAUDE_INLINE_RETRY_WAIT
from .exceptions import TokenLimitDeferred, SummarizeError

_PROMPT_TEMPLATE = (Path(__file__).parent / "prompts" / "summarize_th.txt").read_text(encoding="utf-8")


def _client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SummarizeError("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key)


def _retry_after(err) -> int:
    """Pull Retry-After header (seconds) from a RateLimitError; default 60."""
    try:
        v = err.response.headers.get("retry-after")
        if v is None:
            v = err.response.headers.get("Retry-After")
        return int(float(v)) if v else 60
    except Exception:
        return 60


def _parse_json(text):
    text = text.strip()
    # Strip accidental code fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def summarize(item, body, asset_keys, client=None):
    """
    Returns dict with title_th / summary_th / analysis_th / key_points_th / related_assets.
    Raises TokenLimitDeferred or SummarizeError.
    """
    client = client or _client()
    prompt = _PROMPT_TEMPLATE.format(
        assets=", ".join(asset_keys),
        source=item["source"],
        title=item["title"],
        body=body,
    )

    last_err = None
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            return _parse_json(text)

        except anthropic.RateLimitError as e:
            wait = _retry_after(e)
            if wait > CLAUDE_INLINE_RETRY_WAIT:
                raise TokenLimitDeferred(retry_after_seconds=wait,
                                         message=f"rate-limit too long: {wait}s")
            print(f"    ⏳ rate-limit, waiting {wait}s (attempt {attempt+1}/3)")
            time.sleep(wait)
            last_err = e

        except anthropic.APIStatusError as e:
            # Some accounts get a 529/overloaded — treat like a soft defer
            if getattr(e, "status_code", None) in (529, 503):
                raise TokenLimitDeferred(retry_after_seconds=600,
                                         message=f"API overloaded: {e}")
            last_err = e
            time.sleep(2 ** attempt)

        except json.JSONDecodeError as e:
            last_err = e
            time.sleep(1)  # one quick retry, model occasionally adds prose

    raise SummarizeError(f"failed after retries: {last_err}")
