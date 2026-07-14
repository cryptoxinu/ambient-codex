"""Phase 4 contracts for resumable build workflow policies."""

import importlib
import unittest


class BuildWorkflowTests(unittest.TestCase):
    def test_identity_is_path_order_independent_and_version_sensitive(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        args = dict(runtime_version="1", task="make", model="m", reduce_model=None,
                    raw_context_sha="x", max_files=2, max_file_bytes=3,
                    max_tokens=4, temperature=0)
        self.assertEqual(core.resume_identity(context_paths=["b", "a"], **args),
                         core.resume_identity(context_paths=["a", "b"], **args))
