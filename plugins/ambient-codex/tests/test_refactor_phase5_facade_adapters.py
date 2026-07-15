"""Contracts for compact, late-bound CLI facade adapters."""

import importlib
import unittest
from types import SimpleNamespace


class FacadeAdapterTests(unittest.TestCase):
    def test_adapter_resolves_module_and_dependencies_at_call_time(self):
        core = importlib.import_module("ambient_codex.facade_adapters")
        namespace = {
            "_feature": SimpleNamespace(run=lambda value, deps: (value, deps)),
            "_deps": lambda: "first",
        }
        core.install(namespace, "_feature", "_deps", "public=run")

        self.assertEqual(namespace["public"]("value"), ("value", "first"))
        namespace["_deps"] = lambda: "second"
        namespace["_feature"] = SimpleNamespace(
            run=lambda value, deps: (value.upper(), deps))
        self.assertEqual(namespace["public"]("value"), ("VALUE", "second"))

    def test_invalid_adapter_spec_fails_fast(self):
        core = importlib.import_module("ambient_codex.facade_adapters")
        with self.assertRaises(ValueError):
            core.install({}, "module", "deps", "not valid!")


if __name__ == "__main__":
    unittest.main()
