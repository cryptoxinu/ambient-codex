"""Bounded private usage-ledger persistence for local Ambient metering.

Ambient exposes no balance endpoint, so spend is estimated from a local
append-only ledger. The ledger is capped by a read-modify-rewrite trim, which
must be exclusive across BOTH in-process chunk workers and concurrent ambient
processes. When the cross-process file lock is unavailable a metering line is
written to a per-process spool and folded back under the lock later, never
appended unlocked where a concurrent trim could truncate it away. Losing a
trim costs nothing; losing metering does. Every operation is best effort and
never raises into the caller.
"""

import os
import threading


# Serializes the read-modify-rewrite trim across in-process chunk workers. The
# cross-process file lock is supplied by the caller as an explicit adapter.
_LEDGER_SERIALIZE = threading.Lock()


def spool_line(line, usage_path, max_bytes, *, getpid=None):
    """Append one metering line to this process's own spool when the ledger
    lock is unavailable. Only the owning process writes its spool, so no lock
    is needed; a later successful acquire folds it back. Size-capped so a
    permanently wedged lock (for example a crashed Windows owner) cannot grow
    it without bound. ``getpid`` defaults to a live ``os.getpid`` lookup at
    call time to preserve the original late-bound behavior."""
    pid = os.getpid() if getpid is None else getpid()
    spool = f"{usage_path}.spool.{pid}"
    try:
        if os.path.exists(spool) and os.path.getsize(spool) > max_bytes:
            return
        fd = os.open(spool, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        pass


def merge_spools(usage_path, pid_alive, *, getpid=None):
    """Fold spooled metering lines back into the main ledger. The caller MUST
    hold the ledger lock. Our own spool is always safe (only we write it, and
    appends are serialized in-process); a foreign spool is merged only when its
    owner pid is provably dead, since a live or unknowable owner may still be
    appending to it (its own merge folds it in later). ``getpid`` defaults to a
    live ``os.getpid`` lookup at call time to preserve late-bound behavior."""
    directory = os.path.dirname(usage_path)
    prefix = os.path.basename(usage_path) + ".spool."
    try:
        names = os.listdir(directory)
    except OSError:
        return
    current = os.getpid() if getpid is None else getpid()
    for name in names:
        if not name.startswith(prefix):
            continue
        try:
            pid = int(name[len(prefix):])
        except ValueError:
            continue
        if pid != current and pid_alive(pid) is not False:
            continue
        spath = os.path.join(directory, name)
        try:
            with open(spath, encoding="utf-8") as handle:
                data = handle.read()
            if data:
                fd = os.open(usage_path,
                             os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                with os.fdopen(fd, "a", encoding="utf-8") as handle:
                    handle.write(data)
            os.unlink(spath)
        except OSError:
            continue


def _trim_ledger(usage_path, max_bytes, trim_keep_lines):
    """Heal a pre-hardening ledger's permissions, then cap it to the newest
    ``trim_keep_lines`` once it grows past ``max_bytes``. Best effort."""
    try:
        if os.stat(usage_path).st_mode & 0o077:
            os.chmod(usage_path, 0o600)
        if os.path.getsize(usage_path) > max_bytes:
            with open(usage_path, encoding="utf-8") as handle:
                kept = handle.readlines()[-trim_keep_lines:]
            with open(usage_path, "w", encoding="utf-8") as handle:
                handle.writelines(kept)
    except OSError:
        pass


def append_line(line, *, usage_path, max_bytes, trim_keep_lines, lock_wait_s,
                private_dir, fs_lock, pid_alive, getpid=None):
    """Persist one metering line under both the in-process trim lock and the
    caller-supplied cross-process file lock. If the file lock cannot be taken
    the line is spooled per-process and merged later, never appended unlocked.
    Best effort: metering never raises into the caller."""
    conf_dir = os.path.dirname(usage_path)
    try:
        private_dir(conf_dir)
        with _LEDGER_SERIALIZE, fs_lock(os.path.join(conf_dir, ".usage.lock"),
                                        lock_wait_s) as locked:
            if not locked:
                spool_line(line, usage_path, max_bytes, getpid=getpid)
                return
            merge_spools(usage_path, pid_alive, getpid=getpid)
            _trim_ledger(usage_path, max_bytes, trim_keep_lines)
            fd = os.open(usage_path,
                         os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as handle:
                handle.write(line)
    except OSError:
        pass


__all__ = ("spool_line", "merge_spools", "append_line")
