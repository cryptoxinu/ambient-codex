"""Dependency-injected preparation primitives shared by audit workflows."""

import dataclasses
import json
import re


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
_SPLIT_ARTIFACT = re.compile(
    r"(?i)\b(?:suspected\s+)?split artifact\b"
    r"|\bfile (?:being )?split across chunks\b")


def _finding_signature(finding):
    path = str(finding.get("file", "")).strip().replace("\\", "/").lstrip("./")
    try:
        line = int(finding.get("line") or 0)
    except (TypeError, ValueError):
        line = 0
    words = re.sub(r"\W+", " ", str(finding.get("title", ""))).lower().split()
    return path, line, tuple(words[:4])


def _titles_match(first, second):
    length = min(len(first), len(second), 4)
    return (not first and not second) if length == 0 else first[:length] == second[:length]


def _is_split_artifact(finding):
    if not isinstance(finding, dict):
        return False
    text = " ".join(str(finding.get(key, ""))
                    for key in ("title", "defect", "scenario", "fix"))
    return bool(_SPLIT_ARTIFACT.search(text))


def dedupe_findings(findings):
    """Conservatively merge duplicate chunk findings without losing context."""
    kept = []
    for finding in findings:
        if not isinstance(finding, dict) or _is_split_artifact(finding):
            continue
        path, line, title = _finding_signature(finding)
        slot = next((entry for entry in kept
                     if entry[0][0] == path and _titles_match(entry[0][2], title)
                     and abs(entry[0][1] - line) <= 3), None)
        if slot is None:
            kept.append(((path, line, title), finding))
            continue
        previous = slot[1]
        best = (finding if SEVERITY_ORDER.get(finding.get("severity"), 9)
                < SEVERITY_ORDER.get(previous.get("severity"), 9) else previous)
        richest = max(previous, finding,
                      key=lambda value: len(str(value.get("scenario", ""))))
        if len(str(richest.get("scenario", ""))) > len(str(best.get("scenario", ""))):
            best = {**best, "scenario": richest.get("scenario", "")}
        kept[kept.index(slot)] = (slot[0], best)
    return sorted((finding for _, finding in kept),
                  key=lambda finding: SEVERITY_ORDER.get(finding.get("severity"), 9))


def verdict_from(findings, partial):
    """Derive a conservative audit verdict from structured findings."""
    severities = {finding.get("severity") for finding in findings
                  if isinstance(finding, dict)}
    if partial:
        return "NEEDS WORK"
    if {"CRITICAL", "HIGH"} & severities:
        return "FIX FIRST"
    return "NEEDS WORK" if {"MEDIUM", "LOW"} & severities else "SHIP"


def extract_json(text):
    """Best-effort object extraction that marks only safe truncation repairs."""
    if not text:
        return None
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.S)
    if fence:
        try:
            parsed = json.loads(fence.group(1).strip())
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            pass
    decoder = json.JSONDecoder()
    first = stripped.find("{")
    if first == -1:
        return None
    fragment = stripped[first:]
    try:
        parsed, _end = decoder.raw_decode(fragment)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    if fragment.count('"') % 2 == 0:
        missing_brackets = fragment.count("[") - fragment.count("]")
        missing_braces = fragment.count("{") - fragment.count("}")
        if 0 <= missing_brackets <= 5 and 1 <= missing_braces <= 5:
            try:
                parsed = json.loads(
                    fragment + "]" * missing_brackets + "}" * missing_braces)
                if isinstance(parsed, dict):
                    return {**parsed, "_repaired": True}
            except json.JSONDecodeError:
                pass
    index = first + 1
    while True:
        start = stripped.find("{", index)
        if start == -1:
            return None
        try:
            parsed, _end = decoder.raw_decode(stripped[start:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        index = start + 1


def prepare_sample(model, catalog, labeled, system_prompt, args, *,
                   model_profile, request_spec, response_format,
                   findings_schema, json_instruction):
    """Build the model-specific request and prompt for one audit sample."""
    profile = model_profile(catalog, model)
    single, chunk = profile.single_shot_chars, profile.chunk_chars
    total = sum(len(text) for _, text in labeled)
    spec = request_spec.from_args(args)
    structured = response_format(model, profile, findings_schema)
    prepared = dataclasses.replace(
        spec.with_output_budget(profile, total if total <= single else chunk),
        response_format=structured,
    )
    prompt = system_prompt + (
        json_instruction
        if structured is None or structured.get("type") == "json_object" else ""
    )
    return prepared, prompt, single, chunk, total


def single_shot_key(model, system_prompt, labeled, spec, *, files_block,
                    cache_key):
    """Build the stable, salt-aware cache key for one audit completion."""
    return cache_key(
        model, system_prompt, files_block(labeled), spec.max_tokens,
        spec.temperature, spec.response_format, salt=spec._cache_salt,
    )


def reduce_findings(texts, *, parse, dedupe, verdict):
    """Reduce parsed chunk findings without masking incomplete coverage."""
    collected = []
    unparsed = 0
    repaired = 0
    for text in texts:
        parsed = parse(text)
        if parsed and isinstance(parsed.get("findings"), list):
            collected.extend(parsed["findings"])
            repaired += 1 if parsed.get("_repaired") else 0
        else:
            unparsed += 1
    findings = dedupe(collected)
    final_verdict = ("NEEDS WORK" if (unparsed or repaired)
                     else verdict(findings, False))
    return {
        "findings": findings,
        "verdict": final_verdict,
        "_unparsed_chunks": unparsed,
        "_repaired_chunks": repaired,
    }


__all__ = ("extract_json", "dedupe_findings", "verdict_from", "prepare_sample",
           "single_shot_key", "reduce_findings")
