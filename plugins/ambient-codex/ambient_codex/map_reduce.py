"""Pure planning helpers for the map-reduce orchestration facade."""

import re


def files_block(chunks):
    """Render labeled input files with explicit, model-visible boundaries."""
    return "\n\n".join(f"===== FILE: {path} =====\n{text}"
                       for path, text in chunks)


def chunk_ranges(chunk_text):
    """Return packed-block coverage labels from a chunk body."""
    return [match.group(1).strip()
            for match in re.finditer(r"===== (.+?) =====", chunk_text or "")]


def code_map_budget(single_shot_chars, default_budget, maximum_budget):
    """Scale a repository-map budget to the model's single-shot capacity."""
    if not single_shot_chars or single_shot_chars <= 0:
        return default_budget
    return max(512, min(single_shot_chars // 10, maximum_budget))


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


__all__ = ("files_block", "chunk_ranges", "code_map_budget", "map_note",
           "group_for_budget")
