"""Phase 5 contracts for extracted audit orchestration bindings."""

import importlib
import unittest


class AuditCommandTests(unittest.TestCase):
    def setUp(self):
        self.core = importlib.import_module("ambient_codex.audit_command")

    def test_dependency_bindings_are_immutable(self):
        deps = self.core.AuditDependencies.bind(render_result=object())

        with self.assertRaises(TypeError):
            deps.bindings["render_result"] = object()


if __name__ == "__main__":
    unittest.main()
