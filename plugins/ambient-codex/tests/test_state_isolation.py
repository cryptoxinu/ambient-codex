"""Ambient Codex must never share mutable state with another Ambient install.

Through 1.5.x this fork wrote `~/.config/ambient/env` — the exact path the Claude
plugin reads — so `ambient control mode takeover` here flipped Claude into takeover
on its next session, and a cheap model chosen here silently became Claude's default.
`test_codex_native_isolation.py` only asserted code-path isolation, so it stayed
green the whole time. These tests assert the *state* boundary instead.
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "bin" / "ambient"


def load_cli(home):
    """Import bin/ambient with HOME/AMBIENT_CODEX_HOME pointed at a sandbox."""
    prior = {k: os.environ.get(k) for k in ("HOME", "AMBIENT_CODEX_HOME")}
    os.environ["HOME"] = home
    os.environ.pop("AMBIENT_CODEX_HOME", None)
    try:
        spec = importlib.util.spec_from_loader(
            "ambient_cli_isolation",
            importlib.machinery.SourceFileLoader("ambient_cli_isolation", str(CLI)),
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TestStateRootIsolation(unittest.TestCase):
    def test_every_state_path_lives_under_the_codex_root(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            root = os.path.join(home, ".config", "ambient-codex")
            self.assertEqual(cli.STATE_DIR, root)
            for name in ("CONFIG_PATH", "USAGE_PATH", "CAPABILITY_PATH", "CACHE_DIR"):
                path = getattr(cli, name)
                self.assertTrue(
                    path.startswith(root + os.sep),
                    f"{name}={path} escapes the Codex state root",
                )
            # reservations derive from dirname(USAGE_PATH); prove they followed.
            self.assertTrue(cli._reservations_path().startswith(root + os.sep))

    def test_no_state_path_touches_the_shared_ambient_dir(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            shared = os.path.join(home, ".config", "ambient")
            for name in ("CONFIG_PATH", "USAGE_PATH", "CAPABILITY_PATH", "CACHE_DIR"):
                path = getattr(cli, name)
                self.assertFalse(
                    path == shared or path.startswith(shared + os.sep),
                    f"{name}={path} lands inside the other install's dir {shared}",
                )

    def test_keychain_item_is_distinct_from_the_other_install(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            self.assertEqual(cli.KEYCHAIN_SERVICE, "ambient-codex")
            self.assertNotEqual(cli.KEYCHAIN_SERVICE, cli.LEGACY_KEYCHAIN_SERVICE)

    def test_state_root_is_overridable(self):
        with tempfile.TemporaryDirectory() as home:
            override = os.path.join(home, "elsewhere")
            os.environ["AMBIENT_CODEX_HOME"] = override
            try:
                spec = importlib.util.spec_from_loader(
                    "ambient_cli_override",
                    importlib.machinery.SourceFileLoader(
                        "ambient_cli_override", str(CLI)),
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.STATE_DIR, override)
                self.assertEqual(module.CONFIG_PATH, os.path.join(override, "env"))
            finally:
                os.environ.pop("AMBIENT_CODEX_HOME", None)


class TestNoWritesEscapeTheCodexRoot(unittest.TestCase):
    def test_mode_takeover_never_writes_the_shared_env(self):
        """The exact reported bug: takeover in Codex must not reach the other install."""
        with tempfile.TemporaryDirectory() as home:
            shared_dir = os.path.join(home, ".config", "ambient")
            os.makedirs(shared_dir, mode=0o700)
            shared_env = os.path.join(shared_dir, "env")
            with open(shared_env, "w", encoding="utf-8") as fh:
                fh.write("AMBIENT_DELEGATE=off\nAMBIENT_MODEL=frontier/expensive\n")
            before = Path(shared_env).read_text(encoding="utf-8")

            env = {**os.environ, "HOME": home, "AMBIENT_NO_ONBOARD": "1"}
            env.pop("AMBIENT_CODEX_HOME", None)
            proc = subprocess.run(
                [sys.executable, str(CLI), "control", "mode", "takeover"],
                env=env, capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            self.assertEqual(
                Path(shared_env).read_text(encoding="utf-8"), before,
                "Codex mutated the other Ambient install's env file")
            codex_env = Path(home) / ".config" / "ambient-codex" / "env"
            self.assertIn("AMBIENT_DELEGATE=takeover",
                          codex_env.read_text(encoding="utf-8"))

    def test_shared_dir_is_never_created_when_absent(self):
        with tempfile.TemporaryDirectory() as home:
            env = {**os.environ, "HOME": home, "AMBIENT_NO_ONBOARD": "1"}
            env.pop("AMBIENT_CODEX_HOME", None)
            proc = subprocess.run(
                [sys.executable, str(CLI), "control", "mode", "on"],
                env=env, capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertFalse(
                os.path.exists(os.path.join(home, ".config", "ambient")),
                "Codex created the other install's config dir")
            self.assertTrue(
                os.path.exists(os.path.join(home, ".config", "ambient-codex", "env")))


class TestGitHookOwnership(unittest.TestCase):
    def test_codex_never_claims_the_other_installs_hook_marker(self):
        """Uninstalling hooks from Codex must not delete the Claude install's hook."""
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            self.assertEqual(cli.AMBIENT_HOOK_MARKER, "# ambient-codex audit hook v1")
            self.assertEqual(cli.LEGACY_AMBIENT_HOOK_MARKERS, ())
            source = CLI.read_text(encoding="utf-8")
            self.assertNotIn('"# ambient-code audit hook v1"', source)


class TestPathLauncherName(unittest.TestCase):
    def test_launcher_is_not_named_ambient(self):
        """`~/.local/bin/ambient` belongs to whichever install claimed it first.

        The Claude plugin symlinks that exact name, so Codex must install its own
        launcher as `ambient-codex` rather than race for the shared one.
        """
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            self.assertEqual(cli.LAUNCHER_NAME, "ambient-codex")

    def test_link_writes_the_codex_launcher(self):
        with tempfile.TemporaryDirectory() as home:
            dest = os.path.join(home, "bin")
            env = {**os.environ, "HOME": home, "AMBIENT_NO_ONBOARD": "1"}
            env.pop("AMBIENT_CODEX_HOME", None)
            proc = subprocess.run(
                [sys.executable, str(CLI), "link", "--dir", dest],
                env=env, capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(os.path.lexists(os.path.join(dest, "ambient-codex")))
            self.assertFalse(os.path.lexists(os.path.join(dest, "ambient")),
                             "Codex claimed the shared `ambient` name on PATH")


class TestGuidanceNeverNamesTheSharedLauncher(unittest.TestCase):
    def test_no_printed_command_starts_with_a_bare_ambient(self):
        """Copy-pasteable guidance must name THIS install's launcher.

        `ambient use ...`, `ambient mode on`, and `ambient config set ...` all mutate
        state, and a bare `ambient` on PATH is the other install. `ambient audit`
        would even spend its credits.
        """
        subcommands = (
            "config", "use", "mode", "control", "curate", "trust-url", "setup",
            "models", "audit", "usage", "doctor", "link", "cache", "chat", "ask",
            "code", "build", "map", "agent",
        )
        pattern = re.compile(
            r"(?<![-\w./])ambient (?=(?:" + "|".join(subcommands) + r")\b)")
        offenders = []
        for lineno, line in enumerate(CLI.read_text(encoding="utf-8").split("\n"), 1):
            stripped = line.lstrip()
            if stripped.startswith("#") or "LAUNCHER_NAME" in line:
                continue
            if '"' not in line and "'" not in line:
                continue
            if "audit hook v1" in line:  # ownership marker, not guidance
                continue
            if "Installed by:" in line:  # 1.5.x header we still recognise on uninstall
                continue
            if pattern.search(line):
                offenders.append(f"{lineno}: {stripped[:70]}")
        self.assertEqual(offenders, [], "bare `ambient <subcommand>` in user-facing text")

    def test_the_git_hook_never_invokes_a_bare_ambient(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            for name in ("pre-commit", "pre-push"):
                body = cli._render_hook(name)
                self.assertIn("command -v ambient-codex", body)
                self.assertNotIn("command -v ambient >", body)
                self.assertIn('"$AMBIENT_BIN" audit', body)


class TestForeignKeyImportIsReadOnlyAndOptIn(unittest.TestCase):
    def test_import_is_skipped_without_a_tty(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            self.assertIsNone(cli.offer_foreign_key_import())

    def test_import_is_skipped_when_onboarding_disabled(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            prior = os.environ.get("AMBIENT_NO_ONBOARD")
            os.environ["AMBIENT_NO_ONBOARD"] = "1"
            try:
                self.assertIsNone(cli.offer_foreign_key_import())
            finally:
                if prior is None:
                    os.environ.pop("AMBIENT_NO_ONBOARD", None)
                else:
                    os.environ["AMBIENT_NO_ONBOARD"] = prior

    def test_read_foreign_key_finds_the_legacy_env_without_writing_it(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            shared_dir = os.path.join(home, ".config", "ambient")
            os.makedirs(shared_dir, mode=0o700)
            legacy = os.path.join(shared_dir, "env")
            with open(legacy, "w", encoding="utf-8") as fh:
                fh.write("AMBIENT_API_KEY=sk-legacy-value\n")
            before = Path(legacy).read_text(encoding="utf-8")
            cli.LEGACY_SHARED_DIR = shared_dir
            # NEVER touch the developer's real OS keychain from a test: the real
            # `ambient.xyz` item would be read and echoed by an assertion diff.
            with mock.patch.object(cli, "keychain_read", return_value=None):
                key, source = cli.read_foreign_key()
            self.assertTrue(key == "sk-legacy-value", "legacy env key not read")
            self.assertEqual(source, legacy)
            self.assertEqual(Path(legacy).read_text(encoding="utf-8"), before)

    def test_read_foreign_key_reads_the_legacy_keychain_service_only(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            cli.LEGACY_SHARED_DIR = os.path.join(home, ".config", "ambient")
            with mock.patch.object(cli, "keychain_read",
                                   return_value="stub") as reader:
                key, source = cli.read_foreign_key()
            reader.assert_called_once_with(cli.LEGACY_KEYCHAIN_SERVICE)
            self.assertTrue(key == "stub")
            self.assertIn(cli.LEGACY_KEYCHAIN_SERVICE, source)

    def test_presence_probe_never_reads_the_secret(self):
        """Declining the import must not have pulled the other install's key into memory.

        `security find-generic-password` WITHOUT `-w` reports the item without
        decrypting it, so this also avoids a keychain-unlock prompt.
        """
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            cli.LEGACY_SHARED_DIR = os.path.join(home, ".config", "ambient")
            with mock.patch.object(cli, "keychain_read") as reader, \
                 mock.patch.object(cli, "keychain_has", return_value=True):
                source = cli.find_foreign_key_source()
            reader.assert_not_called()
            self.assertIn(cli.LEGACY_KEYCHAIN_SERVICE, source)

    def test_keychain_presence_probe_omits_the_password_flag(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            with mock.patch.object(cli.subprocess, "run") as run, \
                 mock.patch.object(cli, "secret_backend", return_value="keychain"):
                run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
                cli.keychain_has("ambient.xyz")
            argv = run.call_args[0][0]
            self.assertIn("find-generic-password", argv)
            self.assertNotIn("-w", argv, "presence probe must not request the secret")

    def test_read_foreign_key_returns_none_when_no_other_install(self):
        with tempfile.TemporaryDirectory() as home:
            cli = load_cli(home)
            cli.LEGACY_SHARED_DIR = os.path.join(home, ".config", "ambient")
            with mock.patch.object(cli, "keychain_read", return_value=None):
                self.assertEqual(cli.read_foreign_key(), (None, None))


class TestHookScriptReadsIsolatedEnv(unittest.TestCase):
    def test_session_start_reads_the_codex_root_only(self):
        script = (ROOT / "hooks" / "session-start.sh").read_text(encoding="utf-8")
        self.assertIn('${AMBIENT_CODEX_HOME:-$HOME/.config/ambient-codex}/env', script)
        self.assertNotIn('conf="$HOME/.config/ambient/env"', script)

    def test_session_start_ignores_the_other_installs_takeover_flag(self):
        with tempfile.TemporaryDirectory() as home:
            shared_dir = os.path.join(home, ".config", "ambient")
            os.makedirs(shared_dir, mode=0o700)
            with open(os.path.join(shared_dir, "env"), "w", encoding="utf-8") as fh:
                fh.write("AMBIENT_DELEGATE=takeover\n")
            proc = subprocess.run(
                ["/bin/sh", str(ROOT / "hooks" / "session-start.sh")],
                env={**os.environ, "HOME": home, "PLUGIN_ROOT": str(ROOT)},
                capture_output=True, text=True, timeout=30, check=False)
            self.assertNotIn("TAKEOVER", proc.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
