"""Bounded usage-ledger record reads for the local spend summary.

The ledger is a JSON-lines file of metering records written by the persistence
layer (``ambient_codex.usage_store``). Reading it is separated from pricing and
report math: this module only parses the file into well-formed records and
filters by recency, so the caller keeps ownership of catalog pricing, reference
math, and display. Reads raise the OS error family (missing file, unreadable
path) so the caller can map each to its own user-facing message.
"""

import json


def read_records(usage_path):
    """Return ``(records, bad)`` from the JSON-lines ledger: every well-formed
    object line as a dict, and a count of non-blank lines that were unparseable
    or not a JSON object. Blank/whitespace lines are skipped without counting.
    The open is not guarded here; a missing or unreadable ledger raises the OS
    error family to the caller."""
    records = []
    bad = 0
    with open(usage_path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                # Deliberately broader than json.JSONDecodeError: json.loads can
                # also raise a plain ValueError (e.g. an integer line past the
                # int-string digit limit on 3.11+). The old inline reader crashed
                # on that; counting it corrupt is intentional, tested hardening.
                bad += 1
                continue
            if not isinstance(record, dict):
                bad += 1
                continue
            records.append(record)
    return records, bad


def filter_recent(records, cutoff, ts_of):
    """Return the records whose timestamp (via ``ts_of``) is at or after
    ``cutoff``. ``ts_of`` maps a record to a comparable number, letting the
    caller own timestamp coercion."""
    return [record for record in records if ts_of(record) >= cutoff]


__all__ = ("read_records", "filter_recent")
