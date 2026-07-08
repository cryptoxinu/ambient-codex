import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MCP = ROOT / "mcp" / "ambient_mcp.py"


def load_mcp():
    spec = importlib.util.spec_from_file_location("ambient_mcp", MCP)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encode_frame(payload):
    body = json.dumps(payload).encode("utf-8")
    return b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body


def decode_frames(raw):
    frames = []
    rest = raw
    while rest:
        head, sep, tail = rest.partition(b"\r\n\r\n")
        if not sep:
            break
        length = None
        for line in head.decode("ascii").splitlines():
            if line.lower().startswith("content-length:"):
                length = int(line.split(":", 1)[1].strip())
        if length is None:
            break
        body = tail[:length]
        frames.append(json.loads(body.decode("utf-8")))
        rest = tail[length:]
    return frames


class TestMcpAdapter(unittest.TestCase):
    def test_mcp_version_matches_plugin_manifest(self):
        mcp = load_mcp()
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(mcp.SERVER_VERSION, manifest["version"])

    def test_stdio_initialize_and_list_tools(self):
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        }
        tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        proc = subprocess.run(
            [sys.executable, str(MCP)],
            input=encode_frame(init) + encode_frame(tools),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8"))
        frames = decode_frames(proc.stdout)
        self.assertEqual(frames[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(frames[0]["result"]["serverInfo"]["name"], "ambient-codex")
        self.assertEqual(frames[0]["result"]["capabilities"]["tools"]["listChanged"], False)
        self.assertIn("instructions", frames[0]["result"])
        self.assertIn("bundled Ambient CLI", frames[0]["result"]["instructions"])
        names = {tool["name"] for tool in frames[1]["result"]["tools"]}
        self.assertIn("ambient_status", names)
        self.assertIn("ambient_ask", names)
        self.assertIn("ambient_control", names)
        self.assertIn("ambient_set_mode", names)
        self.assertIn("ambient_set_model", names)
        self.assertIn("ambient_set_config", names)
        self.assertIn("ambient_key", names)
        self.assertIn("ambient_self_test", names)

    def test_notifications_and_ping_are_codex_safe(self):
        mcp = load_mcp()
        self.assertIsNone(mcp.handle_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }))
        self.assertIsNone(mcp.handle_request({
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": 9, "reason": "client cancelled"},
        }))
        response = mcp.handle_request({"jsonrpc": "2.0", "id": 7, "method": "ping"})
        self.assertEqual(response, {"jsonrpc": "2.0", "id": 7, "result": {}})

    def test_empty_resource_and_prompt_lists_are_supported(self):
        mcp = load_mcp()
        resources = mcp.handle_request({"jsonrpc": "2.0", "id": 1, "method": "resources/list"})
        templates = mcp.handle_request({"jsonrpc": "2.0", "id": 2, "method": "resources/templates/list"})
        prompts = mcp.handle_request({"jsonrpc": "2.0", "id": 3, "method": "prompts/list"})
        self.assertEqual(resources["result"], {"resources": []})
        self.assertEqual(templates["result"], {"resourceTemplates": []})
        self.assertEqual(prompts["result"], {"prompts": []})

    def test_batch_requests_return_only_call_responses(self):
        mcp = load_mcp()
        response = mcp.handle_payload([
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ])
        self.assertEqual([item["id"] for item in response], [1, 2])
        self.assertIn("tools", response[1]["result"])

    def test_plugin_mcp_config_is_fast_unbuffered_and_bounded(self):
        data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        ambient = data["mcpServers"]["ambient"]
        self.assertEqual(ambient["command"], "python3")
        self.assertEqual(ambient["args"], ["-u", "mcp/ambient_mcp.py"])
        self.assertGreaterEqual(ambient["startup_timeout_sec"], 60)
        self.assertEqual(ambient["tool_timeout_sec"], 120)

    def test_self_test_is_local_bounded_and_redacted(self):
        mcp = load_mcp()
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="ambient 1.5.3\n",
            stderr="",
        )
        with mock.patch.object(mcp.subprocess, "run", return_value=completed) as run:
            result = mcp.call_tool("ambient_self_test", {})
        argv = run.call_args.args[0]
        self.assertEqual(argv[-1], "version")
        self.assertEqual(run.call_args.kwargs["timeout"], 5)
        text = result["content"][0]["text"]
        self.assertIn("ambient-codex self-test ok", text)
        self.assertNotIn("AMBIENT_API_KEY", text)

    def test_status_tool_runs_config_with_redaction(self):
        mcp = load_mcp()
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="AMBIENT_API_KEY=amb_abcdefghijklmnopqrstuvwxyz\nok\n",
            stderr="",
        )
        with mock.patch.object(mcp.subprocess, "run", return_value=completed) as run:
            result = mcp.call_tool("ambient_status", {})
        argv = run.call_args.args[0]
        self.assertEqual(argv[-1], "config")
        text = result["content"][0]["text"]
        self.assertIn("AMBIENT_API_KEY=<redacted>", text)
        self.assertNotIn("amb_abcdefghijklmnopqrstuvwxyz", text)
        self.assertFalse(result.get("isError", False))

    def test_control_tool_runs_bundled_control_json(self):
        mcp = load_mcp()
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='{"schema_version":1,"surface":"codex-native"}\n',
            stderr="",
        )
        with mock.patch.object(mcp.subprocess, "run", return_value=completed) as run:
            result = mcp.call_tool("ambient_control", {"offline": True})
        argv = run.call_args.args[0]
        self.assertEqual(argv[-3:], ["control", "--json", "--offline"])
        self.assertIn("codex-native", result["content"][0]["text"])

    def test_setters_route_through_control_subcommands(self):
        mcp = load_mcp()
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
        with mock.patch.object(mcp.subprocess, "run", return_value=completed) as run:
            mcp.call_tool("ambient_set_mode", {"state": "takeover"})
            mcp.call_tool("ambient_set_model", {"model": "z-ai/glm-5.2", "lane": "code"})
            mcp.call_tool("ambient_set_config", {"name": "fallback", "value": "on"})
            mcp.call_tool("ambient_set_config", {"name": "fallback", "unset": True})
        calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(calls[0][-3:], ["control", "mode", "takeover"])
        self.assertEqual(calls[1][-4:], ["control", "model", "z-ai/glm-5.2", "--code"])
        self.assertEqual(calls[2][-4:], ["control", "setting", "fallback", "on"])
        self.assertEqual(calls[3][-4:], ["control", "setting", "fallback", "--unset"])

    def test_setters_validate_before_subprocess(self):
        mcp = load_mcp()
        with mock.patch.object(mcp.subprocess, "run") as run:
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_set_mode", {"state": "bogus"})
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_set_model", {"model": "x", "lane": "bad"})
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_set_config", {"name": "fallback", "value": "on", "unset": True})
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_key", {"action": "add", "key": "amb_abcdefghijklmnopqrstuvwxyz"})
        run.assert_not_called()

    def test_key_tool_never_accepts_key_material(self):
        mcp = load_mcp()
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="key missing\n", stderr="")
        with mock.patch.object(mcp.subprocess, "run", return_value=completed) as run:
            mcp.call_tool("ambient_key", {"action": "status"})
            mcp.call_tool("ambient_key", {"action": "setup"})
        calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(calls[0][-3:], ["control", "key", "status"])
        self.assertEqual(calls[1][-3:], ["control", "key", "setup"])

    def test_ask_tool_rejects_huge_prompt_before_subprocess(self):
        mcp = load_mcp()
        with mock.patch.object(mcp.subprocess, "run") as run:
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_ask", {"prompt": "x" * 60001})
        run.assert_not_called()

    def test_unknown_tool_is_mcp_error(self):
        mcp = load_mcp()
        response = mcp.handle_request({
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "missing", "arguments": {}},
        })
        self.assertEqual(response["error"]["code"], -32602)
        self.assertIn("unknown Ambient tool", response["error"]["message"])

    def test_audit_small_validates_cwd(self):
        mcp = load_mcp()
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "missing")
            with self.assertRaises(mcp.ToolInputError):
                mcp.call_tool("ambient_audit_small", {
                    "paths": ["a.py"],
                    "cwd": missing,
                })


if __name__ == "__main__":
    unittest.main()
