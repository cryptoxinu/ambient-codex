"""Repository text transforms and bounded size accounting."""

import os
import stat


_READ_BLOCK_BYTES = 1 << 16


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


__all__ = ("with_line_gutters", "guttered_file_size")
