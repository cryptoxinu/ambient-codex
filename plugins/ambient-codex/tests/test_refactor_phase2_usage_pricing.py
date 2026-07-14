"""Phase 2D3-a contracts for pure pricing primitives."""

import importlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "ambient"
MOVED_NAMES = ("model_pricing", "parse_reference_price")


def load_facade(home):
    prior = {name: os.environ.get(name) for name in ("HOME", "USERPROFILE")}
    os.environ.update({"HOME": str(home), "USERPROFILE": str(home)})
    try:
        loader = importlib.machinery.SourceFileLoader("ambient_phase2d3a", str(BIN))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
    finally:
        for name, value in prior.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class PricingOwnershipTests(unittest.TestCase):
    def test_module_owns_exact_exports(self):
        pricing = importlib.import_module("ambient_codex.usage_pricing")
        self.assertEqual(pricing.__all__, MOVED_NAMES)

    def test_import_is_side_effect_free_in_fresh_home(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            env = dict(os.environ)
            env.update({
                "HOME": str(home),
                "USERPROFILE": str(home),
                "PYTHONPATH": str(ROOT),
            })
            proc = subprocess.run(
                [sys.executable, "-c", "import ambient_codex.usage_pricing"],
                cwd=str(home), env=env, capture_output=True, text=True,
                timeout=60, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(list(home.iterdir()), [])


class ModelPricingTests(unittest.TestCase):
    def setUp(self):
        self.pricing = importlib.import_module("ambient_codex.usage_pricing")

    def test_priced_model_returns_pair(self):
        catalog = [{"id": "x", "pricing": {"input": 3, "output": 15}}]
        self.assertEqual(self.pricing.model_pricing(catalog, "x"), (3.0, 15.0))

    def test_string_prices_are_coerced(self):
        catalog = [{"id": "x", "pricing": {"input": "1.5", "output": "6"}}]
        self.assertEqual(self.pricing.model_pricing(catalog, "x"), (1.5, 6.0))

    def test_unpriced_and_degraded_are_none(self):
        cases = [
            ([], "x"),                                             # empty
            (None, "x"),                                          # no catalog
            ([{"id": "x"}], "x"),                                 # no pricing
            ([{"id": "x", "pricing": "nope"}], "x"),             # non-dict
            ([{"id": "x", "pricing": {"input": 0, "output": 0}}], "x"),  # all-zero
            ([{"id": "x", "pricing": {"input": -1, "output": 5}}], "x"),  # negative
            ([{"id": "x", "pricing": {"input": float("nan"),
                                       "output": 5}}], "x"),      # NaN
            ([{"id": "x", "pricing": {"input": None, "output": 5}}], "x"),  # None
            ([{"id": "x", "pricing": {"input": 5, "output": -1}}], "x"),  # out neg
            ([{"id": "x", "pricing": {"input": 5,
                                       "output": float("nan")}}], "x"),  # out NaN
            ([{"id": "x", "pricing": {"input": "abc", "output": 5}}], "x"),  # bad
            ([{"id": "y", "pricing": {"input": 3, "output": 15}}], "x"),  # miss
        ]
        for catalog, model in cases:
            with self.subTest(catalog=catalog):
                self.assertIsNone(self.pricing.model_pricing(catalog, model))

    def test_partial_zero_is_still_priced_either_side(self):
        self.assertEqual(
            self.pricing.model_pricing(
                [{"id": "x", "pricing": {"input": 0, "output": 8}}], "x"),
            (0.0, 8.0))
        self.assertEqual(
            self.pricing.model_pricing(
                [{"id": "x", "pricing": {"input": 8, "output": 0}}], "x"),
            (8.0, 0.0))

    def test_first_matching_id_wins(self):
        catalog = [
            {"id": "x", "pricing": {"input": 3, "output": 15}},
            {"id": "x", "pricing": {"input": 1, "output": 1}},
        ]
        self.assertEqual(self.pricing.model_pricing(catalog, "x"), (3.0, 15.0))


class ParseReferencePriceTests(unittest.TestCase):
    def setUp(self):
        self.pricing = importlib.import_module("ambient_codex.usage_pricing")

    def test_pair_and_blended(self):
        self.assertEqual(self.pricing.parse_reference_price("3/15"), (3.0, 15.0))
        self.assertEqual(self.pricing.parse_reference_price("10"), (10.0, 10.0))
        self.assertEqual(self.pricing.parse_reference_price(" 2 / 4 "), (2.0, 4.0))

    def test_junk_returns_none(self):
        for raw in ("", "  ", "a/b", "3/", "/3", "3/4/5", "0", "-1", "1/-1",
                    "inf", "nan", "1/nan", None, 3):
            with self.subTest(raw=raw):
                self.assertIsNone(self.pricing.parse_reference_price(raw))


class PricingFacadeTests(unittest.TestCase):
    def test_facade_wrappers_delegate(self):
        with tempfile.TemporaryDirectory() as td:
            facade = load_facade(Path(td) / "home")
            with mock.patch.object(facade._usage_pricing, "model_pricing",
                                   return_value=(1.0, 2.0)) as mp:
                self.assertEqual(facade.model_pricing(["cat"], "m"), (1.0, 2.0))
            mp.assert_called_once_with(["cat"], "m")
            with mock.patch.object(facade._usage_pricing, "parse_reference_price",
                                   return_value=(9.0, 9.0)) as pr:
                self.assertEqual(facade.parse_reference_price("9"), (9.0, 9.0))
            pr.assert_called_once_with("9")

    def test_facade_global_is_the_seam_for_downstream_callers(self):
        with tempfile.TemporaryDirectory() as td:
            facade = load_facade(Path(td) / "home")
            # usage_cost calls model_pricing() as a facade global; patching the
            # facade name must flow through to the downstream caller.
            with mock.patch.object(facade, "model_pricing",
                                   return_value=(2.0, 4.0)):
                cost, assumed = facade.usage_cost(
                    "m", {"prompt_tokens": 1_000_000,
                          "completion_tokens": 1_000_000})
            self.assertFalse(assumed)
            self.assertAlmostEqual(cost, 6.0)  # (1e6*2 + 1e6*4) / 1e6


if __name__ == "__main__":
    unittest.main()
