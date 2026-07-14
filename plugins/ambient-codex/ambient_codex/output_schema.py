"""Public JSON projection rules for Ambient CLI output."""


_PUBLIC_USAGE_KEYS = frozenset((
    "prompt_tokens", "completion_tokens", "total_tokens",
    "reasoning_tokens", "_estimated",
))


def public_usage(usage):
    """Return a fresh token-only usage mapping safe for public JSON output."""
    if not isinstance(usage, dict):
        return usage
    return {key: usage[key] for key in usage if key in _PUBLIC_USAGE_KEYS}


__all__ = ("public_usage",)
