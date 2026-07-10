"""Repository text transforms and bounded size accounting."""

import os
import stat
from typing import NamedTuple


_READ_BLOCK_BYTES = 1 << 16
_BINARY_SNIFF_BYTES = 8_192
_GIT_LIST_TIMEOUT_SECONDS = 30
_OVERSIZE_PATH_LIMIT = 40


class RepositorySkips(NamedTuple):
    """Immutable repository omission counters and bounded path evidence."""

    binary: int = 0
    lockfile: int = 0
    oversize: int = 0
    oversize_paths: tuple = ()
    nonregular: int = 0
    vendored: int = 0


def _entry_kind(entry, skip_dirs):
    try:
        if entry.is_dir(follow_symlinks=False):
            if entry.name in skip_dirs or entry.name.startswith("."):
                return "skip"
            return "directory"
        if entry.is_symlink() and entry.is_dir():
            return "skip"
    except OSError:
        return "file"
    return "file"


def _scan_directory(directory, skip_dirs):
    try:
        with os.scandir(directory) as scanner:
            entries = tuple(sorted(tuple(scanner), key=lambda entry: entry.name))
    except OSError:
        return (), ()
    classified = tuple(
        (_entry_kind(entry, skip_dirs), entry.path) for entry in entries
    )
    directories = tuple(path for kind, path in classified if kind == "directory")
    files = tuple(path for kind, path in classified if kind == "file")
    return directories, files


def _plain_candidate_paths(root, skip_dirs):
    pending = (root, None)
    while pending is not None:
        directory, pending = pending
        children, files = _scan_directory(directory, skip_dirs)
        for path in files:
            yield os.path.relpath(path, root)
        for child in reversed(children):
            pending = (child, pending)


def _decode_git_paths(output):
    if isinstance(output, bytes):
        values = output.split(b"\0")
    elif isinstance(output, str):
        values = output.split("\0")
    else:
        return None
    try:
        return tuple(os.fsdecode(value) for value in values if value)
    except (UnicodeError, ValueError):
        return None


def candidate_paths(root, run_git, timeout_error, skip_dirs):
    """Return immutable Git-aware or plain-walk repository candidates."""
    root = os.fsdecode(os.fspath(root))
    skip_dirs = frozenset(skip_dirs)
    try:
        completed = run_git(
            [
                "git", "-C", root, "ls-files", "-z", "--cached", "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            timeout=_GIT_LIST_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, timeout_error):
        completed = None
    if completed is not None and getattr(completed, "returncode", 1) == 0:
        paths = _decode_git_paths(getattr(completed, "stdout", None))
        if paths is not None:
            return paths, True
    return tuple(_plain_candidate_paths(root, skip_dirs)), False


def _candidate_text(candidate):
    try:
        return os.fsdecode(os.fspath(candidate))
    except (TypeError, UnicodeError, ValueError):
        return None


def _candidate_contract(candidate, used_git, skip_dirs, lockfiles):
    relative = _candidate_text(candidate)
    if relative is None:
        return None, None, None
    portable = relative.replace(os.sep, "/")
    parts = portable.split("/")
    if not relative or "\0" in relative or os.path.isabs(relative) or ".." in parts:
        return None, None, None
    if any(
            part in skip_dirs
            or (not used_git and part != "." and part.startswith("."))
            for part in parts[:-1]
    ):
        return None, None, "vendored"
    if parts[-1] in lockfiles or parts[-1].endswith(".lock"):
        return None, None, "lockfile"
    return relative, relative.replace("\\", "/"), None


def _within_root(child_real, root_real):
    try:
        return os.path.commonpath([child_real, root_real]) == root_real
    except ValueError:
        return False


def _close_descriptor(descriptor):
    try:
        os.close(descriptor)
    except OSError:
        pass


def _open_matching_descriptor(path, expected_stat):
    flags = os.O_RDONLY
    for name in ("O_BINARY", "O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK"):
        flags |= getattr(os, name, 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None, None, False
    try:
        opened_stat = os.fstat(descriptor)
    except OSError:
        _close_descriptor(descriptor)
        return None, None, False
    try:
        matches = os.path.samestat(expected_stat, opened_stat)
    except (AttributeError, OSError, ValueError):
        matches = False
    if not stat.S_ISREG(opened_stat.st_mode) or not matches:
        _close_descriptor(descriptor)
        return None, None, True
    return descriptor, opened_stat, False


def _inspect_candidate(root, root_real, relative, label, per_file_cap):
    full = os.path.join(root, relative)
    try:
        expected_stat = os.lstat(full)
    except (OSError, ValueError):
        return None, None, label
    if not stat.S_ISREG(expected_stat.st_mode):
        return None, "nonregular", label
    if not _within_root(os.path.realpath(full), root_real):
        return None, "nonregular", label
    descriptor, opened_stat, mismatch = _open_matching_descriptor(full, expected_stat)
    if descriptor is None:
        return None, "nonregular" if mismatch else None, label
    try:
        if not _within_root(os.path.realpath(full), root_real):
            return None, "nonregular", label
        if opened_stat.st_size == 0:
            return None, None, label
        if opened_stat.st_size > per_file_cap:
            return None, "oversize", label
        head = os.read(descriptor, _BINARY_SNIFF_BYTES)
    except (OSError, ValueError):
        return None, None, label
    finally:
        _close_descriptor(descriptor)
    if not isinstance(head, bytes):
        return None, None, label
    if b"\0" in head:
        return None, "binary", label
    return (label, full, opened_stat.st_size), None, label


def _classify_candidate(
        root, root_real, candidate, used_git, per_file_cap, skip_dirs, lockfiles
):
    relative, label, reason = _candidate_contract(
        candidate, used_git, skip_dirs, lockfiles
    )
    if relative is None:
        return None, reason, label
    return _inspect_candidate(root, root_real, relative, label, per_file_cap)


def _record_skip(skipped, reason, label):
    if reason == "binary":
        return skipped._replace(binary=skipped.binary + 1)
    if reason == "lockfile":
        return skipped._replace(lockfile=skipped.lockfile + 1)
    if reason == "nonregular":
        return skipped._replace(nonregular=skipped.nonregular + 1)
    if reason == "vendored":
        return skipped._replace(vendored=skipped.vendored + 1)
    if reason == "oversize":
        paths = skipped.oversize_paths
        if label is not None and len(paths) < _OVERSIZE_PATH_LIMIT:
            paths = (*paths, label)
        return skipped._replace(oversize=skipped.oversize + 1, oversize_paths=paths)
    return skipped


def classify_repository_files(
        root, candidates, used_git, per_file_cap, skip_dirs, lockfiles
):
    """Return immutable auditable files and bounded omission metadata."""
    if (
        isinstance(per_file_cap, bool)
        or not isinstance(per_file_cap, int)
        or per_file_cap <= 0
    ):
        raise ValueError("per-file ceiling must be a positive integer")
    root = os.fsdecode(os.fspath(root))
    root_real = os.path.realpath(root)
    skip_dirs = frozenset(skip_dirs)
    lockfiles = frozenset(lockfiles)
    normalized = tuple(
        value for value in (_candidate_text(item) for item in candidates)
        if value is not None
    )
    outcomes = tuple(
        _classify_candidate(
            root, root_real, candidate, used_git, per_file_cap,
            skip_dirs, lockfiles,
        )
        for candidate in sorted(set(normalized))
    )
    files = tuple(item for item, _reason, _label in outcomes if item is not None)
    skipped = RepositorySkips()
    for _item, reason, label in outcomes:
        skipped = _record_skip(skipped, reason, label)
    return files, skipped


def with_line_gutters(labeled):
    """Return immutable labeled text with absolute one-based line prefixes."""
    output = ()
    for label, text in labeled:
        lines = text.split("\n")
        width = max(2, len(str(len(lines))))
        guttered = "\n".join(
            f"{index:>{width}}| {line}"
            for index, line in enumerate(lines, 1)
        )
        output = (*output, (label, guttered))
    return output


def _open_regular_descriptor(path):
    try:
        path_stat = os.lstat(path)
    except OSError as err:
        return None, str(err)
    if not stat.S_ISREG(path_stat.st_mode):
        return None, "not a regular file"
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


def guttered_file_size(path, size):
    """Conservatively estimate post-gutter characters with bounded file I/O."""
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise ValueError("snapshot size must be a non-negative integer")
    descriptor, error = _open_regular_descriptor(path)
    if error is not None:
        return size
    remaining = size + 1
    bytes_read = 0
    newline_count = 0
    try:
        while remaining > 0:
            block = os.read(descriptor, min(_READ_BLOCK_BYTES, remaining))
            if not block:
                break
            if not isinstance(block, bytes):
                return size
            bytes_read += len(block)
            remaining -= len(block)
            newline_count += block.count(b"\n")
    except OSError:
        return size
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    lines = newline_count + 1
    width = max(2, len(str(lines)))
    return max(size, bytes_read) + lines * (width + 2)


__all__ = (
    "RepositorySkips",
    "candidate_paths",
    "classify_repository_files",
    "with_line_gutters",
    "guttered_file_size",
)
