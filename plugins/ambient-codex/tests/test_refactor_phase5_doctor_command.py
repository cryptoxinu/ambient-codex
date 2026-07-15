"""Phase 5 contracts for extracted health diagnostics."""

import importlib
import unittest


class DoctorCommandTests(unittest.TestCase):
    def setUp(self):
        self.core = importlib.import_module("ambient_codex.doctor_command")

    def test_check_line_keeps_stable_alignment(self):
        line = self.core.format_check_line(
            "runtime", True, "python3 -> /usr/bin/python3",
            paint=lambda text, _color: text,
        )

        self.assertEqual(
            line, "PASS  runtime        python3 -> /usr/bin/python3")

    def test_secret_safe_detail_redacts_keys_before_terminal_output(self):
        secret = "sk-live-secret-that-must-not-print"

        detail = self.core.secret_safe_detail(
            f"provider echoed {secret}", secret,
            lambda text, key: text.replace(key, "[REDACTED]"),
        )

        self.assertEqual(detail, "provider echoed [REDACTED]")
        self.assertNotIn(secret, detail)


if __name__ == "__main__":
    unittest.main()
