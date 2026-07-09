"""The delegate/takeover contract must resurface every session.

Codex registers no lifecycle hooks for this plugin by default (a default hook forces a
hook-trust review on a clean install), so `initialize` is the only per-session hook we
have. The mode is read from THIS install's env, never the shared ~/.config/ambient the
other Ambient install owns.
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
MCP = ROOT / "mcp" / "ambient_mcp.py"


def load_mcp():
    spec = importlib.util.spec_from_file_location("ambient_mcp_mode", MCP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestCurrentMode(unittest.TestCase):
    def setUp(self):
        self.mcp = load_mcp()

    def _home(self, tmp, text):
        root = Path(tmp) / "state"
        root.mkdir(parents=True)
        (root / "env").write_text(text, encoding="utf-8")
        return str(root)

    def test_missing_env_is_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"AMBIENT_CODEX_HOME": tmp}):
                self.assertEqual(self.mcp.current_mode(), "off")

    def test_takeover_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = self._home(tmp, "AMBIENT_DELEGATE=takeover\n")
            with mock.patch.dict(os.environ, {"AMBIENT_CODEX_HOME": home}):
                self.assertEqual(self.mcp.current_mode(), "takeover")

    def test_last_assignment_wins_like_the_cli_parser(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = self._home(tmp, "AMBIENT_DELEGATE=off\n AMBIENT_DELEGATE = takeover \n")
            with mock.patch.dict(os.environ, {"AMBIENT_CODEX_HOME": home}):
                self.assertEqual(self.mcp.current_mode(), "takeover")

    def test_garbage_value_falls_back_to_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = self._home(tmp, "AMBIENT_DELEGATE=wat\n")
            with mock.patch.dict(os.environ, {"AMBIENT_CODEX_HOME": home}):
                self.assertEqual(self.mcp.current_mode(), "off")

    def test_the_other_installs_takeover_flag_is_ignored(self):
        """~/.config/ambient belongs to the Claude plugin; it must not drive Codex."""
        with tempfile.TemporaryDirectory() as tmp:
            shared = Path(tmp) / ".config" / "ambient"
            shared.mkdir(parents=True)
            (shared / "env").write_text("AMBIENT_DELEGATE=takeover\n", encoding="utf-8")
            codex_home = Path(tmp) / ".config" / "ambient-codex"
            codex_home.mkdir(parents=True)
            with mock.patch.dict(os.environ, {"AMBIENT_CODEX_HOME": str(codex_home)}):
                self.assertEqual(self.mcp.current_mode(), "off")


class TestSessionInstructions(unittest.TestCase):
    def setUp(self):
        self.mcp = load_mcp()

    def test_off_mode_keeps_the_base_instructions(self):
        with mock.patch.object(self.mcp, "current_mode", return_value="off"):
            self.assertEqual(self.mcp.session_instructions(),
                             self.mcp.SERVER_INSTRUCTIONS)

    def test_takeover_announces_itself(self):
        with mock.patch.object(self.mcp, "current_mode", return_value="takeover"):
            text = self.mcp.session_instructions()
        self.assertIn("TAKEOVER is ON", text)
        self.assertIn("ambient-codex control mode off", text)
        self.assertIn("bundled Ambient CLI", text)  # base contract preserved

    def test_delegate_announces_itself(self):
        with mock.patch.object(self.mcp, "current_mode", return_value="on"):
            text = self.mcp.session_instructions()
        self.assertIn("delegate mode is ON", text)

    def test_initialize_carries_the_mode(self):
        with mock.patch.object(self.mcp, "current_mode", return_value="takeover"):
            response = self.mcp.handle_request({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
            })
        self.assertIn("TAKEOVER is ON", response["result"]["instructions"])

    def test_initialize_never_shells_out(self):
        """A slow CLI must not blow Codex's MCP startup_timeout_sec."""
        with mock.patch.object(self.mcp.subprocess, "run") as run:
            self.mcp.handle_request({
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
            })
        run.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
