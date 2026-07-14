"""Pure identity policy for resumable build workflows."""

import hashlib
import json
import os


def state_path(root):
    """Return the fixed resume-state path beneath a validated build root."""
    return os.path.join(root, ".ambient-build.json")


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


def _normalized_plan(state, root, max_plan, safe_relpath):
    """Copy and firewall the bounded plan from untrusted resume state."""
    plan = []
    for item in state["plan"][:max_plan]:
        if not isinstance(item, dict):
            return None
        copied = dict(item)
        copied["path"] = safe_relpath(str(copied.get("path", "")), root)
        plan.append(copied)
    return plan


def _normalized_done(state, plan_paths, root, max_file_bytes, safe_relpath):
    """Return verified completed files that remain inside the bounded plan."""
    done = {}
    for path, record in state["done"].items():
        rel = safe_relpath(str(path), root)
        if rel not in plan_paths:
            continue
        if not (isinstance(record, dict) and isinstance(record.get("content"), str)):
            return None
        content = record["content"]
        if max_file_bytes is not None and len(content.encode()) > max_file_bytes:
            continue
        digest = hashlib.sha256(content.encode()).hexdigest()
        if record.get("sha256") != digest:
            return None
        done[rel] = {"content": content, "sha256": digest}
    return done


def normalize_resume_state(state, *, task_sha, root, max_plan, max_file_bytes,
                           safe_relpath):
    """Validate parsed untrusted resume state without mutating its caller.

    ``safe_relpath`` is injected so the path firewall stays owned by the facade
    while this module remains pure and directly unit-testable.  Its ValueError
    is intentionally propagated so the boundary can emit the established warning.
    """
    if not (isinstance(state, dict) and state.get("version") == 1
            and state.get("task_sha") == task_sha
            and isinstance(state.get("plan"), list)
            and isinstance(state.get("done"), dict)):
        return None
    plan = _normalized_plan(state, root, max_plan, safe_relpath)
    if plan is None:
        return None
    done = _normalized_done(state, {item["path"] for item in plan}, root,
                            max_file_bytes, safe_relpath)
    if done is None:
        return None
    failed = state.get("failed")
    return dict(state, plan=plan, done=done,
                failed=[dict(item) for item in failed
                        if isinstance(item, dict) and isinstance(item.get("path"), str)
                        and isinstance(item.get("reason"), str)]
                if isinstance(failed, list) else [])


def validate_plan_items(items, *, max_files, root, safe_relpath):
    """Copy, cap, and firewall a model-proposed build manifest."""
    plan, rejected = [], []
    for item in items[:max_files]:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        candidate = dict(item)
        raw_path = str(candidate["path"])
        try:
            candidate["path"] = safe_relpath(raw_path, root)
            plan.append(candidate)
        except ValueError as error:
            rejected.append({"path": raw_path, "reason": f"unsafe path: {error}"})
    return plan, rejected


__all__ = ("state_path", "resume_identity", "normalize_resume_state",
           "validate_plan_items")
