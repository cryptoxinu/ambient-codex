"""Pure planning helpers for the map-reduce orchestration facade."""


def map_note(map_system, code_map, chunk_count, index_marker):
    """Build the shared per-chunk system prompt before index substitution."""
    return (
        map_system
        + (f"\n\n{code_map}" if code_map else "")
        + f"\n\n(You are seeing chunk {index_marker} of {chunk_count} of a "
        "larger input. File boundaries may be split across chunks — flag "
        "suspected split artifacts as such instead of guessing.)"
    )


def group_for_budget(texts, budget):
    """Keep input order while forming maximal groups within a char budget.

    A single oversized item remains its own group: the caller must preserve it
    rather than drop paid-for model output just because no further merge is
    possible.
    """
    groups, current, current_length = [], [], 0
    for text in texts:
        if current and current_length + len(text) > budget:
            groups.append(current)
            current, current_length = [], 0
        current.append(text)
        current_length += len(text)
    if current:
        groups.append(current)
    return groups


__all__ = ("map_note", "group_for_budget")
