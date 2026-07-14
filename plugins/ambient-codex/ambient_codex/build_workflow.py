"""Pure identity policy for resumable build workflows."""

import hashlib
import json


def resume_identity(*, runtime_version, task, model, reduce_model, context_paths,
                    raw_context_sha, max_files, max_file_bytes, max_tokens,
                    temperature):
    """Hash stable build inputs so incompatible resumptions are rejected."""
    payload = {"identity_version": 2, "runtime_version": runtime_version,
               "task": task, "model": model, "reduce_model": reduce_model,
               "context_paths": sorted(str(path) for path in (context_paths or [])),
               "raw_context_sha": raw_context_sha, "max_files": max_files,
               "max_file_bytes": max_file_bytes, "max_tokens": max_tokens,
               "temperature": temperature}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = ("resume_identity",)
