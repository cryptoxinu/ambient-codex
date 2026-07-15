"""Pure final-request construction for code generation."""


def final_messages(task, context):
    """Return a fresh generation request with an optional context boundary."""
    user_content = task if not context else f"{task}\n\nContext files:\n\n{context}"
    return [
        {
            "role": "system",
            "content": (
                "You are a senior software engineer. Produce complete, correct, "
                "production-quality code. Include brief usage notes. No placeholders."
            ),
        },
        {"role": "user", "content": user_content},
    ]


def clamp_context(context, *, task, single_shot_chars):
    """Return a final-context value that leaves room for task and prompt text."""
    room = max(1_000, single_shot_chars - len(task) - 500)
    return (context if len(context) <= room
            else context[:room] + "\n[ambient: context truncated to fit]")


__all__ = ("final_messages", "clamp_context")
