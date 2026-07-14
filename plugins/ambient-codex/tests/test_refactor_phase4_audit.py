"""Phase 4 contracts for audit preparation and cache identity."""

import importlib
import unittest


class AuditPreparationTests(unittest.TestCase):
    def test_module_owns_audit_prep_and_single_shot_key(self):
        core = importlib.import_module("ambient_codex.audit_core")
        self.assertEqual(core.__all__, (
            "prepare_sample", "single_shot_key", "reduce_findings",
        ))

    def test_single_shot_key_uses_a_complete_file_block_and_sample_salt(self):
        core = importlib.import_module("ambient_codex.audit_core")
        calls = []

        def key(*args, **kwargs):
            calls.append((args, kwargs))
            return "key"

        result = core.single_shot_key(
            "model", "system", [("a.py", "x")],
            type("Spec", (), {"max_tokens": 7, "temperature": 0.1,
                                "response_format": None, "_cache_salt": "lane"})(),
            files_block=lambda files: "BLOCK",
            cache_key=key,
        )
        self.assertEqual(result, "key")
        self.assertEqual(calls, [(("model", "system", "BLOCK", 7, 0.1, None),
                                  {"salt": "lane"})])

    def test_reducer_marks_unparseable_or_repaired_chunks_as_incomplete(self):
        core = importlib.import_module("ambient_codex.audit_core")
        values = iter((
            {"findings": [{"severity": "LOW"}]},
            {"findings": [], "_repaired": True},
            None,
        ))
        payload = core.reduce_findings(
            ["one", "two", "three"],
            parse=lambda _: next(values),
            dedupe=lambda findings: findings,
            verdict=lambda findings, partial: "SHIP",
        )
        self.assertEqual(payload["verdict"], "NEEDS WORK")
        self.assertEqual(payload["_repaired_chunks"], 1)
        self.assertEqual(payload["_unparsed_chunks"], 1)
