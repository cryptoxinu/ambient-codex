"""v1.4.0 native Codex control surface.

Covers the Codex-owned settings panel, safe mode/model/settings writes, key
offboarding, and MCP write-tool wiring. Hermetic: no live API, temp config only.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIN = os.path.join(ROOT, "bin", "ambient")


def load_module():
    loader = importlib.machinery.SourceFileLoader("ambient_cli_v29", BIN)
    spec = importlib.util.spec_from_loader("ambient_cli_v29", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


amb = load_module()


@contextlib.contextmanager
def patched(obj, **attrs):
    missing = object()
    old = {k: getattr(obj, k, missing) for k in attrs}
    for key, value in attrs.items():
        setattr(obj, key, value)
    try:
        yield
    finally:
        for key, value in old.items():
            if value is missing:
                delattr(obj, key)
            else:
                setattr(obj, key, value)


class NotATTY(io.StringIO):
    def isatty(self):
        return False


CATALOG = [
    {
        "id": "moonshotai/kimi-k2.7-code",
        "name": "Kimi K2.7 Code",
        "is_ready": True,
        "context_length": 262144,
        "max_output_length": 65536,
        "supported_features": ["reasoning", "json_mode"],
    },
    {
        "id": "z-ai/glm-5.2",
        "name": "GLM 5.2",
        "is_ready": False,
        "context_length": 202752,
        "max_output_length": 65536,
        "supported_features": ["reasoning", "json_mode"],
    },
]


class ControlCase(unittest.TestCase):
    def setUp(self):
        self._env = dict(os.environ)
        for key in list(os.environ):
            if key.startswith("AMBIENT_"):
                os.environ.pop(key, None)
        self._td = tempfile.mkdtemp()
        self._cfg = os.path.join(self._td, "env")
        self._orig_cfg = amb.CONFIG_PATH
        amb.CONFIG_PATH = self._cfg

    def tearDown(self):
        amb.CONFIG_PATH = self._orig_cfg
        shutil.rmtree(self._td, ignore_errors=True)
        os.environ.clear()
        os.environ.update(self._env)

    def parse(self, *argv):
        return amb.build_parser().parse_args(["control", *argv])

    def run_control(self, *argv):
        args = self.parse(*argv)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            amb.cmd_control(args)
        return out.getvalue(), err.getvalue()


class ControlSnapshotTests(ControlCase):
    def test_json_snapshot_is_native_redacted_and_actionable(self):
        amb.save_config_values({
            "AMBIENT_DELEGATE": "on",
            "AMBIENT_MODEL": "z-ai/glm-5.2",
            "AMBIENT_CODE_MODEL": "moonshotai/kimi-k2.7-code",
        })
        secret = "amb_abcdefghijklmnopqrstuvwxyz"
        with patched(amb, resolve_key_and_backend=lambda conf: (secret, "keychain"),
                     safe_catalog=lambda api_url, api_key: CATALOG):
            out, _ = self.run_control("--json")
        self.assertNotIn(secret, out)
        data = json.loads(out)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["surface"], "codex-native")
        self.assertEqual(data["mode"], "on")
        self.assertEqual(data["key"], {"configured": True, "backend": "keychain"})
        self.assertEqual(data["defaults"]["chat"], "z-ai/glm-5.2")
        self.assertEqual(data["models"]["serving_count"], 1)
        self.assertIn("ambient control mode on", data["actions"])
        self.assertIn("ambient control key setup", data["actions"])

    def test_text_panel_exposes_controls_without_network_requirement(self):
        amb.save_config_values({"AMBIENT_DELEGATE": "off"})
        with patched(amb, safe_catalog=lambda api_url, api_key: []):
            out, _ = self.run_control("--offline")
        self.assertIn("Ambient Codex Control", out)
        self.assertIn("API key", out)
        self.assertIn("Mode", out)
        self.assertIn("ambient control model MODEL --chat", out)


class ControlWriteTests(ControlCase):
    def test_mode_action_updates_delegate_state(self):
        out, _ = self.run_control("mode", "takeover")
        self.assertIn("Ambient Takeover: ON", out)
        self.assertEqual(amb.read_config_file().get("AMBIENT_DELEGATE"), "takeover")

    def test_model_action_can_update_only_code_lane_without_key(self):
        with patched(amb, fetch_models=lambda api_url, api_key: CATALOG):
            out, _ = self.run_control("model", "glm", "--code")
        conf = amb.read_config_file()
        self.assertIn("z-ai/glm-5.2", out)
        self.assertNotIn("AMBIENT_MODEL", conf)
        self.assertEqual(conf.get("AMBIENT_CODE_MODEL"), "z-ai/glm-5.2")

    def test_setting_action_uses_config_whitelist(self):
        out, _ = self.run_control("setting", "fallback", "on")
        self.assertIn("fallback = on", out)
        self.assertEqual(amb.read_config_file().get("AMBIENT_FALLBACK"), "on")
        out, _ = self.run_control("setting", "fallback", "--unset")
        self.assertIn("back to default", out)
        self.assertNotIn("AMBIENT_FALLBACK", amb.read_config_file())

    def test_key_setup_in_non_tty_gives_instructions_not_prompt(self):
        with patched(amb.sys, stdin=NotATTY(), stdout=io.StringIO(), stderr=io.StringIO()):
            out, _ = self.run_control("key", "setup")
        self.assertIn("ambient control key setup", out)
        self.assertIn("ambient setup", out)

    def test_key_remove_scrubs_file_and_secret_store(self):
        amb.save_config_values({
            "AMBIENT_API_KEY": "amb_abcdefghijklmnopqrstuvwxyz",
            "AMBIENT_KEY_BACKEND": "file",
        })
        with patched(amb, keychain_delete=lambda: True, keychain_read=lambda: None):
            out, _ = self.run_control("key", "remove")
        self.assertIn("Key removed", out)
        conf = amb.read_config_file()
        self.assertNotIn("AMBIENT_API_KEY", conf)
        self.assertNotIn("AMBIENT_KEY_BACKEND", conf)


class RegistryDocsContractTests(unittest.TestCase):
    def test_control_is_registered_keyless(self):
        spec = next(s for s in amb.COMMANDS if s["name"] == "control")
        self.assertIs(spec["needs_key"], False)
        self.assertEqual(spec["handler"], "cmd_control")

    def test_parser_accepts_native_control_forms(self):
        parser = amb.build_parser()
        self.assertEqual(parser.parse_args(["control"]).command, "control")
        self.assertEqual(parser.parse_args(["control", "--json"]).json, True)
        model = parser.parse_args(["control", "model", "m", "--chat"])
        self.assertEqual((model.control_action, model.model_id, model.chat),
                         ("model", "m", True))
        setting = parser.parse_args(["control", "setting", "fallback", "--unset"])
        self.assertEqual((setting.control_action, setting.name, setting.unset),
                         ("setting", "fallback", True))


if __name__ == "__main__":
    unittest.main()
