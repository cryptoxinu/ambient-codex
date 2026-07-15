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


__all__ = ("final_messages",)
