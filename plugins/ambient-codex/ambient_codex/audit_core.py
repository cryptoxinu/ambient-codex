"""Dependency-injected preparation primitives shared by audit workflows."""

import dataclasses


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


__all__ = ("prepare_sample", "single_shot_key")
