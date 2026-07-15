"""Phase 4 contracts for code-generation workflow policies."""

import importlib
import unittest


class CodeWorkflowTests(unittest.TestCase):
    def test_final_messages_are_immutable_and_preserve_context_boundaries(self):
        core = importlib.import_module("ambient_codex.code_workflow")
        task = "Add validation"
        context = "def existing():\n    pass\n"
        messages = core.final_messages(task, context)
        self.assertEqual(messages[1]["content"],
                         "Add validation\n\nContext files:\n\ndef existing():\n    pass\n")
        self.assertIn("senior software engineer", messages[0]["content"])
        self.assertEqual(task, "Add validation")
        self.assertEqual(context, "def existing():\n    pass\n")

    def test_context_is_clamped_to_the_final_prompt_room_immutably(self):
        core = importlib.import_module("ambient_codex.code_workflow")
        context = "a" * 1001
        clamped = core.clamp_context(
            context, task="t" * 600, single_shot_chars=2_000)
        self.assertEqual(clamped[:1000], "a" * 1000)
        self.assertTrue(clamped.endswith("[ambient: context truncated to fit]"))
        self.assertEqual(context, "a" * 1001)
