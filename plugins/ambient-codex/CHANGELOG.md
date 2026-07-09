# Changelog

All notable changes to `ambient-codex`.

## 1.5.6 - 2026-07-08

### Fixed
- MCP stdio now supports Codex's newline-delimited JSON-RPC startup path in
  addition to standard `Content-Length` framing. The server responds using the
  same framing it receives, preventing plugin MCP startup from hanging while
  waiting for headers that Codex did not send.

### Tests
- Added direct and Node-launcher JSONL MCP startup regressions covering
  `initialize`, `notifications/initialized`, and `tools/list`.

## 1.5.5 - 2026-07-08

### Fixed
- MCP tool schemas now always include an explicit `required` array, including
  empty-input and optional-only tools, so stricter Codex tool conversion can
  register Ambient tools instead of leaving the server started but unusable.

### Tests
- Expanded the Node launcher smoke test to run the full Codex startup path:
  `initialize`, `notifications/initialized`, then `tools/list`.
- Added a schema regression test for Codex-strict MCP object schemas.

## 1.5.4 - 2026-07-08

### Fixed
- MCP startup now uses a small Node launcher that resolves Python 3 across
  macOS/Linux (`python3` or `python`) and native Windows (`py -3`, `python3`,
  or `python`) instead of hard-coding the `python3` executable name.

## 1.5.3 - 2026-07-08

### Changed

- Ported the build lane to record-framed JSONL generation: each generated file
  is parsed as an independent complete record, truncated tails are dropped and
  requeued, reasoning drafts are never mined for files, and apply idempotency now
  compares raw bytes.
- Hardened the MCP adapter for Codex's runtime handshake: notifications are now
  handled without invalid `id: null` responses, `ping` is supported, empty
  resource/prompt lists are explicit, batch messages are accepted, and tool-list
  capability metadata is concrete.
- Added opt-in `AMBIENT_MCP_TRACE_FILE` tracing for local protocol diagnostics.
  It is disabled unless the environment variable is set.

## 1.5.0 - 2026-07-08

### Added

- MCP `ambient_self_test` for local no-network startup verification.
- Compaction-safe production rebuild checklist in `docs/PRODUCTION_REBUILD_PLAN.md`.

### Changed

- MCP startup now uses unbuffered Python, a 60-second startup timeout, client
  protocol-version echoing, and server instructions for Codex.
- Public plugin installs no longer register default lifecycle hooks, avoiding
  hook trust-review prompts on clean install.
- Git audit-hook ownership now uses the native `ambient-codex audit hook v1`
  marker while still recognizing exact legacy Ambient-owned hook headers for
  safe uninstall or upgrade.
- Public docs now spell out GitHub install, local install, API key setup, and why
  Codex starts a local Python MCP process.

## 1.4.0 - 2026-07-08

### Added

- Native `ambient control` command for Codex-facing status, mode switching,
  model lane selection, API key lifecycle guidance/removal, settings, doctor,
  usage, and JSON snapshots.
- MCP control/write tools: `ambient_control`, `ambient_set_mode`,
  `ambient_set_model`, `ambient_set_config`, and `ambient_key`.
- Regression tests for Codex-native control behavior, MCP state changes, and
  key handling that never accepts secret material through tool arguments.

### Changed

- Codex skill and docs now route setup, model picking, mode changes, and settings
  through the native control surface or MCP tools first.
- The control surface remains stdlib-only and reuses the hardened config writer,
  OS secret-store handling, and model-resolution rules from the CLI engine.

## 1.3.0 - 2026-07-08

### Added

- Standalone Codex plugin manifest at `.codex-plugin/plugin.json`.
- Codex-native `$ambient` skill instructions and `agents/openai.yaml` metadata.
- Local stdio MCP server at `mcp/ambient_mcp.py` with bounded tools for status,
  models, doctor, usage, short asks, and small audits.
- Codex session-start hook using `${PLUGIN_ROOT}`.
- Root marketplace at `.agents/plugins/marketplace.json`.
- Regression tests proving Codex launcher self-heal only touches `/ambient-codex/`
  targets and leaves foreign `ambient-code`-style launchers untouched.

### Changed

- Package identity is now `ambient-codex`.
- CLI help, mode messaging, hook contracts, docs, and security notes now describe
  Codex behavior.
- Launcher ownership moved from `/ambient-code/` to `/ambient-codex/`.
- Direct `ambient codex` provider support remains a diagnostic lane until the
  current Responses API tool-payload blocker is resolved.

### Preserved

- The stdlib Ambient CLI behavior from the source baseline, including audits,
  builds, map-reduce, consensus, best-of, usage, curation, config, setup, cache,
  trust-url, opencode agent, and git audit-hook support.
- The git audit-hook marker string remains `ambient-code audit hook v1` so older
  repository hooks can still be detected and removed safely.
