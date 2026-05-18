"""
CLI entry for the retry workflow:

    python -m news.resume

Processes any pending items whose retry_after is in the past.
"""

from .pipeline import resume_pending
from . import cache as cache_mod


def has_due_pending() -> bool:
    state = cache_mod.load()
    return bool(cache_mod.due_pending(state))


def main():
    payload = resume_pending()
    print(f"📰 summarized today: {len(payload['items'])} | "
          f"pending: {payload['pending_count']}")


if __name__ == "__main__":
    main()
