"""Phase 5 contracts for secure setup command orchestration."""

import importlib
import unittest


class SetupCommandTests(unittest.TestCase):
    def setUp(self):
        self.core = importlib.import_module("ambient_codex.setup_command")

    def test_bearer_prefix_is_removed_without_touching_key_body(self):
        self.assertEqual(
            self.core.normalize_pasted_key("  Bearer abc_DEF-123  "),
            "abc_DEF-123",
        )
        self.assertEqual(
            self.core.normalize_pasted_key("abc_DEF-123"),
            "abc_DEF-123",
        )


if __name__ == "__main__":
    unittest.main()
