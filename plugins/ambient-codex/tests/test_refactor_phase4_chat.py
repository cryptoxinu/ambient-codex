"""Phase 4 contracts for pure interactive-chat workflow policies."""

import importlib
import unittest


class ChatWorkflowTests(unittest.TestCase):
    def test_trim_history_is_immutable_and_retains_the_latest_exchange(self):
        core = importlib.import_module("ambient_codex.chat_workflow")
        history = [{"content": "old"}, {"content": "reply"},
                   {"content": "new"}, {"content": "latest"}]
        self.assertEqual(core.trim_history(history, 10), history[-2:])
        self.assertEqual(history[0]["content"], "old")
