"""Validated late-bound adapters for the extensionless CLI facade."""

import functools
import re


_NAME = re.compile(r"^[A-Za-z_]\w*$")


def _parse(specification):
    pairs = []
    for item in specification.split():
        public, separator, target = item.partition("=")
        target = target if separator else public
        if not _NAME.fullmatch(public) or not _NAME.fullmatch(target):
            raise ValueError(f"invalid facade adapter specification: {item!r}")
        pairs.append((public, target))
    return tuple(pairs)


def build(namespace, module_name, dependencies_name, specification):
    """Build adapters that resolve collaborators from ``namespace`` per call.

    Late resolution deliberately preserves the launcher's established testing
    and embedding seams: replacing a module, dependency builder, or any value
    read by that builder remains visible without rebuilding the adapter table.
    """
    adapters = []
    for public_name, target_name in _parse(specification):
        def adapter(*args, _target=target_name, **kwargs):
            module = namespace[module_name]
            dependencies = namespace[dependencies_name]()
            return getattr(module, _target)(*args, deps=dependencies, **kwargs)

        adapter = functools.update_wrapper(
            adapter, getattr(namespace[module_name], target_name))
        adapter.__name__ = public_name
        adapter.__qualname__ = public_name
        adapters.append(adapter)
    return tuple(adapters)


def install(namespace, module_name, dependencies_name, specification):
    """Build and install a group, returning its validated public names."""
    pairs = _parse(specification)
    adapters = build(
        namespace, module_name, dependencies_name, specification)
    for (public_name, _target_name), adapter in zip(pairs, adapters, strict=True):
        namespace[public_name] = adapter
    return tuple(public_name for public_name, _target_name in pairs)


__all__ = ("build", "install")
