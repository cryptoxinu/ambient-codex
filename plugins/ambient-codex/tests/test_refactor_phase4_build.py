"""Phase 4 contracts for resumable build workflow policies."""

import importlib
import unittest


class BuildWorkflowTests(unittest.TestCase):
    def test_state_path_is_scoped_to_the_build_root(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        self.assertEqual(core.state_path("/tmp/build"), "/tmp/build/.ambient-build.json")

    def test_identity_is_path_order_independent_and_version_sensitive(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        args = dict(runtime_version="1", task="make", model="m", reduce_model=None,
                    raw_context_sha="x", max_files=2, max_file_bytes=3,
                    max_tokens=4, temperature=0)
        self.assertEqual(core.resume_identity(context_paths=["b", "a"], **args),
                         core.resume_identity(context_paths=["a", "b"], **args))

    def test_resume_state_normalization_is_bounded_and_immutable(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        state = {
            "version": 1,
            "task_sha": "task",
            "plan": [{"path": "keep.py"}, {"path": "drop.py"}],
            "done": {
                "keep.py": {"content": "ok", "sha256": "ignored"},
                "drop.py": {"content": "too long", "sha256": "ignored"},
                "other.py": {"content": "unplanned", "sha256": "ignored"},
            },
            "failed": [None, {"path": "keep.py", "reason": "retry"}],
        }
        digest = __import__("hashlib").sha256(b"ok").hexdigest()
        state["done"]["keep.py"]["sha256"] = digest
        state["done"]["drop.py"]["sha256"] = __import__("hashlib").sha256(
            b"too long").hexdigest()
        before = __import__("copy").deepcopy(state)

        out = core.normalize_resume_state(
            state, task_sha="task", root="/build", max_plan=1,
            max_file_bytes=2, safe_relpath=lambda path, root: path)

        self.assertEqual(state, before)
        self.assertEqual(out["plan"], [{"path": "keep.py"}])
        self.assertEqual(out["done"], {"keep.py": {"content": "ok", "sha256": digest}})
        self.assertEqual(out["failed"], [{"path": "keep.py", "reason": "retry"}])

    def test_resume_state_normalization_rejects_bad_shape_hash_and_unsafe_path(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        base = {"version": 1, "task_sha": "task", "plan": [{"path": "a.py"}],
                "done": {}, "failed": []}
        self.assertIsNone(core.normalize_resume_state(
            {"version": 2}, task_sha="task", root="/build", max_plan=1,
            max_file_bytes=10, safe_relpath=lambda path, root: path))
        bad_hash = dict(base, done={"a.py": {"content": "ok", "sha256": "bad"}})
        self.assertIsNone(core.normalize_resume_state(
            bad_hash, task_sha="task", root="/build", max_plan=1,
            max_file_bytes=10, safe_relpath=lambda path, root: path))
        with self.assertRaises(ValueError):
            core.normalize_resume_state(
                base, task_sha="task", root="/build", max_plan=1,
                max_file_bytes=10,
                safe_relpath=lambda path, root: (_ for _ in ()).throw(ValueError("unsafe")))

    def test_plan_validation_caps_paths_and_does_not_mutate_model_payload(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        proposed = [
            {"path": "safe.py", "purpose": "keep"},
            {"path": "../unsafe.py", "purpose": "reject"},
            "not-an-object",
            {"path": "later.py"},
        ]
        before = __import__("copy").deepcopy(proposed)

        plan, rejected = core.validate_plan_items(
            proposed, max_files=3, root="/build",
            safe_relpath=lambda path, root: (
                (_ for _ in ()).throw(ValueError("escape"))
                if path.startswith("../") else path))

        self.assertEqual(proposed, before)
        self.assertEqual(plan, [{"path": "safe.py", "purpose": "keep"}])
        self.assertEqual(rejected, [{"path": "../unsafe.py", "reason": "unsafe path: escape"}])

    def test_file_record_parser_keeps_complete_records_and_drops_cut_tail(self):
        core = importlib.import_module("ambient_codex.build_workflow")
        records = core.parse_file_records(
            '{"path":"a.py","content":"A"}\n'
            '{"path":"b.py","content":"B')
        self.assertEqual(records, [{"path": "a.py", "content": "A"}])
        wrapped = core.parse_file_records(
            '{"files":[{"path":"c.py","content":"C"}]}')
        self.assertEqual(wrapped, [{"path": "c.py", "content": "C"}])
