"""Phase 3G contracts for map-reduce planning helpers."""

import importlib
import unittest


class MapReducePlanningTests(unittest.TestCase):
    def test_module_owns_prompt_and_budget_grouping(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        self.assertEqual(core.__all__, ("map_note", "group_for_budget"))

    def test_grouping_is_ordered_and_never_overflows_a_joinable_group(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        groups = core.group_for_budget(["aaa", "bbbb", "cc", "dddd"], 7)
        self.assertEqual(groups, [["aaa", "bbbb"], ["cc", "dddd"]])

    def test_map_note_uses_the_supplied_collision_safe_index_marker(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        note = core.map_note("inspect", "MAP", 3, "<index>")
        self.assertIn("<index> of 3", note)
        self.assertIn("MAP", note)

