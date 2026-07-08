# Changelog

All notable changes to `ambient-codex`.

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
