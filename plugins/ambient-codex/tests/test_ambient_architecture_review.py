"""Architecture boundary tests for context, repository coverage, and budgets.

These tests exercise the policy boundaries that ordinary happy-path API tests
do not: a large text file must enter the chunking lane, an unprocessable source
file must become an explicit coverage gap, and the public token ceiling must
not reject a currently advertised frontier output budget.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
BIN = HERE.parent / "bin" / "ambient"


def load_module():
    loader = importlib.machinery.SourceFileLoader(
        "ambient_architecture_review", str(BIN))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


amb = load_module()


@contextlib.contextmanager
def patched(obj, **attrs):
    missing = object()
    old = {key: getattr(obj, key, missing) for key in attrs}
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


class RepositoryCoverageTests(unittest.TestCase):
    def test_large_text_file_enters_chunking_lane(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "large.py"
            path.write_bytes(b"x\n" * 500_001)
            files, skipped, _used_git = amb.repo_walk(str(root))

        self.assertEqual([item[0] for item in files], ["large.py"])
        self.assertEqual(skipped["oversize"], 0)

    def test_oversized_source_is_an_explicit_coverage_gap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "small.py").write_text("x = 1\n", encoding="utf-8")
            (root / "too-large.py").write_bytes(b"x\n" * 80)
            args = type("Args", (), {
                "repo": str(root),
                "allow_cost": True,
                "allow_partial": False,
            })()
            with patched(amb, ABS_MAX_CHARS=100,
                         REPO_FILE_MAX_BYTES=100), \
                    contextlib.redirect_stderr(io.StringIO()):
                labeled, meta = amb.repo_audit_inputs(args, "sk-test")

        labels = {label for label, _text in labeled}
        self.assertIn("REPO COVERAGE NOTE", labels)
        self.assertEqual(meta["omitted_oversize"], 1)
        self.assertTrue(meta["coverage_gap"])


class RequestBudgetTests(unittest.TestCase):
    def test_public_budget_allows_current_frontier_output_cap(self):
        self.assertGreaterEqual(amb.MAX_REQUESTED_TOKENS, 262144)

    def test_budget_normalizer_only_clamps_above_safety_ceiling(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(amb.normalize_requested_max_tokens(262144), 262144)
            self.assertEqual(
                amb.normalize_requested_max_tokens(amb.MAX_REQUESTED_TOKENS + 1),
                amb.MAX_REQUESTED_TOKENS,
            )
        self.assertIn("capped", err.getvalue())


if __name__ == "__main__":
    unittest.main()
