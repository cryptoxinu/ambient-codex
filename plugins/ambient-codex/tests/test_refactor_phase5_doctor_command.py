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


if __name__ == "__main__":
    unittest.main()
