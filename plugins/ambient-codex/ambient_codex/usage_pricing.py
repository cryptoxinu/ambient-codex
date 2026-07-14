"""Pure pricing primitives for local Ambient spend estimation.

These functions turn a fetched model catalog and the reference-price setting
into ``(input_per_Mtok, output_per_Mtok)`` pairs. They are pure (no I/O,
environment, state, or catalog fetching) and match the pre-extraction facade
behavior exactly. They are not fully total: a non-iterable catalog or a price
integer too large to convert to ``float()`` raises, exactly as before -- neither
arises from a real fetched catalog, and normalizing those is deferred hardening.
Higher layers own catalog fetching, reference resolution/memoization, cost math,
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


__all__ = ("model_pricing", "parse_reference_price")
