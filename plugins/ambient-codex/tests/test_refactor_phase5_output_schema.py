"""Phase 5 contract for the money-safe public usage projection."""

import importlib
import unittest


class OutputSchemaTests(unittest.TestCase):
    def test_module_allowlists_tokens_and_never_mutates_input(self):
        core = importlib.import_module("ambient_codex.output_schema")
        source = {"prompt_tokens": 1, "completion_tokens": 2,
                  "cost": 0.01, "price": 1, "saved_pct": 99}
        self.assertEqual(core.__all__, ("public_usage",))
        self.assertEqual(core.public_usage(source),
                         {"prompt_tokens": 1, "completion_tokens": 2})
        self.assertIn("cost", source)
