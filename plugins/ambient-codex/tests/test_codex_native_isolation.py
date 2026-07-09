import importlib.util
import json
import re
import unittest
from functools import lru_cache
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_mcp():
    spec = importlib.util.spec_from_file_location(
        "ambient_mcp_isolation",
        ROOT / "mcp" / "ambient_mcp.py",
    )
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load Ambient MCP module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_schema_properties(schema):
    properties = set()
    if not isinstance(schema, dict):
        return properties
    nested = schema.get("properties", {})
    if isinstance(nested, dict):
        properties.update(nested)
        for child in nested.values():
            properties.update(collect_schema_properties(child))
    items = schema.get("items")
    if isinstance(items, dict):
        properties.update(collect_schema_properties(items))
    return properties


class TestCodexNativeIsolation(unittest.TestCase):
    def test_plugin_bundles_no_default_lifecycle_hooks(self):
        data = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        self.assertEqual(data, {"hooks": {}})

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
            ROOT / "docs" / "CODEX_NATIVE_ARCHITECTURE.md",
        ]
        pattern = re.compile(r"Prefer `ambient`|on PATH when available|CLAUDE_PLUGIN_ROOT")
        for path in docs:
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), str(path))

    def test_architecture_contract_is_codex_native_hybrid(self):
        text = (ROOT / "docs" / "CODEX_NATIVE_ARCHITECTURE.md").read_text(encoding="utf-8")
        expected_tools = {
            "ambient_self_test",
            "ambient_status",
            "ambient_control",
            "ambient_set_mode",
            "ambient_set_model",
            "ambient_pick_model",
            "ambient_set_config",
            "ambient_key",
            "ambient_models",
            "ambient_doctor",
            "ambient_usage",
            "ambient_ask",
            "ambient_audit_small",
        }
        required = [
            "Ambient Codex is a standalone Codex plugin",
            "intentionally hybrid",
            "Codex skill",
            "MCP server",
            "Bundled CLI",
            "Hooks",
            "Why Not MCP-Only",
            "Why Not CLI-Only",
            "must not depend on a Claude",
            "Hooks are not part of the default runtime path",
        ]
        for needle in required:
            self.assertIn(needle, text)
        self.assertIn("Content-Length framed JSON-RPC", text)
        self.assertIn("newline-delimited JSON-RPC", text)
        tool_section = text.split("## MCP Control Plane", 1)[1].split("## CLI Execution Plane", 1)[0]
        self.assertEqual(set(re.findall(r"- `(ambient_[^`]+)`", tool_section)), expected_tools)

        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.7.2")
        long_description = manifest["interface"]["longDescription"]
        self.assertIn("Hooks are not registered by default.", long_description)
        hook_capabilities = [
            item for item in manifest["interface"].get("capabilities", [])
            if "hook" in item.lower()
        ]
        self.assertEqual(hook_capabilities, [])
        hook_advertising = re.compile(r"adds[^.]*hooks|lifecycle hooks|hook support", re.IGNORECASE)
        self.assertRegex("Ambient Codex adds lifecycle hooks.", hook_advertising)
        self.assertIsNone(hook_advertising.search(long_description))

        mcp = load_mcp()
        self.assertEqual({tool["name"] for tool in mcp.TOOLS}, expected_tools)
        self.assertEqual(set(mcp.TOOL_HANDLERS), expected_tools)

        forbidden_secret_args = {
            "ambient_api_key",
            "api_key",
            "apikey",
            "authorization",
            "credential",
            "credentials",
            "key",
            "password",
            "secret",
            "token",
        }
        for tool in mcp.TOOLS:
            with self.subTest(tool=tool["name"]):
                properties = collect_schema_properties(tool["inputSchema"])
                self.assertFalse(properties & forbidden_secret_args)

        with mock.patch.object(mcp.subprocess, "run") as run:
            for secret_name in ("ambient_api_key", "api_key", "key", "token"):
                with self.subTest(secret_name=secret_name):
                    with self.assertRaises(mcp.ToolInputError):
                        mcp.call_tool("ambient_set_config", {
                            "name": secret_name,
                            "value": "amb_should_not_be_accepted",
                        })
        run.assert_not_called()

    def test_mcp_uses_bundled_cli_not_path_lookup(self):
        module = load_mcp()
        self.assertEqual(module.ambient_bin().name, "ambient")
        self.assertIn("ambient-codex", module.ambient_bin().as_posix())


if __name__ == "__main__":
    unittest.main()
