# Changelog

All notable changes to `ambient-codex`.

## 1.10.0 - 2026-07-14

### Cost/savings display is off by default

- The relative savings note ("~N% cheaper than a frontier model") no longer
  appears unless you opt in with `config set savings on` (or env
  `AMBIENT_SAVINGS`). Absolute cost is never shown — no dollar or cent figure
  anywhere — because billing is plan-dependent (API vs subscription). When
  enabled, only the relative percentage shows, on receipts and in
  `ambient-codex usage`; with it off, `usage` reports calls and tokens only.

### Removed the dollar spend cap

- The per-invocation and aggregate dollar spend cap (`AMBIENT_MAX_SPEND`, the
  `spend-cap` / `fleet-budget` settings, and the `reservations.jsonl` fleet
  reservation system) has been removed. It refused runs based on an estimated
  dollar cost and surfaced a dollar figure in the settings table; since billing
  is plan-dependent, that was noise. Runs are no longer refused on estimated
  cost, and no dollar value appears in settings. Parallel fan-out (`--parallel`
  / `AMBIENT_MAX_PARALLEL`) and the raw input-size guard (`--allow-cost`) are
  unchanged.

## 1.9.0 - 2026-07-10

### Public-release hardening and large-context reliability

- Raised the CLI/MCP request guard to one million output tokens while retaining
  catalog-derived per-model output and context clamps, so current frontier models
  can use their advertised capacity without unsafe over-allocation.
- Extended repository intake to the bounded 20M-character execution ceiling and
  made oversized or aggregate-overflow exclusions force explicit partial coverage;
  unread source can no longer produce a misleading clean verdict.
- Hardened MCP framing, argument boundaries, NUL handling, audit-file bounds,
  startup error redaction, and truncated-frame rejection.
- Repaired malformed Ambient Codex entries in opencode's shared config without
  modifying foreign providers, preserving restrictive file permissions and the
  install-scoped credential boundary; agent runs now use opencode's isolated
  `--pure` mode unless the caller explicitly overrides it.
- Made reasoning-model spend estimates reserve the full completion budget,
  capped automatic reasoning budgets at 65,536 tokens, and retained
  `--allow-cost` plus explicit `--max-tokens` as deliberate power-user escapes.
- Bound resumable builds to model, reducer, context digest, generation settings,
  and runtime version; corrected unresolved `auto` model labeling in dry runs.
- Reduced the always-loaded Codex skill contract by roughly 60% while preserving
  delegation, takeover, model routing, massive-repository, and trust rules.
- Corrected public launcher, key-isolation, uninstall, privacy, and portable-path
  documentation; added a published privacy-policy link to the plugin manifest.
- Revalidated the live agent lane, large map/reduce, resumable build, takeover
  state, all serving models, clean non-serving-model failures, and key-leak guards.

## 1.8.6 - 2026-07-09

### Control-panel settings cleanup

- Removed `spend-cap` from the default Codex control panel, MCP
  `ambient_set_config` schema, and advertised `control setting` actions so regular
  users are not asked to reason about pay-per-token budget ceilings.
- Kept `spend-cap` available through lower-level `ambient-codex config` and
  `AMBIENT_MAX_SPEND` for advanced users who explicitly want a local budget
  guardrail.
- MCP now self-heals one more stale-cache case: if the running server's versioned
  cache directory was removed but the current same-version sibling install exists,
  bounded tools route through that current bundled CLI instead of failing on a
  missing path.

## 1.8.5 - 2026-07-09

### Model browsing and mode clarity

- Clarified the Codex control panel mode model: off, delegate, and takeover now
  have explicit descriptions, and audit/build/ask are presented as workflows
  rather than hidden modes.
- Added a browse-all model path to Codex-facing model menu guidance. Serving
  models stay first, while on-demand models are described as available but likely
  slower to start, not broken.
- Exposed mode options and workflow metadata in the control JSON snapshot so MCP
  and the text panel share the same control vocabulary.
- Removed stale native-picker-default and zero-Codex-token wording from docs and
  runtime messages.

## 1.8.4 - 2026-07-09

### Clearer control panel and reliable text menus

- Bare Ambient now exposes the product surface instead of only reporting state:
  model lanes, delegate/takeover mode, settings, audits, builds, ask, diagnostics,
  and usage.
- The normal `pick a model`, `change chat model`, `change code model`, and
  `change mode` flows now use deterministic numbered text menus plus direct setter
  tools. Native MCP elicitation pickers are reserved for users who explicitly ask
  for a native picker.
- `ambient-codex control` now prints the same "In Codex chat, say:" action list
  and advertises all setting knobs plus common audit/build/ask/doctor/usage
  commands.

## 1.8.3 - 2026-07-09

### Picker fallback and settings clarity

- Mode and model picker cancellations now return explicit numbered fallback menus
  instead of dead-ending with "kept current" when Codex auto-cancels elicitation.
- The mode fallback lists `off`, `on`, and `takeover` with the exact setter tool to
  call.
- The model fallback lists currently serving model ids and the exact setter tool to
  call.
- The skill now treats settings as direct-set controls: show the settings list,
  then use `ambient_set_config` with the chosen setting/value.

## 1.8.2 - 2026-07-09

### Setup control panel polish

- The post-setup panel now shows key, mode, model, and serving-model status, then
  offers the model and mode pickers only when the user asks instead of auto-firing both.
- Dismissed model and mode pickers now read as "kept your current setting" so canceling
  a picker does not look like a failure.

## 1.8.1 - 2026-07-09

### Second-auditor fixes on the 1.8.0 additions

An independent Codex audit of the 1.8.0 diff found four issues, all fixed:

- The post-setup welcome panel still printed bare `ambient audit / use / doctor / mode`
  commands (which drive a different install). All 15 are now `ambient-codex`. The gap
  existed because the guard test skipped quote-less lines, so multi-line `print("""…""")`
  continuations went unchecked — the test now scans them.
- `ambient-codex uninstall --purge` swallowed `rmtree` errors and still reported
  "Deleted all state". It now surfaces a partial failure instead of lying.
- `uninstall` re-verifies its state root is not inside another Ambient install before
  scrubbing anything (defence in depth over the import-time guard), and accepts `--dir`
  to un-link a launcher created with `link --dir`.

## 1.8.0 - 2026-07-09

### Native mode picker + control-panel onboarding

- New MCP tool `ambient_pick_mode` renders a native Codex picker for off / delegate /
  takeover, mirroring `ambient_pick_model`. Tap to choose; it persists the choice and
  falls back to a numbered menu on clients without elicitation.
- The skill now opens a control panel on bare `$ambient` and right after setup: it
  shows key/mode/model status, then offers the model and mode pickers directly, instead
  of just telling the user to type commands. Setup is not "done" until the user has seen
  the panel and can pick a model and a mode.

### `ambient-codex uninstall`

Clean offboarding that touches ONLY this install:

- Wipes the key from the `ambient-codex` keychain item and the env file.
- Removes the `ambient-codex` PATH launcher (refuses any launcher that isn't ours).
- `--purge` deletes the whole `~/.config/ambient-codex` state dir — and refuses if that
  root has been relocated onto another Ambient install's tree.
- Prints `codex plugin remove ambient-codex@ambient-codex` for the plugin itself.
- Never deletes or modifies another Ambient install's key, state, launcher, or hooks.
  Tests prove a seeded neighbour's env is byte-identical after every uninstall path.

### Clearer welcome copy

The banner and welcome no longer say "a second pair of eyes"; they now read
"open frontier models in your terminal, ~10-40x cheaper than the closed ones", and every
command shown is `ambient-codex` (a bare `ambient` would drive a different install).

## 1.7.3 - 2026-07-09

### Clearer first-run key setup

The no-key onboarding now says, everywhere it appears: get a key at
**https://app.ambient.xyz**, then run `ambient-codex setup`.

- The skill shows a verbatim First-run block with the URL and the one command, and no
  longer tells the user `control key setup`.
- `control`, `control key status`, and the MCP `ambient_key` tool all lead with the key
  console URL and the clean `ambient-codex setup` command.
- The control-panel action list offers `setup` / `setup --force` / `setup --remove`
  instead of the longer `control key ...` forms. (`control key setup` still works.)

## 1.7.2 - 2026-07-09

### Second-auditor hardening of the isolation boundary

An independent audit (Codex + an adversarial Opus pass) found the 1.7.1 boundary was
bypassable several ways. All fixed:

- **State-root guard was exact-match only.** `AMBIENT_CODEX_HOME=~/.config/ambient/cache`
  slipped past it and rooted this install's state inside the other install's tree. The
  guard now compares realpaths and rejects the override at ANY depth under
  `~/.config/ambient` or `~/.claude`.
- **The MCP server and the SessionStart hook bypassed the guard entirely.** Both read
  `$AMBIENT_CODEX_HOME/env` directly, so a hostile override surfaced the OTHER install's
  delegate/takeover mode in Codex. Both now apply the same validation and refuse a
  foreign root.
- **`AMBIENT_API_KEY` is no longer a key source.** Every Ambient install reads that name,
  so honouring it shared one key; a `setup --file` neighbour even leaked its key outright.
  Only `AMBIENT_CODEX_API_KEY` (or this install's own keychain/config) supplies the key.
  `doctor` reports the shared variable as present-and-ignored.
- **The opencode `agent` provider is re-pinned.** Its `apiKey` placeholder is
  `{env:AMBIENT_CODEX_API_KEY}` and the child inherits that variable, and an entry left
  by an older version is corrected rather than trusted.
- **`plugin_root()` no longer trusts a stale `PLUGIN_ROOT`.** A directory that merely
  looked like a plugin let a new MCP server drive an old CLI after an update; the
  manifest must now name this plugin and match its version (cachebuster tag ignored).
- The MCP trace variable is `AMBIENT_CODEX_MCP_TRACE_FILE`, and the last bare
  `ambient control mode off` in the MCP/hook copy is now `ambient-codex`.

## 1.7.1 - 2026-07-09

### `AMBIENT_CODEX_HOME` can no longer be aimed at another install

`AMBIENT_CODEX_HOME=~/.config/ambient` made this install adopt the other Ambient
install's config: it read that install's API key (`backend=file`) and rewrote its
`AMBIENT_DELEGATE`. The override exists to relocate THIS install's state, not to hijack
somebody else's.

- The conventional root `~/.config/ambient` is refused outright.
- Any override directory that already holds an `env` without our `.ambient-codex`
  marker is refused: it belongs to someone else.
- A state root we create is stamped with a `0600` `.ambient-codex` marker.
- The DEFAULT root never requires a marker, so existing 1.6.x/1.7.0 installs keep working.

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
- Codex-native `$ambient` skill instructions and `skills/ambient/agents/openai.yaml` metadata.
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
