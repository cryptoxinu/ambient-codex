import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestCodexNativeIsolation(unittest.TestCase):
    def test_hook_has_no_claude_plugin_root_fallback(self):
        text = (ROOT / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        self.assertNotIn("CLAUDE_PLUGIN_ROOT", text)

    def test_skill_forbids_path_first_ambient_routing(self):
        text = (ROOT / "skills" / "ambient" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("must never\nrun a bare `ambient` from PATH", text)
        forbidden = [
            "Prefer `ambient`",
            "on PATH when available",
            "Claude-style slash command",
            "AskUserQuestion",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, text)
        self.assertIn("ambient_control", text)
        self.assertIn("control mode off", text)

    def test_codex_facing_docs_do_not_reintroduce_path_first_routing(self):
        docs = [
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "docs" / "RELEASING.md",
        ]
        pattern = re.compile(r"Prefer `ambient`|on PATH when available|CLAUDE_PLUGIN_ROOT")
        for path in docs:
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), str(path))

    def test_mcp_uses_bundled_cli_not_path_lookup(self):
        spec = importlib.util.spec_from_file_location(
            "ambient_mcp_isolation",
            ROOT / "mcp" / "ambient_mcp.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ambient_bin().name, "ambient")
        self.assertIn("ambient-codex", module.ambient_bin().as_posix())


if __name__ == "__main__":
    unittest.main()
