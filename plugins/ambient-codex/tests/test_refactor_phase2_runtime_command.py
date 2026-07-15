"""Phase 2 contracts for extracted runtime state and backend configuration."""

import importlib
import unittest


class RuntimeCommandTests(unittest.TestCase):
    def test_dependency_bindings_are_immutable(self):
        core = importlib.import_module("ambient_codex.runtime_command")
        deps = core.RuntimeDependencies.bind(state=object())

        with self.assertRaises(TypeError):
            deps.bindings["state"] = object()


if __name__ == "__main__":
    unittest.main()
