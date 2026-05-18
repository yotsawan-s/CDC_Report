"""Typed errors so callers can branch on failure mode without parsing strings."""


class FetchError(Exception):
    """Could not retrieve the article body — network/paywall/etc."""


class TokenLimitDeferred(Exception):
    """
    Anthropic rate-limited us harder than we can wait inline.
    Caller should persist the item with status='pending' and let the
    scheduled retry workflow pick it up later.
    """

    def __init__(self, retry_after_seconds: int, message: str = ""):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message or f"deferred for {retry_after_seconds}s")


class SummarizeError(Exception):
    """Non-rate-limit Claude failure — bad JSON, server error, etc."""
