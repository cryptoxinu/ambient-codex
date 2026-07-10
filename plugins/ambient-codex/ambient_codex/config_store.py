"""Defensive config parsing and reads with no import-time external effects."""

import os
import stat


def _parse_config_line(line):
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, _, value = stripped.partition("=")
    return key.strip(), value.strip()


def parse_config_lines(lines):
    """Parse env-style lines, retaining the final value for duplicate keys."""
    pairs = (_parse_config_line(line) for line in lines)
    return {pair[0]: pair[1] for pair in pairs if pair is not None}


def _prepare_config_file(config_path, stderr, platform_name):
    try:
        file_stat = os.lstat(config_path)
        if not stat.S_ISREG(file_stat.st_mode):
            print(
                f"ambient: {config_path} is not a regular file — ignoring it",
                file=stderr,
            )
            return False
        if hasattr(os, "getuid") and file_stat.st_uid != os.getuid():
            print(
                f"ambient: {config_path} is not owned by you — ignoring it",
                file=stderr,
            )
            return False
        mode_bits = file_stat.st_mode & 0o777
        if platform_name == "posix" and mode_bits != 0o600:
            os.chmod(config_path, 0o600)
            print(
                f"ambient: tightened {config_path} permissions "
                f"({oct(mode_bits)[2:]} -> 600)",
                file=stderr,
            )
        return True
    except FileNotFoundError:
        return False
    except OSError as err:
        print(f"ambient: cannot read {config_path}: {err}", file=stderr)
        return False


def read_config_file(config_path, launcher_name, stderr, platform_name):
    """Read a regular owner-controlled UTF-8 config file, or return empty."""
    if not _prepare_config_file(config_path, stderr, platform_name):
        return {}
    try:
        with open(config_path, encoding="utf-8") as config_file:
            return parse_config_lines(config_file)
    except FileNotFoundError:
        return {}
    except UnicodeDecodeError:
        print(
            f"ambient: {config_path} is corrupt (not valid UTF-8) — ignoring it. "
            f"Re-run: {launcher_name} setup",
            file=stderr,
        )
        return {}
    except OSError as err:
        print(f"ambient: cannot read {config_path}: {err}", file=stderr)
        return {}


__all__ = ("parse_config_lines", "read_config_file")
