"""Phase 5 contract for the money-safe public usage projection."""

import importlib
import unittest


class OutputSchemaTests(unittest.TestCase):
    def test_module_allowlists_tokens_and_never_mutates_input(self):
        core = importlib.import_module("ambient_codex.output_schema")
        source = {"prompt_tokens": 1, "completion_tokens": 2,
                  "cost": 0.01, "price": 1, "saved_pct": 99}
        self.assertEqual(core.__all__, (
            "public_usage", "build_envelope", "build_error_envelope",
        ))
        self.assertEqual(core.public_usage(source),
                         {"prompt_tokens": 1, "completion_tokens": 2})
        self.assertIn("cost", source)

    def test_envelope_marks_token_cap_as_partial_without_money_fields(self):
        core = importlib.import_module("ambient_codex.output_schema")
        envelope, code = core.build_envelope(
            "audit", model="model", usage={"prompt_tokens": 1, "cost": 2},
            finish_reason="length", allow_partial=False, partial_exit_code=2,
        )
        self.assertEqual(code, 2)
        self.assertEqual(envelope["status"], "partial")
        self.assertNotIn("cost", envelope["usage"])

    def test_error_envelope_uses_the_same_versioned_public_schema(self):
        core = importlib.import_module("ambient_codex.output_schema")
        self.assertEqual(
            core.build_error_envelope("map", "usage", "bad input", 64),
            {"schema_version": 1, "kind": "map", "status": "error",
             "category": "usage", "diagnosis": "bad input", "exit_code": 64},
        )
