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

