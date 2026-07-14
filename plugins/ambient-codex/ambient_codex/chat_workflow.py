"""Pure state policies used by the interactive chat workflow."""


def trim_history(history, budget_chars):
    """Return a new recent-first-fitting history without mutating the caller."""
    kept = list(history)

    def size(messages):
        return sum(len(message.get("content") or "") for message in messages)

    while len(kept) > 2 and size(kept) > budget_chars:
        kept = kept[2:]
    while len(kept) > 1 and size(kept) > budget_chars:
        kept = kept[1:]
    return kept


__all__ = ("trim_history",)
