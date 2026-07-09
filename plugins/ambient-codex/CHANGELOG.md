# Changelog

All notable changes to `ambient-codex`.

## 1.7.0 - 2026-07-09

### Each install holds its own API key

Ambient Codex no longer reads another Ambient install's credential under any
circumstance. 1.6.0 offered a TTY-gated, opt-in import that read the `ambient.xyz`
keychain item and copied the secret across; that is still two installs sharing one key,
and it required reaching into a directory this plugin has no business touching.

- Removed `keychain_has`, `find_foreign_key_source`, `read_foreign_key`,
  `offer_foreign_key_import`, `LEGACY_KEYCHAIN_SERVICE`, and `LEGACY_SHARED_DIR`.
- `keychain_read()` takes no service argument, so it cannot be pointed at another item.
- `ambient-codex setup` asks for this install's own key. `doctor` reports a missing key
  plainly rather than advertising a neighbour's.
- New `AMBIENT_CODEX_API_KEY` overrides the key from the environment and takes
  precedence over `AMBIENT_API_KEY`. The latter is still honoured, because it is the
  conventional name, but EVERY Ambient install reads it — so `doctor` now emits a
  `key isolation` FAIL when the key came from the shared variable.

The suite proves the boundary rather than asserting it: every command runs with
`~/.config/ambient` and `~/.claude` at mode `000`, and the install's own delegate mode
is checked not to inherit `takeover` from the locked-out neighbour.

## 1.6.0 - 2026-07-09

### Zero-dependency MCP transport

- Codex now starts the MCP server as `python3 -u mcp/ambient_mcp.py`. `mcp/ambient_mcp_launcher.js`
  is deleted. That Node script existed only to locate `python3`, which made Node a hard runtime
  requirement of a stdlib-only plugin; Codex installed from Homebrew or the standalone build ships
  no Node, so the MCP server never started and every Ambient MCP tool was silently missing.
  Python 3.8+ is now the only runtime.
- `ambient doctor` leads with a `runtime` row that resolves `python3` by path and prints the fix
  when it is absent, since a missing interpreter otherwise surfaces only as an MCP startup timeout.
- CI gains a job that removes Node from the runner and proves the server still starts.

### Two Ambient installs can now coexist

- All mutable state moved to `~/.config/ambient-codex/` (override: `AMBIENT_CODEX_HOME`).
  Through 1.5.x this plugin wrote `~/.config/ambient/env` — byte-identical to the path the Claude
  Ambient plugin reads — and shared `usage.jsonl`, `reservations.jsonl`, `capabilities.json`,
  `cache/`, and the `ambient.xyz` keychain item with it. `ambient control mode takeover` here
  flipped Claude into takeover on its next session, and a cheap model picked here silently became
  Claude's default.
- The keychain item is now `ambient-codex`. A shared item meant `control key remove` here deleted
  the other install's key.
- `ambient link` installs `~/.local/bin/ambient-codex`, not `ambient`.
- The git hook uninstaller no longer recognises the other install's `# ambient-code audit hook v1`
  marker, so it can never delete a hook it did not install. The installed hook itself now runs
  `ambient-codex` (or the bundled CLI), never a bare `ambient` off PATH, which would have audited using
  the other install's key and usage ledger.
- The opencode provider written to the shared `~/.config/opencode/opencode.json` is keyed
  `ambient-codex` rather than `ambient`. Both installs used to share one entry, so whichever ran
  `agent` first pinned the `baseURL` and the other then sent its own key to that endpoint.
- Every copy-pasteable command in the CLI's output names `ambient-codex`. `ambient use`, `ambient mode`
  and `ambient config set` mutate state and `ambient audit` spends credit, so following the old guidance
  drove the other install.
- `doctor` probes `ambient-codex` on PATH rather than `ambient`, reports where an importable key was
  found instead of a bare "MISSING", and names a coexisting Ambient install as expected rather than
  mistaking it for this one.
- `ambient setup` offers a one-time, TTY-gated, opt-in import of another install's key so nothing
  has to be pasted twice. It copies once, never writes back, and validates the key like a pasted one.
- Fleet budget and spend cap are now per-install rather than per-billing-key.

### Native model picker

- New MCP tool `ambient_pick_model` renders a real Codex picker over `elicitation/create`, listing
  only the models serving right now. The server previously discarded the client's advertised
  capabilities at `initialize` and had no server-initiated request path, so it could not ask the
  user anything.
- Declining, cancelling, timing out, an error reply, a client without the elicitation capability,
  and headless `codex exec` all collapse to "change nothing". A model id that was not offered is
  refused rather than persisted.
- MCP `initialize` instructions now carry the delegate/takeover contract, so an agent cannot
  silently forget it is in takeover mode.

### Fixed

- `ruff check .` silently skipped the entire 12.9k-line extensionless `bin/ambient`; a planted
  unused import passed clean. `pyproject.toml` now sets `extend-include`, and CI lints it.
- The version-sync gate now covers `mcp/ambient_mcp.py`, which reports its version over the wire.

## 1.5.7 - 2026-07-09

### Fixed
- MCP now treats `PLUGIN_ROOT` as a validated hint. If Codex retains a stale
  plugin cache path after local plugin reinstall or cache cleanup, the MCP
  server falls back to the bundled plugin root beside `ambient_mcp.py` instead
  of trying to launch a missing CLI.

### Tests
- Added MCP plugin-root regression coverage for stale `PLUGIN_ROOT` fallback
  and valid `PLUGIN_ROOT` handling.

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
