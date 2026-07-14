"""Phase 3G contracts for map-reduce planning helpers."""

import importlib
import unittest


class MapReducePlanningTests(unittest.TestCase):
    def test_module_owns_prompt_and_budget_grouping(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        self.assertEqual(
            core.__all__,
            ("files_block", "chunk_ranges", "code_map_budget", "map_note", "group_for_budget"),
        )

    def test_input_helpers_preserve_file_boundaries_and_coverage_ranges(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        block = core.files_block([("a.py", "x = 1")])
        self.assertEqual(block, "===== FILE: a.py =====\nx = 1")
        self.assertEqual(core.chunk_ranges("===== a.py [lines 1-2] =====\nx"),
                         ["a.py [lines 1-2]"])
        self.assertEqual(core.code_map_budget(10_000, 4_000, 40_000), 1_000)

    def test_grouping_is_ordered_and_never_overflows_a_joinable_group(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        groups = core.group_for_budget(["aaa", "bbbb", "cc", "dddd"], 7)
        self.assertEqual(groups, [["aaa", "bbbb"], ["cc", "dddd"]])

    def test_map_note_uses_the_supplied_collision_safe_index_marker(self):
        core = importlib.import_module("ambient_codex.map_reduce")
        note = core.map_note("inspect", "MAP", 3, "<index>")
        self.assertIn("<index> of 3", note)
        self.assertIn("MAP", note)
