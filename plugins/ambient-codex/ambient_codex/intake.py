"""Bounded text-file intake with no import-time external effects."""

import os
import stat


def _validate_char_cap(char_cap):
    if isinstance(char_cap, bool) or not isinstance(char_cap, int) or char_cap <= 0:
        raise ValueError("character ceiling must be a positive integer")


def _regular_file_error(path):
    try:
        file_stat = os.lstat(path)
    except OSError as err:
        return str(err)
    if not stat.S_ISREG(file_stat.st_mode):
        return "not a regular file"
    return None


def _regular_open(path):
    flags = os.O_RDONLY
    for name in ("O_BINARY", "O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as err:
        return None, str(err)
    try:
        opened_stat = os.fstat(descriptor)
    except OSError as err:
        os.close(descriptor)
        return None, str(err)
    if not stat.S_ISREG(opened_stat.st_mode):
        os.close(descriptor)
        return None, "not a regular file"
    return descriptor, None


def _read_text(path, max_chars):
    descriptor, error = _regular_open(path)
    if error is not None:
        return None, error
    try:
        source = os.fdopen(
            descriptor,
            "r",
            encoding="utf-8",
            errors="replace",
            newline="",
        )
    except (OSError, ValueError) as err:
        os.close(descriptor)
        return None, str(err)
    try:
        with source:
            return source.read(max_chars + 1), None
    except OSError as err:
        return None, str(err)


def read_files(paths, char_cap):
    """Return immutable ``(chunks, warnings, overflow_path)`` batch results."""
    _validate_char_cap(char_cap)
    chunks = ()
    warnings = ()
    total = 0
    for path in paths:
        error = _regular_file_error(path)
        if error is not None:
            warnings = (*warnings, f"skipping {path} ({error})")
            continue
        text, error = _read_text(path, char_cap - total)
        if error is not None:
            warnings = (*warnings, f"skipping {path} ({error})")
            continue
        if "\x00" in text:
            warnings = (*warnings, f"skipping {path} (looks binary)")
            continue
        if len(text) > char_cap - total:
            return chunks, warnings, path
        if not text.strip():
            warnings = (*warnings, f"skipping {path} (empty)")
            continue
        chunks = (*chunks, (path, text))
        total += len(text)
    return chunks, warnings, None


def read_map_item(path, char_cap):
    """Return ``(text, error)`` for one bounded map file without printing."""
    _validate_char_cap(char_cap)
    if os.path.isdir(path):
        return None, (
            "is a directory — map takes one FILE per item; glob "
            f"its files instead (e.g. {path}/*.py)"
        )
    error = _regular_file_error(path)
    if error is not None:
        if error == "not a regular file":
            return None, error
        return None, f"unreadable ({error})"
    text, error = _read_text(path, char_cap)
    if error is not None:
        return None, f"unreadable ({error})"
    if "\x00" in text:
        return None, "looks binary — map sends text items only"
    if len(text) > char_cap:
        return None, (
            f"file exceeds the {char_cap:,}-char ceiling — too large for map; "
            "run ambient-codex audit on it instead"
        )
    if not text.strip():
        return None, "empty file"
    return text, None


__all__ = ("read_files", "read_map_item")
