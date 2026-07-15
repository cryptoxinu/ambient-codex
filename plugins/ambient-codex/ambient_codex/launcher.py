"""Pure launcher-ownership checks with injected filesystem reads."""

import re


def owned_link(path, *, is_link, read_link):
    """Return whether a symlink belongs to an Ambient Codex install."""
    if not is_link(path):
        return False
    try:
        target = read_link(path)
    except OSError:
        return False
    return "/ambient-codex/" in target.replace("\\", "/")


def owned_shim(path, *, read_text):
    """Return whether a Windows command shim belongs to Ambient Codex."""
    try:
        body = read_text(path).strip()
    except OSError:
        return False
    match = re.fullmatch(r'@(?:python|"[^"]+") "(.+)" %\*', body)
    return bool(match) and "/ambient-codex/" in match.group(1).replace("\\", "/")


__all__ = ("owned_link", "owned_shim")
