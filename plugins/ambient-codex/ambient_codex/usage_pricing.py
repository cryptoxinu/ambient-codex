"""Pure pricing primitives for local Ambient spend estimation.

These functions turn a fetched model catalog and the reference-price setting
into ``(input_per_Mtok, output_per_Mtok)`` pairs, and price a finished run's
token counts against catalog or reference pricing. They are pure (no I/O,
environment, state, or catalog fetching) and match the pre-extraction facade
behavior exactly. The cost-math functions take their worst-case ASSUMED prices
and untrusted-token coercer as injected deps -- the facade owns those constants
and the ``_as_pos_int`` helper. They are not fully total: a non-iterable catalog
or a price integer too large to convert to ``float()`` raises, exactly as before
-- neither arises from a real fetched catalog, and normalizing those is deferred
hardening. Higher layers own catalog fetching, reference resolution/memoization,
and receipt copy.
"""


def model_pricing(catalog, model):
    """Return ``(input per Mtok, output per Mtok)`` for ``model`` from the
    catalog, or ``None`` if unpriced. Zero/absent/NaN pricing is UNPRICED, not
    free -- treating it as 0 would disable the spend gate exactly when the
    catalog is degraded. Unpriced models fall to assumed worst-case pricing."""
    for entry in catalog or []:
        if isinstance(entry, dict) and entry.get("id") == model:
            price = entry.get("pricing")
            if not isinstance(price, dict):
                return None
            try:
                pin, pout = float(price.get("input")), float(price.get("output"))
            except (TypeError, ValueError):
                return None
            if not (pin >= 0 and pout >= 0 and (pin > 0 or pout > 0)):
                return None  # rejects NaN, negatives, and all-zero "pricing"
            return (pin, pout)
    return None


def parse_reference_price(raw):
    """Turn an ``AMBIENT_REFERENCE_PRICE`` value into ``(input, output)`` per
    Mtok, else ``None``. Accepts an ``in/out`` pair (``"3/15"``) or one blended
    figure (``"10"`` -> ``10/10``). Zero/negative/NaN/inf/garbage -> ``None``
    (the caller falls back to the default -- a junk reference must never
    fabricate a comparison)."""
    if not isinstance(raw, str):
        return None
    parts = [part.strip() for part in raw.strip().split("/")]
    if not 1 <= len(parts) <= 2 or not all(parts):
        return None
    try:
        vals = [float(part) for part in parts]
    except ValueError:
        return None
    if not all(0 < value < float("inf") for value in vals):  # also rejects NaN
        return None
    return (vals[0], vals[0]) if len(vals) == 1 else (vals[0], vals[1])


def usage_cost(model, usage, catalog, assumed_prices, to_pos_int):
    """``(dollars, assumed)`` for a FINISHED run's token counts. Unpriced model
    / degraded catalog -> worst-case ``assumed_prices`` (an (input, output)
    per-Mtok pair) with ``assumed=True``, so the figure can over-state cost but
    never under-state it (and the caller must not claim a saving from it).
    ``to_pos_int`` coerces the untrusted ``prompt_tokens``/``completion_tokens``
    fields to a non-negative int floor of 0."""
    price = model_pricing(catalog, model)
    assumed = price is None
    if assumed:
        price = assumed_prices
    tin = to_pos_int(usage.get("prompt_tokens"), 0)
    tout = to_pos_int(usage.get("completion_tokens"), 0)
    return (tin * price[0] + tout * price[1]) / 1e6, assumed


def reference_cost(usage, ref, to_pos_int):
    """The same tokens priced at the frontier reference ``ref`` (input, output)
    per Mtok. ``to_pos_int`` coerces the untrusted token counts."""
    tin = to_pos_int(usage.get("prompt_tokens"), 0)
    tout = to_pos_int(usage.get("completion_tokens"), 0)
    return (tin * ref[0] + tout * ref[1]) / 1e6


__all__ = ("model_pricing", "parse_reference_price", "usage_cost",
           "reference_cost")
