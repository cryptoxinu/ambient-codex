#!/usr/bin/env python3
"""MCP stdio adapter for the Ambient Codex plugin.

The adapter intentionally delegates all Ambient behavior to the bundled CLI. It
adds only the Codex/MCP boundary: schemas, validation, subprocess isolation,
redaction, and JSON-RPC framing.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional


SERVER_NAME = "ambient-codex"
SERVER_VERSION = "1.4.0"
PROTOCOL_VERSION = "2024-11-05"
DEFAULT_TIMEOUT_SECONDS = 120
MAX_PROMPT_CHARS = 60_000
MAX_SYSTEM_CHARS = 10_000
MAX_PATHS = 25


class ToolInputError(ValueError):
    """Raised when a tool receives invalid or unsafe user arguments."""


class AmbientCommandError(RuntimeError):
    """Raised when the CLI cannot be launched."""


def plugin_root() -> Path:
    configured = os.environ.get("PLUGIN_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def ambient_bin() -> Path:
    return plugin_root() / "bin" / "ambient"


SECRET_PATTERNS = (
    re.compile(r"(AMBIENT_API_KEY\s*=\s*)[^\s]+"),
    re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bamb_[A-Za-z0-9._~+/=-]{12,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9._~+/=-]{20,}\b"),
)


def redact(text: str) -> str:
    redacted = text
    redacted = SECRET_PATTERNS[0].sub(r"\1<redacted>", redacted)
    redacted = SECRET_PATTERNS[1].sub(r"\1<redacted>", redacted)
    for pattern in SECRET_PATTERNS[2:]:
        redacted = pattern.sub("<redacted>", redacted)
    return redacted


def require_object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ToolInputError(f"{label} must be an object")
    return value


def optional_bool(args: Dict[str, Any], name: str, default: bool) -> bool:
    value = args.get(name, default)
    if not isinstance(value, bool):
        raise ToolInputError(f"{name} must be a boolean")
    return value


def optional_int(
    args: Dict[str, Any],
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    value = args.get(name, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ToolInputError(f"{name} must be an integer")
    if value < minimum or value > maximum:
        raise ToolInputError(f"{name} must be between {minimum} and {maximum}")
    return value


def optional_string(
    args: Dict[str, Any],
    name: str,
    *,
    max_chars: int,
    allow_empty: bool = False,
) -> Optional[str]:
    value = args.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ToolInputError(f"{name} must be a string")
    if not allow_empty and not value.strip():
        raise ToolInputError(f"{name} cannot be empty")
    if len(value) > max_chars:
        raise ToolInputError(f"{name} is too large for the MCP adapter")
    return value


def require_string(args: Dict[str, Any], name: str, *, max_chars: int) -> str:
    value = optional_string(args, name, max_chars=max_chars)
    if value is None:
        raise ToolInputError(f"{name} is required")
    return value


def require_choice(args: Dict[str, Any], name: str, choices: Iterable[str]) -> str:
    value = require_string(args, name, max_chars=256)
    allowed = tuple(choices)
    if value not in allowed:
        raise ToolInputError(f"{name} must be one of: {', '.join(allowed)}")
    return value


def optional_string_list(
    args: Dict[str, Any],
    name: str,
    *,
    max_items: int,
    max_chars: int,
) -> List[str]:
    value = args.get(name, [])
    if not isinstance(value, list):
        raise ToolInputError(f"{name} must be an array of strings")
    if len(value) > max_items:
        raise ToolInputError(f"{name} can include at most {max_items} items")
    output: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ToolInputError(f"{name} must contain only non-empty strings")
        if len(item) > max_chars:
            raise ToolInputError(f"{name} contains an item that is too large")
        output.append(item)
    return output


def reject_unknown(args: Dict[str, Any], allowed: Iterable[str]) -> None:
    extra = sorted(set(args) - set(allowed))
    if extra:
        raise ToolInputError(f"unknown argument(s): {', '.join(extra)}")


def tool_text(text: str, *, is_error: bool = False) -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": redact(text) or "(no output)"}],
        "isError": is_error,
    }


def run_ambient(
    args: List[str],
    *,
    input_text: Optional[str] = None,
    cwd: Optional[Path] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    command = [sys.executable, str(ambient_bin())] + args
    try:
        completed = subprocess.run(
            command,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd or plugin_root()),
            timeout=timeout_seconds,
            check=False,
        )
    except OSError as exc:
        raise AmbientCommandError(f"unable to launch ambient CLI: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(part for part in (exc.stdout or "", exc.stderr or "") if part)
        return tool_text(f"ambient command timed out after {timeout_seconds}s\n{output}", is_error=True)

    parts = [completed.stdout.strip()]
    if completed.stderr.strip():
        parts.append("[stderr]\n" + completed.stderr.strip())
    text = "\n\n".join(part for part in parts if part)
    if completed.returncode:
        return tool_text(f"ambient exited {completed.returncode}\n{text}", is_error=True)
    return tool_text(text)


def status_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, set())
    return run_ambient(["config"])


def control_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"all_models", "offline"})
    argv = ["control", "--json"]
    if optional_bool(args, "all_models", False):
        argv.append("--all-models")
    if optional_bool(args, "offline", False):
        argv.append("--offline")
    return run_ambient(argv)


def set_mode_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"state"})
    state = require_choice(args, "state", ("off", "on", "takeover"))
    return run_ambient(["control", "mode", state])


def set_model_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"model", "lane"})
    model = require_string(args, "model", max_chars=256)
    lane = require_choice(args, "lane", ("both", "chat", "code"))
    argv = ["control", "model", model]
    if lane == "chat":
        argv.append("--chat")
    elif lane == "code":
        argv.append("--code")
    return run_ambient(argv)


def set_config_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"name", "value", "unset"})
    name = require_choice(
        args,
        "name",
        ("streaming", "fallback", "fleet-budget", "spend-cap", "reference-price"),
    )
    unset = optional_bool(args, "unset", False)
    value = optional_string(args, "value", max_chars=128)
    if unset and value is not None:
        raise ToolInputError("value cannot be provided when unset=true")
    if unset:
        return run_ambient(["control", "setting", name, "--unset"])
    if value is None:
        raise ToolInputError("value is required unless unset=true")
    return run_ambient(["control", "setting", name, value])


def key_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"action"})
    action = require_choice(args, "action", ("status", "setup", "rotate", "remove"))
    return run_ambient(["control", "key", action])


def models_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"all", "json"})
    argv = ["models"]
    if optional_bool(args, "all", False):
        argv.append("--all")
    if optional_bool(args, "json", True):
        argv.append("--json")
    return run_ambient(argv)


def doctor_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, set())
    return run_ambient(["doctor"])


def usage_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"days", "json"})
    days = optional_int(args, "days", 30, minimum=1, maximum=3650)
    argv = ["usage", "--days", str(days)]
    if optional_bool(args, "json", True):
        argv.append("--json")
    return run_ambient(argv)


def ask_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"prompt", "system", "model", "max_tokens", "timeout", "json"})
    prompt = require_string(args, "prompt", max_chars=MAX_PROMPT_CHARS)
    system = optional_string(args, "system", max_chars=MAX_SYSTEM_CHARS)
    model = optional_string(args, "model", max_chars=256)
    max_tokens = args.get("max_tokens")
    if max_tokens is not None:
        optional_int(args, "max_tokens", 0, minimum=1, maximum=200_000)
    timeout_seconds = optional_int(args, "timeout", DEFAULT_TIMEOUT_SECONDS, minimum=1, maximum=3600)

    argv = ["ask", prompt, "--yes"]
    if system is not None:
        argv.extend(["--system", system])
    if model is not None:
        argv.extend(["--model", model])
    if max_tokens is not None:
        argv.extend(["--max-tokens", str(max_tokens)])
    if optional_bool(args, "json", True):
        argv.append("--json")
    return run_ambient(argv, timeout_seconds=timeout_seconds)


def audit_small_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    reject_unknown(args, {"paths", "staged", "diff", "focus", "cwd", "json", "timeout"})
    paths = optional_string_list(args, "paths", max_items=MAX_PATHS, max_chars=1000)
    staged = optional_bool(args, "staged", False)
    diff = optional_string(args, "diff", max_chars=200)
    focus = optional_string(args, "focus", max_chars=300)
    cwd_value = optional_string(args, "cwd", max_chars=4096)
    timeout_seconds = optional_int(args, "timeout", DEFAULT_TIMEOUT_SECONDS, minimum=1, maximum=3600)
    if not paths and not staged and diff is None:
        raise ToolInputError("ambient_audit_small requires paths, staged=true, or diff")

    workdir = Path(cwd_value).expanduser().resolve() if cwd_value else Path.cwd()
    if not workdir.is_dir():
        raise ToolInputError("cwd must be an existing directory")

    argv = ["audit"]
    if staged:
        argv.append("--staged")
    if diff is not None:
        argv.extend(["--diff", diff])
    argv.extend(paths)
    if focus is not None:
        argv.extend(["--focus", focus])
    if optional_bool(args, "json", True):
        argv.append("--json")
    argv.append("--yes")
    return run_ambient(argv, cwd=workdir, timeout_seconds=timeout_seconds)


TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "ambient_status": status_tool,
    "ambient_control": control_tool,
    "ambient_set_mode": set_mode_tool,
    "ambient_set_model": set_model_tool,
    "ambient_set_config": set_config_tool,
    "ambient_key": key_tool,
    "ambient_models": models_tool,
    "ambient_doctor": doctor_tool,
    "ambient_usage": usage_tool,
    "ambient_ask": ask_tool,
    "ambient_audit_small": audit_small_tool,
}


def empty_schema() -> Dict[str, Any]:
    return {"type": "object", "properties": {}, "additionalProperties": False}


def tool_schema(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema = {**schema, "required": required}
    return schema


TOOLS = [
    {
        "name": "ambient_status",
        "description": "Show local Ambient configuration, key state, model defaults, and delegate mode.",
        "inputSchema": empty_schema(),
    },
    {
        "name": "ambient_control",
        "description": "Return the Codex-native Ambient control snapshot as JSON.",
        "inputSchema": tool_schema({
            "all_models": {
                "type": "boolean",
                "description": "Include models hidden by local curation.",
            },
            "offline": {
                "type": "boolean",
                "description": "Skip catalog fetch and show only local state.",
            },
        }),
    },
    {
        "name": "ambient_set_mode",
        "description": "Set Ambient delegate mode for Codex: off, on, or takeover.",
        "inputSchema": tool_schema({
            "state": {"type": "string", "enum": ["off", "on", "takeover"]},
        }, required=["state"]),
    },
    {
        "name": "ambient_set_model",
        "description": "Set the default Ambient model for chat, code, or both lanes.",
        "inputSchema": tool_schema({
            "model": {"type": "string", "maxLength": 256},
            "lane": {"type": "string", "enum": ["both", "chat", "code"]},
        }, required=["model", "lane"]),
    },
    {
        "name": "ambient_set_config",
        "description": "Set or unset a whitelisted Ambient config knob.",
        "inputSchema": tool_schema({
            "name": {
                "type": "string",
                "enum": [
                    "streaming",
                    "fallback",
                    "fleet-budget",
                    "spend-cap",
                    "reference-price",
                ],
            },
            "value": {"type": "string", "maxLength": 128},
            "unset": {"type": "boolean"},
        }, required=["name"]),
    },
    {
        "name": "ambient_key",
        "description": "Show key status, print terminal-only setup/rotation instructions, or remove the stored key. Never accepts key material.",
        "inputSchema": tool_schema({
            "action": {"type": "string", "enum": ["status", "setup", "rotate", "remove"]},
        }, required=["action"]),
    },
    {
        "name": "ambient_models",
        "description": "List Ambient models. Defaults to serving/catalog JSON.",
        "inputSchema": tool_schema({
            "all": {"type": "boolean", "description": "Include the full catalog."},
            "json": {"type": "boolean", "description": "Return CLI JSON output."},
        }),
    },
    {
        "name": "ambient_doctor",
        "description": "Run Ambient diagnostics for key, funds, model, network, and service issues.",
        "inputSchema": empty_schema(),
    },
    {
        "name": "ambient_usage",
        "description": "Show local Ambient usage and relative savings estimates.",
        "inputSchema": tool_schema({
            "days": {"type": "integer", "minimum": 1, "maximum": 3650},
            "json": {"type": "boolean"},
        }),
    },
    {
        "name": "ambient_ask",
        "description": "Run a short one-shot Ambient ask through the CLI.",
        "inputSchema": tool_schema({
            "prompt": {"type": "string", "maxLength": MAX_PROMPT_CHARS},
            "system": {"type": "string", "maxLength": MAX_SYSTEM_CHARS},
            "model": {"type": "string", "maxLength": 256},
            "max_tokens": {"type": "integer", "minimum": 1, "maximum": 200000},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 3600},
            "json": {"type": "boolean"},
        }, required=["prompt"]),
    },
    {
        "name": "ambient_audit_small",
        "description": "Audit a small bounded path list, staged diff, or diff ref. Use shell CLI for repo audits.",
        "inputSchema": tool_schema({
            "paths": {
                "type": "array",
                "items": {"type": "string", "maxLength": 1000},
                "maxItems": MAX_PATHS,
            },
            "staged": {"type": "boolean"},
            "diff": {"type": "string", "maxLength": 200},
            "focus": {"type": "string", "maxLength": 300},
            "cwd": {"type": "string", "maxLength": 4096},
            "json": {"type": "boolean"},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 3600},
        }),
    },
]


def call_tool(name: str, arguments: Any) -> Dict[str, Any]:
    args = require_object(arguments or {}, "arguments")
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        raise ToolInputError(f"unknown Ambient tool: {name}")
    return handler(args)


def response_result(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def response_error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request_id = request.get("id")
    method = request.get("method")
    if method == "notifications/initialized":
        return None
    try:
        if method == "initialize":
            return response_result(request_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        if method == "tools/list":
            return response_result(request_id, {"tools": TOOLS})
        if method == "tools/call":
            params = require_object(request.get("params"), "params")
            name = require_string(params, "name", max_chars=128)
            arguments = params.get("arguments", {})
            return response_result(request_id, call_tool(name, arguments))
        return response_error(request_id, -32601, f"method not found: {method}")
    except ToolInputError as exc:
        return response_error(request_id, -32602, str(exc))
    except AmbientCommandError as exc:
        return response_error(request_id, -32000, str(exc))
    except Exception as exc:  # pragma: no cover - defensive JSON-RPC boundary.
        return response_error(request_id, -32000, f"ambient MCP internal error: {exc}")


def read_headers(stream) -> Optional[Dict[str, str]]:
    headers: Dict[str, str] = {}
    while True:
        line = stream.readline()
        if line == b"":
            return None if not headers else headers
        stripped = line.strip()
        if not stripped:
            return headers
        key, sep, value = stripped.decode("ascii").partition(":")
        if sep:
            headers = {**headers, key.lower(): value.strip()}


def read_message(stream) -> Optional[Dict[str, Any]]:
    headers = read_headers(stream)
    if headers is None:
        return None
    raw_length = headers.get("content-length")
    if raw_length is None:
        raise ValueError("missing Content-Length header")
    body = stream.read(int(raw_length))
    if not body:
        return None
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON-RPC message must be an object")
    return payload


def write_message(stream, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    stream.write(header + body)
    stream.flush()


def serve() -> int:
    while True:
        request = read_message(sys.stdin.buffer)
        if request is None:
            return 0
        response = handle_request(request)
        if response is not None:
            write_message(sys.stdout.buffer, response)


if __name__ == "__main__":
    try:
        raise SystemExit(serve())
    except Exception as exc:
        print(f"ambient MCP fatal error: {exc}", file=sys.stderr)
        raise SystemExit(1)
