# CLI Refactor Progress Ledger

This is the living execution record for the phased refactor defined in
[CLI_REFACTOR_SCOPE.md](CLI_REFACTOR_SCOPE.md). Read both files before changing
refactor code. Update this ledger whenever phase status, decisions, discovered
bugs, verification, commits, or the next action changes.

## Non-negotiable contracts

- No big-bang rewrite; one independently revertible phase at a time.
- Do not start the next phase until the current phase is fully green and committed.
- Preserve CLI commands/flags/help, exit codes, JSON/JSONL envelopes, state,
  keychain identity, model routing, context/spend behavior, MCP's 14 tools, and
  build safety.
- Preserve Python 3.8+, stdlib-only runtime, no Node dependency, and no Claude
  runtime/config/key dependency.
- Change at most five production/test files per phase checkpoint; tracking docs
  may be updated alongside each checkpoint.
- Write regression/characterization tests before moving behavior.
- Keep runtime coverage at or above 80% and require installed-plugin plus
  cross-platform CI gates before completing every phase.
- Do not combine mechanical extraction with API, prompt, feature, or UX redesign.

## Protected baseline and rollback

- Pre-refactor commit: `8104930c529740ebdc9c86769f99920180e15d56`.
- GitHub CI baseline: run `29103164093`, fully green across lint/coverage,
  plugin/no-Node, Linux/macOS/Windows, and Python 3.8/3.10/3.12/3.13.
- Local backup root, outside the working repository:
  `/Users/z/ambient-codex-backups/pre-refactor-8104930/`.
- Full-history bundle: `ambient-codex-full-history.bundle`.
  SHA-256: `b389c8b9b5020762c3819c1fa7969f21fc9994084c964deedc1b0fbbbdcfcc6b`.
- Exact source archive: `ambient-codex-source-8104930.tar.gz`.
  SHA-256: `3e75430eea8af2bbd841ddc07d503ff1e1097c02a3d77c28008f4d4ba6954d32`.
- The bundle was verified as complete and contains the baseline `main` ref.

## Baseline quality evidence

- 1,128 tests passed locally on Python 3.11, 3.12, and 3.14.
- Runtime coverage: CLI 81%, MCP 84%, total 81%.
- Live takeover completed an error-free `ambient_ask` and returned
  `TAKEOVER-LIVE-OK`; mode was restored to `off`.
- Live current-model matrix: 47 pass, 0 fail, 1 expected skip across 16 models.
- Installed MCP initialize/list/self-test/control/live-ask passed with 14 tools.
- Offline and live stress batteries passed before the refactor.

## Phase status

| Phase | Scope | Status | Commit | Exit evidence |
|---|---|---|---|---|
| 0A | Package seam and install fixtures | Complete | `c79596d` | Local gates + committed archive green |
| 0B | CI/package gate integration | Complete | `4c8e31f` | GitHub + installed-cache gates green |
| 1A | Immutable runtime constants | Complete | `c0b5bb1` | All gates green |
| 1B | Pure record and error types | Complete | `8ec853d` | All gates green after `d7bad68` |
| 2A | State-path validation core | Complete | `2d623f5` | All gates green after `37afbe9` |
| 2B | Config, keychain, and atomic state | Complete | `edaf8b1` | All gates green after `73e71cd` |
| 2C1 | Secret detection | Complete | `b4bc6f7` | All gates green |
| 2C2 | File and stdin intake | Complete | `5f4cf9e` | All gates green after `536b345` |
| 2C3A | Repository gutters and size | Complete | `09b03b1` | All gates green after `cdde512` |
| 2C3B | Repository discovery and classification | Complete | `ae34b98` | All gates green |
| 2C3C | Repository diff/status intake | Complete | `4ba1015` | All gates green |
| 2D1 | Cache state | Complete | `0b12b10` | All gates green |
| 2D2A | Usage ledger persistence | Complete | `114966e`→`b91d26f`→fixes | All gates green; Codex-audited |
| 2D2B | Usage summary records/report | Complete | pending push | Reader extracted; Codex-audited |
| 2D3a | Pure pricing primitives (`model_pricing`, `parse_reference_price`) | Complete | `34b5958`+`ed4f314` | Extracted to `usage_pricing.py`; Codex-audited; CI green |
| 2D3b-1 | Cost math (`usage_cost`, `reference_cost`) | Complete | `7f6c5f1` | Extended `usage_pricing.py`; injected assumed-prices + coercer; CI green |
| 2D3b-2 | Savings notes (`savings_note*`) | Deferred | — | Receipt composition w/ 5 deps + `_savings_enabled` gate; move with the display/facade-reduction phase |
| 2D3c | Spend gate (`_gate_amount`, `_config_norm_spend`) | REMOVED | `5b08854` | Feature DELETED per founder 2026-07-14 — nothing to extract |
| 2D4 | Fleet reservations | REMOVED | `5b08854` | Deleted with the spend cap; concurrency (`_resolve_parallel`) is independent and survives |
| 3A | HTTP transport + catalog normalization | Complete | local checkpoint | `transport.py`; GET-only retry and facade patch seams preserved; full suite green |
| 3C-1 | Model config + catalog coercion | Complete | local checkpoint | `model_config.py`; resolution precedence and readiness parsing preserved |
| 3C-2 | Model budget primitives | Complete | local checkpoint | `model_budget.py`; structured output and context-safe sizing formulas extracted |
| 3C-3 | Model profile construction | Complete | local checkpoint | `model_profiles.py`; catalog-driven context/output/chunk profile preserves facade telemetry adapter |
| 3E | Observed token telemetry | Complete | local checkpoint | `telemetry.py`; immutable cache derivation and fail-open ledger reads preserved |
| 3 | Transport, models, and map/reduce | In progress | — | 3A + 3C-1 complete; model profiles/routing, telemetry, streaming, chunking, and orchestration remain |
| 4 | Audit and generation workflows | Pending | — | — |
| 5 | Integrations and facade reduction | Pending | — | — |

## Phase 0 checklist

- [x] Research official setuptools package inclusion/discovery guidance.
- [x] Inventory current extensionless-loader, CI, and packaging contracts.
- [x] Write characterization tests before implementation and observe RED.
- [x] Add a side-effect-free internal package marker.
- [x] Add deterministic source/plugin package bootstrap to `bin/ambient`.
- [x] Explicitly include only `ambient_codex` in setuptools metadata.
- [x] Add CI compile/lint/coverage/package-install gates for the package seam.
- [x] Make the real isolated package-install smoke pass.
- [x] Run copied-plugin and no-Node MCP smokes.
- [x] Run the complete unit suite and 80% coverage gate.
- [x] Run plugin/skill/compile/lint/archive validation.
- [x] Reinstall the cache-busted plugin and run installed MCP smoke.
- [x] Commit Phase 0 and require GitHub's full matrix to pass.

## Current implementation boundary

Phase 0A may touch these production/test files only:

1. `tests/test_refactor_phase0.py`
2. `ambient_codex/__init__.py`
3. `bin/ambient`
4. `pyproject.toml`
5. `tests/test_ambient_v21_polish.py`

Tracking-document updates are allowed in `CLI_REFACTOR_SCOPE.md` and this ledger.
No workflow function may move during Phase 0.

Phase 0B is a separate green checkpoint limited to `.github/workflows/ci.yml`
plus tracking-document updates. This keeps each checkpoint within the five-file
production/test limit while ensuring CI covers the new package only after the
source/package behavior is green.

## Decisions

- Use a conventional root-level `ambient_codex/` package and list it explicitly
  in setuptools. Avoid package auto-discovery and arbitrary package-dir mappings.
- Keep `bin/ambient` as the public extensionless executable and compatibility
  facade.
- Source and Codex-cache execution prefer the package bundled beside the script.
  Normal pip/pipx execution imports the installed site-packages copy.
- Preserve `script-files` during the refactor even though modern setuptools
  prefers entry points; changing the public executable mechanism is out of scope.
- A real package-install smoke is an explicit integration gate, not repeated in
  every ordinary unit-test invocation.
- The package-install smoke clears `PYTHONPATH`; passing therefore proves the
  installed extensionless script resolves the installed package on its own.

## Phase 0A verification

- 1,134 tests pass on Python 3.11, 3.12, and 3.14; one explicit package-install
  test is skipped in ordinary unit runs.
- The real PEP 517 package-install test passes with no runtime `PYTHONPATH`.
- Runtime coverage including the new package is 81% total: CLI 81%, MCP 84%,
  package marker 100%.
- Focused ruff, compile, JSON manifest parsing, hook shell parsing, plugin
  validation, and skill validation pass.
- Offline stress: 26 pass, 0 fail, 0 skip.
- No-Node MCP starts with a Python-only PATH and lists exactly 14 tools.
- The installed-cache check remains pending; it requires the cache-busted
  reinstall after Phase 0B is committed.
- A clean `git archive` of `c79596d` contains the internal package and passes
  source loading plus isolated-venv installation; no cache artifact is present.
- GitHub Actions run `29104722339` passed all 18 jobs: 12 runtime OS/Python
  combinations, three cross-platform package installs, lint/81% coverage,
  plugin validation, and no-Node MCP startup.
- Cache-busted install `1.9.0+codex.20260710154546` contains the package and
  passes plugin validation, CLI version/control, MCP initialize/list/self-test/
  control with 14 tools, and installed MCP startup on a Python-only PATH.
- The source manifest was restored to release version `1.9.0` after reinstall;
  the source tree remained clean and matched `origin/main`.

## Findings and bugs

- “No-Node MCP passed” is a success label: the server starts with a PATH that has
  Python and no Node. It protects against the removed historical Node launcher.
- The first Phase 0 package-install RED run used `--no-build-isolation` and found
  the current Python environment did not provide `setuptools.build_meta`. This is
  a test-harness/environment issue, not an Ambient runtime failure. Exercising the
  declared PEP 517 build isolation as an installer actually does passed.
- The first characterization snapshot expected “unrecognized command,” while
  argparse's real stable wording is “invalid choice.” The test was corrected
  before implementation.
- The first complete-suite run found two launcher self-heal failures. Their fake
  cache install copied only the historical standalone `bin/ambient`; after the
  package seam, the hidden `ambient link` process correctly failed because that
  fake install omitted `ambient_codex`. Phase 0A now makes the fixture mirror a
  real plugin root by copying both the executable and package. CI wiring moved to
  Phase 0B so the five-file checkpoint boundary remains explicit.
- Phase 0B uses a dedicated Python 3.12 package matrix on Linux, macOS, and
  Windows instead of checking package installation only on Ubuntu. The normal
  runtime matrix still covers Python 3.8/3.10/3.12/3.13 on all three platforms.
- The no-Node CI assertion now asks the Python-only environment whether `node`
  is resolvable. The previous `env ... sh -c` probe could fail because `sh`
  itself was intentionally absent, producing the right job result for the wrong
  immediate reason before the real MCP startup check.

## Phase 1A plan — immutable runtime constants

Purpose: create the first real acyclic implementation boundary while preserving
every facade symbol and all runtime behavior. This checkpoint moves only literal,
immutable values and compiled terminal-sanitization patterns.

Production/test file boundary (five files):

1. `tests/test_refactor_phase1_constants.py` — RED-first ownership, snapshot,
   side-effect, and facade-compatibility tests.
2. `ambient_codex/constants.py` — stdlib-only immutable constants; imports only
   `re`, performs no environment, filesystem, network, or state access.
3. `bin/ambient` — imports and re-exports the moved names; all existing command
   functions continue resolving the facade globals so direct test patching works.
4. `.github/workflows/ci.yml` — compile every internal package module instead of
   naming only `__init__.py`, and load the test hermeticity package guard.
5. `tests/test_ambient_v5_fleet_hardening.py` — package-qualify its sole
   cross-test-module import so guarded discovery works.

Move in Phase 1A:

- State/key/launcher names and public URLs, but not `STATE_DIR`, paths derived
  from it, `FOREIGN_STATE_DIRS`, or any state helper.
- Exit codes and terminal ANSI/control compiled patterns.
- Default model, timeout, output, stream, context, reasoning, and chunk limits.
- Telemetry numeric bounds, but not mutable telemetry caches.
- Repo-map budgets and immutable skip/lockfile sets.

Explicitly defer:

- `__version__`, prompts/schemas, catalog/model-note dictionaries, environment-
  derived values, filesystem paths, mutable caches/holders, and every function.
- Dataclasses/named tuples and model metadata to Phase 1B after 1A is green.

RED/compatibility contract:

- The internal module owns the exact expected export set and imports without
  creating files or reading Ambient state.
- Representative values, regex patterns/flags, frozenset types, and derived
  equalities match the pre-move facade contract.
- `bin/ambient` still exposes every moved name with equal values and no duplicate
  module-level assignments.
- Source, copied-plugin, isolated-venv, archive, no-Node MCP, coverage, and the
  full OS/Python CI matrix remain required before Phase 1A closes.

## Phase 1A verification

- RED observed: all five initial constants tests failed because the internal
  module did not exist; the test-discovery guard test then failed before the CI
  runner was corrected.
- 51 moved names are type-and-value equivalent to the pre-extraction `c79596d`
  facade, including regex patterns/flags and immutable set contents.
- 1,140 guarded tests pass concurrently in the same checkout on Python 3.11,
  3.12, and 3.14; one package-install test remains an explicit opt-in gate.
- Runtime coverage remains 81% total: facade 81%, MCP 84%, internal package
  modules 100%.
- Isolated-venv installation, recursive package compilation, full ruff, plugin
  and skill validators, offline stress (26/26), and no-Node MCP (14 tools) pass.
- A clean archive of the committed Phase 1A tree passes recursive compile, all
  1,140 guarded tests, and isolated-venv installation. Installed-cache and
  GitHub cross-platform gates remain pending.
- Canonical local test commands were synchronized in bounded follow-up commits
  `a267f7b` and `637db65`; no documented gate bypasses `tests/__init__.py` now.
- GitHub Actions run `29106204600` passed all 18 runtime, package, quality,
  plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710160907` contains the constants module
  and passes facade import, plugin validation, MCP initialize/list/self-test/
  control with 14 tools, and no-Node installed MCP startup.
- The source manifest was restored to `1.9.0`; source `HEAD` and `origin/main`
  matched with a clean worktree after installed-cache verification.

## Phase 1A findings

- The canonical `unittest discover -s tests` command treated test modules as
  top-level modules and never imported `tests/__init__.py`. Its telemetry/fleet
  hermeticity guard therefore did not run in CI or the documented local gate.
- Under three simultaneous suites, v18/v19 spend tests wrote process reservations
  to the real Ambient Codex fleet ledger and correctly saw the other test PIDs as
  siblings, causing spend-gate failures. Guarded discovery (`-s tests -t .`)
  disables non-fleet-test reservations as intended; the same three-way run is
  now green and the real reservation ledger is empty after cleanup.
- Guarded discovery exposed one stale top-level fixture import in the v5 fleet
  tests. It was the only `from test_*` occurrence and is now package-qualified.
- `DEFAULT_MAX_TOKENS` is a compatibility-only facade symbol. It remains an
  explicit same-name re-export even though current runtime code does not read it.

## Phase 1B plan — pure record and error types

Purpose: move only dependency-free types that can sit directly above constants
without changing method resolution, test patching, or runtime effects.

Production/test file boundary (four files):

1. `tests/test_refactor_phase1_records.py` — RED-first ownership, field/default,
   error-payload, side-effect, and facade-compatibility tests.
2. `ambient_codex/records.py` — stdlib-only `ModelProfile`, `NetworkError`,
   `ChatError`, and `StallError`; no facade imports or effects.
3. `bin/ambient` — imports/re-exports those four types and removes duplicate
   definitions while existing functions continue resolving facade globals.

Explicitly defer:

- `Session`: its catalog method depends on facade-owned `safe_catalog`, locking,
  and a weak cache, so it belongs with the transport/models extraction.
- `RequestSpec`: its output-budget method depends on facade model-sizing helpers;
  moving it now would reverse the dependency direction or break monkeypatching.
- `AttemptState`: it contains `RequestSpec` and a mutable messages list despite a
  frozen outer dataclass; move it with `RequestSpec` after that boundary is ready.
- Mutable model-note/schema/config dictionaries; Phase 1 does not disguise
  mutable global data as immutable metadata.

RED/compatibility contract:

- Exact `ModelProfile` fields/default construction and tuple semantics remain.
- Error inheritance, string value, categories, partial/reasoning text, and
  hard-wall flags remain byte-equivalent.
- The facade exposes the same class objects with patchable bindings and owns no
  duplicate assignments/class definitions.
- Importing `ambient_codex.records` performs no state, environment, filesystem,
  keychain, or network work.

## Phase 1B verification

- RED observed: all six ownership/behavior tests failed because
  `ambient_codex.records` did not exist.
- The internal module owns exactly four exports; the facade re-exports the same
  class objects and retains independently patchable bindings.
- `ModelProfile` fields/tuple behavior and all error payload/default contracts
  match the pre-move facade behavior.
- 1,146 guarded tests pass on Python 3.11, 3.12, and 3.14.
- Runtime coverage remains 81% total; `records.py` is 100% covered.
- Isolated-venv installation, recursive compile, full ruff, plugin/skill
  validators, offline stress (26/26), and no-Node MCP (14 tools) pass.
- A clean archive of `8ec853d` passes all guarded tests and isolated-venv
  installation with both internal modules present.

## Phase 1B CI finding

- GitHub run `29106709125` passed 17 of 18 jobs. macOS Python 3.8 alone failed
  the existing two-second prose-regex ReDoS performance assertion.
- Profiling showed `_PROSE_SEVERITY_HINT_RE` consumed nearly all scan time on a
  500 KB severity-only line even though the function had already computed that
  no location existed. That pattern requires a location and therefore could
  never match this input.
- The pattern now runs only when the existing `has_loc` precheck is true. This
  preserves finding semantics and reduces the adversarial local case from about
  0.52 seconds to 0.035 seconds without increasing the test threshold.
- All 68 prose-recovery tests and the complete guarded suite pass after the fix
  on Python 3.11, 3.12, and 3.14.
- Replacement GitHub run `29106971726` passed all 18 jobs, including macOS
  Python 3.8 and the unchanged two-second ReDoS assertion.
- Cache-busted install `1.9.0+codex.20260710162209` passes record/facade class
  identity, adversarial prose timing (0.055 seconds locally), plugin validation,
  MCP initialize/list/self-test with 14 tools, and no-Node startup.
- The source manifest was restored to `1.9.0`; source `HEAD` and `origin/main`
  matched with a clean worktree after installed-cache verification.

## Phase 2 program — state, safety, and spend

Phase 2 is split so each effect boundary can be reviewed and reverted on its own:

- 2A: extract pure path normalization/containment/state-root checks behind
  facade wrappers that preserve `SystemExit` text and patchable dependencies.
- 2B: extract config/keychain/state persistence behind explicit filesystem and
  subprocess adapters; preserve ownership, permissions, and atomic writes.
- 2C: extract secret scanning, bounded readers, build-path validation, and
  repository intake safety without moving audit orchestration.
- 2D: extract usage/cache/spend/fleet persistence and locking; preserve pricing,
  reservation, concurrent-write, and receipt contracts.

No Phase 2 checkpoint may import transport, models, map/reduce, audit,
generation, integration, or CLI modules.

## Phase 2A plan — state-path validation core

Production/test file boundary (four files):

1. `tests/test_refactor_phase2_state_paths.py` — RED-first normalization,
   symlink/drive containment, foreign-root, error-text, side-effect, and facade
   patchability contracts.
2. `ambient_codex/state.py` — pure path/root validation functions accepting
   roots, marker, and environment-name values explicitly; imports only `os`.
3. `bin/ambient` — thin compatibility wrappers retain facade globals and map a
   returned validation error to the existing `sys.exit` behavior.
4. `tests/test_state_isolation.py` — update its exact source-reference count for
   the definition plus two refusal-only facade adapters.

Move in 2A:

- `_resolve` and `_is_within` implementation.
- Foreign-root selection over an explicitly supplied immutable root sequence.
- Existing-config/ownership-marker validation and exact user-facing errors.

Explicitly defer all environment reads, directory/file creation, keychain work,
config parsing/writes, permissions, locks, mutable paths, and purge behavior to
2B. The internal state module performs no I/O beyond read-only path/existence
queries supplied by the standard `os` module.

## Phase 2A verification

- RED observed: eight internal/facade tests failed because `ambient_codex.state`
  did not exist; the existing source-reference assertion then failed on the new
  third refusal-only adapter.
- Pre/post comparison against `d7bad68` proves path normalization, containment,
  foreign-root selection, and exact refusal text are equivalent.
- 1,155 guarded tests pass on Python 3.11, 3.12, and 3.14.
- Runtime coverage remains 81% total; `state.py` is 100% covered.
- State-isolation tests, isolated-venv install, recursive compile, full ruff,
  plugin/skill validators, offline stress (26/26), and no-Node MCP (14 tools)
  pass.
- Facade wrappers still read patchable `FOREIGN_STATE_DIRS`; the internal module
  imports without creating state or reading the environment.
- A clean archive of `2d623f5` passes all guarded tests and isolated-venv
  installation with `state.py` present.

## Phase 2A CI finding

- GitHub run `29107572182` passed every Linux/macOS runtime, package-install,
  quality, plugin, and no-Node job; all four Windows runtime jobs failed the
  same new `resolve` contract assertion.
- The implementation correctly preserves the pre-extraction
  `normcase(realpath(abspath(expanduser(path))))` behavior. On Windows,
  `normcase` lowercases case-insensitive paths, while the test's expected value
  used raw `realpath` and retained display casing.
- The test now compares against `normcase(realpath(...))`. Production behavior
  and containment security semantics are unchanged; the complete matrix must
  pass on the corrective commit before installation.
- After the correction, all 1,155 guarded tests pass on local Python 3.11,
  3.12, and 3.14; pinned coverage remains 81% total with `state.py` at 100%.
  Full ruff, isolated installation, recursive compile, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) also pass.
- Corrective commit `37afbe9` passes clean-archive compile, all 1,155 guarded
  tests, and isolated installation. Replacement GitHub run `29108136134`
  passes all 18 jobs, including Windows Python 3.8/3.10/3.12/3.13.
- Cache-busted install `1.9.0+codex.20260710164110` contains `state.py` and
  passes installed facade/internal equivalence, foreign-root refusal, plugin
  validation, MCP initialize/list/self-test/offline-control with 14 tools, and
  no-Node startup. The source manifest is restored to `1.9.0`; source `HEAD`
  and `origin/main` match with a clean worktree.

## Phase 2B program — credentials and config persistence

Phase 2B is divided into three independently reviewable checkpoints so secret
process boundaries are never mixed with file parsing or lock/rename behavior:

- 2B1: credential backend detection, OS keychain/libsecret operations, and key
  precedence policy.
- 2B2: owner/type/permission-safe config reading and defensive env-line parsing.
- 2B3: state-root claiming, private-directory healing, cross-platform config
  locking, and atomic merge-preserving config writes.

Every internal function receives paths, environment values, service/account
names, or process adapters explicitly. Modules may use the standard library but
must not import the facade, read state, inspect the environment, invoke a secret
store, or create files at import time. Facade wrappers remain where existing
tests and integrations patch facade globals.

## Phase 2B1 plan — credential boundary

Production/test file boundary (four files):

1. `tests/test_refactor_phase2_credentials.py` — RED-first ownership, backend
   routing, argv/stdin secret safety, timeout/failure, delete, precedence,
   side-effect, and facade-patchability contracts.
2. `ambient_codex/credentials.py` — credential backend selection and operations
   over explicit platform, executable lookup, subprocess runner, service,
   account, environment-key, and config inputs.
3. `bin/ambient` — thin compatibility wrappers preserve current function names,
   constants, facade monkeypatch points, exact return values, and key precedence.
4. `tests/test_state_isolation.py` — retarget its secret-store service/command
   source-ownership assertion to `ambient_codex/credentials.py` while retaining
   facade signature, cross-install refusal, and patchability coverage.

Move in 2B1:

- `secret_backend`, `keychain_available`, `keychain_read`, `keychain_write`, and
  `keychain_delete` decision/command construction.
- `shared_key_env_is_set` and `resolve_key_and_backend` policy, including the
  deliberate refusal to consult the cross-install `AMBIENT_API_KEY` variable.

Explicitly defer config-file reads/writes and setup/onboarding orchestration.
2B1 does not validate key syntax, contact Ambient, mutate config, or alter user
messages. Existing security tests must continue proving that secrets travel over
stdin and never process argv.

## Phase 2B1 verification

- RED observed: six direct internal imports errored, the import-side-effect
  subprocess failed, and two source-ownership checks errored because
  `ambient_codex.credentials` did not exist. The facade-only compatibility test
  remained green, proving the failure was isolated to the planned ownership move.
- Review-driven RED checks then proved an arbitrary backend string was treated
  as available and malformed macOS `security -i` stream fields/carriage returns
  were not rejected at the new internal boundary. The adapter now accepts only
  `keychain`/`secret-tool`, requires non-empty string keys, and rejects command-
  stream metacharacters before spawning a process. Public valid-key behavior is
  unchanged because facade service/account values are fixed constants.
- Pre/post comparison against `1a2eb16` proves exact facade behavior across 15
  macOS Keychain, Linux libsecret, unsupported-platform, read/write/delete, and
  env/keychain/file precedence scenarios.
- All 1,163 guarded tests pass on Python 3.11, 3.12, and 3.14. Runtime coverage
  is 82% total and `credentials.py` is 100% covered.
- Full ruff/compile, isolated-venv installation, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) pass.
- A clean archive of commit `6945b87` passes recursive compile, all 1,163
  guarded tests, and isolated installation. GitHub run `29109055056` passes all
  18 runtime, package, quality, plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710165823` passes credential module
  ownership, facade signature/patchability, malformed command-stream refusal,
  namespaced-key precedence, plugin validation, MCP initialize/list/self-test/
  offline-control with 14 tools, and no-Node startup. The source manifest is
  restored to `1.9.0`; source `HEAD` and `origin/main` match cleanly.

## Phase 2B2 plan — safe config reads

Production/test file boundary (three files):

1. `tests/test_refactor_phase2_config_read.py` — RED-first parser, duplicate,
   file-type, ownership, POSIX permission-heal, Windows no-op, invalid UTF-8,
   read-error, import-side-effect, and facade-path/stream contracts.
2. `ambient_codex/config_store.py` — defensive env-line parsing plus config
   reads over an explicit path, launcher name, stderr stream, and platform
   name; standard-library filesystem calls occur only when invoked.
3. `bin/ambient` — a thin `read_config_file()` wrapper supplies patchable
   `CONFIG_PATH`, `LAUNCHER_NAME`, `sys.stderr`, and `os.name` values.

Move in 2B2:

- Env-line parsing semantics: trim whitespace, ignore comments/bare lines,
  split on the first `=`, trim key/value, and keep the last duplicate.
- Existing `lstat` regular-file and POSIX owner checks, owner-only permission
  healing/reporting, UTF-8 corruption fallback, and read-error diagnostics.

Explicitly defer all directory creation, state marker writes, locks, temp files,
fsync/replace, and config mutation to 2B3. The facade retains a zero-argument,
independently patchable `read_config_file` binding, and all user-facing messages
must remain byte-equivalent for existing inputs.

## Phase 2B2 verification

- RED observed: eight direct internal tests errored and the import-side-effect
  subprocess failed because `ambient_codex.config_store` did not exist. The
  facade-only zero-argument/path/platform test stayed green, isolating RED to
  the planned ownership move.
- Pre/post comparison against `ebc767f` proves exact config dictionaries,
  diagnostics, and permission results across seven regular, Windows-mode,
  corrupt, missing, symlink, read-error, and foreign-owner scenarios.
- All 1,173 guarded tests pass on Python 3.11, 3.12, and 3.14. Runtime coverage
  is 82% total; `config_store.py` and every earlier internal module are 100%.
- Full ruff/compile, isolated-venv installation, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) pass.
- A clean archive of commit `997cb27` passes recursive compile, all 1,173
  guarded tests, and isolated installation. GitHub run `29109890376` passes all
  18 runtime, package, quality, plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710171044` passes parser semantics,
  POSIX permission healing, symlink refusal, Windows behavior, facade path/
  platform patchability, plugin validation, MCP initialize/list/self-test/
  offline-control with 14 tools, and no-Node startup. The source manifest is
  restored to `1.9.0`; source `HEAD` and `origin/main` match cleanly.

## Phase 2B3 plan — locked atomic config writes

Production/test file boundary (four files):

1. `tests/test_refactor_phase2_config_write.py` — RED-first state-marker,
   private-directory, POSIX flock, fallback O_EXCL/stale/timeout, merge/delete/
   duplicate, callable freshness, atomic replace, permissions, cleanup,
   side-effect, and facade-patchability contracts.
2. `ambient_codex/config_store.py` — extend the existing lower-layer module with
   explicit state claiming, private-directory healing, a cross-platform lock
   context, and atomic merge-preserving writes.
3. `bin/ambient` — thin `_claim_state_dir`, `_config_lock`, `_private_dir`, and
   `save_config_values` wrappers bind patchable state/config paths, version,
   `fcntl`, clocks, subprocess-independent filesystem primitives, and `sys.exit`.
4. `tests/test_refactor_phase2_config_read.py` — extend its module ownership
   tuple now that the same lower-layer store intentionally owns read and write
   APIs; all Phase 2B2 read contracts remain unchanged.

Move in 2B3:

- Marker creation for this install only, with existing best-effort behavior and
  owner-only permissions.
- Owner-only directory creation/healing used by state/cache/usage surfaces.
- POSIX `flock` and Windows/portable O_EXCL locking, including stale-lock break,
  bounded wait, ownership-token write, fail-closed timeout, and cleanup.
- Fresh-under-lock callable updates, managed-key dedup/delete, fsync of a unique
  owner-only temp file, atomic replace, destination permission enforcement, and
  temp cleanup on failures.

No transport, model, spend, cache-entry, usage-ledger, build-state, or OpenCode
write path moves in this checkpoint. Existing public wrappers retain their
signatures and all failure text; no lock path may enter a critical section after
timeout or lock-open failure.

## Phase 2B3 verification

- RED observed: eight direct write/lock tests errored because the planned APIs
  were absent and the export-set assertion failed; import purity and the existing
  facade write flow remained green.
- The first complete suite then failed only the Phase 2B2 exact-export assertion,
  which still named the read-only API set. The 2B3 boundary was expanded from
  three to four files before updating that ownership contract.
- Review-driven RED tests exposed raw lock-acquisition/config-read errors and
  destination permission enforcement occurring after lock release in the first
  extraction draft. Lock/open/temp/read failures now produce bounded user-facing
  errors, a broken abort callback still cannot enter the critical section, and
  destination `0600` enforcement occurs before unlock.
- Pre/post comparison against `367a3cf` proves valid facade behavior for marker
  content, private-directory/file modes, duplicate/delete/callable merges, and
  POSIX/portable lock cleanup. A 24-writer concurrent stress preserves every
  independent key without leaving a lock or temp artifact.
- All 1,190 guarded tests pass on Python 3.11, 3.12, and 3.14. Runtime coverage
  remains 82% total; `config_store.py` is 98% covered, with only nested cleanup-
  failure handlers unexecuted.
- Full ruff/compile, isolated-venv installation, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) pass.
- A clean archive of commit `edaf8b1` passes recursive compile, all 1,190
  guarded tests, and isolated installation. GitHub run `29110930210` passes all
  18 runtime, package, quality, plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710172757` passes marker/private-mode
  behavior, callable and fallback-lock writes, real 24-writer concurrency,
  lock/temp cleanup, plugin validation, MCP initialize/list/self-test/offline-
  control with 14 tools, and no-Node startup. The source manifest is restored
  to `1.9.0`; source `HEAD` and `origin/main` match cleanly.

### Phase 2B3 Windows contention follow-up

GitHub run `29111937821` exposed an intermittent Windows 3.10 failure in the
24-writer portable-lock stress: opening an already-existing `.env.lock` returned
`PermissionError` (Windows sharing violation semantics) instead of
`FileExistsError`. The lock failed closed, so no unlocked write occurred, but a
normal contention event aborted one writer and failed the batch.

- Deterministic RED reproduces `PermissionError` while the lock path exists,
  releases the competing lock during the bounded wait, and requires the writer
  to acquire on its second attempt.
- Portable locking now classifies `FileExistsError`, plus `PermissionError` only
  while the lock path still exists, as contention. Permission failures without
  an extant lock remain immediate user-facing errors; ownership-token write
  failures still clean up and fail closed.
- Stale-lock, ten-second timeout, unreadable-metadata, broken-abort, cleanup,
  and 24-writer preservation contracts remain in the same test surface.
- All 1,215 guarded tests, full ruff/compile, and 20 forced portable-lock runs
  of 48 concurrent writers (960 writes total) pass locally. GitHub run
  `29112620337` also passes all 18 jobs at the preceding intake commit, including
  Windows 3.10. Replacement run `29112858149`, which contains the deterministic
  race fix, passes all 18 jobs across Linux, macOS, Windows, Python 3.8/3.10/
  3.12/3.13, coverage, packaging, plugin, and no-Node gates.

## Phase 2C program — input, secret, and repository safety

Phase 2C is split into four bounded checkpoints:

- 2C1: pure credential/secret detection and location enumeration.
- 2C2: bounded stdin, explicit-file, and map-item text intake.
- 2C3: git/plain repository candidate discovery, containment, binary/size
  classification, gutter sizing, and diff intake.
- 2C4: generated/build path validation and safe record parsing, coordinated
  with Phase 4 if generation-layer dependencies make an earlier move acyclically
  incorrect.

No Phase 2C module may import transport, model routing, spend, audit orchestration,
generation, integrations, MCP, or the facade. System exits and user-facing
command categories remain facade responsibilities; lower layers return bounded
data, explicit errors, or immutable findings.

## Phase 2C1 plan — pure secret tripwire

Production/test file boundary (three files):

1. `tests/test_refactor_phase2_secrets.py` — RED-first export, precise/loose,
   assignment/reference, filename, layered-gutter location, long-line runtime,
   side-effect, and facade-equivalence contracts.
2. `ambient_codex/secrets.py` — secret regexes plus pure identifier/value/line
   classification and immutable hit enumeration; imports only `os`, `re`, and
   the scan-bound constant.
3. `bin/ambient` — compatibility aliases/wrappers retain `_env_is_strong`,
   `_value_looks_nonsecret`, `_env_assignment_is_secret`, `_line_has_secret`,
   `SECRET_NAMES_RE`, and `refuse_if_secrets`; only the facade maps hits to the
   existing `_fail_exit` message/category.

Move in 2C1:

- All regex construction and pure classification from the loose/precise secret
  pattern block through URL-credential scanning.
- Credential-named-file checks, absolute line extraction, repeated gutter
  stripping, first-20 location bounding, and hit enumeration.

Preserve the current documented false-positive boundary and every existing
tripwire corpus result. Do not combine this mechanical ownership move with new
detection heuristics; review-driven hardening requires a separate RED example.

## Phase 2C1 verification

- RED observed: four direct internal tests errored and import purity failed
  because `ambient_codex.secrets` did not exist. The new facade assertion also
  caught and corrected its own singular `secret` expectation to the existing
  `secrets` error category before implementation.
- The regex corpus was moved mechanically; facade compatibility aliases retain
  prior symbols while only immutable hit enumeration is new. The facade still
  owns `_fail_exit`, command categorization, and the exact refusal message.
- All 49 historical tripwire corpus tests and six new ownership/location/
  performance contracts pass. `secrets.py` is 95% covered.
- All 1,196 guarded tests pass on Python 3.11, 3.12, and 3.14. Full ruff/compile,
  isolated-venv installation, plugin/skill validators, offline stress (26/26),
  and no-Node MCP startup (14 tools) pass.
- A clean archive of commit `b4bc6f7` passes recursive compile, all 1,196
  guarded tests, and isolated installation. GitHub run `29111557343` passes all
  18 runtime, package, quality, plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710173832` passes direct secret-module
  imports, true/false detection, credential filename and layered-gutter
  locations, a one-million-character benign-line bound, facade aliases/refusal,
  plugin validation, MCP initialize/list/self-test/offline-control with 14 tools,
  and no-Node startup. The source manifest is restored to `1.9.0`; source
  `HEAD` and `origin/main` match cleanly.

## Phase 2C2 program — bounded text intake

Phase 2C2 is split into two independently releasable checkpoints so filesystem
descriptor safety and cross-platform stdin liveness never share one review:

- 2C2A: explicit batch-file and one-map-item reads.
- 2C2B: piped stdin readiness, bounded reading/decoding, and ignored-input
  detection.

Both checkpoints preserve facade-level names and patch points. The lower layer
receives limits and environment/runtime dependencies explicitly, returns
immutable data or explicit failures, and has no import-time filesystem, stream,
thread, environment, or terminal effects. Map gathering/JSONL parsing stays in
the facade until its per-item orchestration phase; repository discovery stays in
2C3.

## Phase 2C2A plan — explicit file intake

Production/test file boundary (three files):

1. `tests/test_refactor_phase2_intake_files.py` — RED-first exact exports,
   import purity, regular/symlink/directory/FIFO, missing/unreadable, empty,
   binary, UTF-8 replacement, multibyte cap, cumulative cap, map per-item error,
   facade message/category, and compatibility-patch contracts.
2. `ambient_codex/intake.py` — bounded regular-file reads for batch and map
   callers over an explicit character ceiling, returning immutable chunks,
   warnings, and overflow metadata rather than exiting or printing.
3. `bin/ambient` — thin `read_files` and `_read_map_item` wrappers retain
   patchable `ABS_MAX_CHARS`, `_fail_exit`, `_argv_command`, and stderr behavior.

Move in 2C2A:

- Regular-file/type checks, bounded byte reads, lossy UTF-8 decoding, NUL/binary
  classification, empty-file classification, cumulative character accounting,
  and map's per-item result text.
- Correct map's existing byte/character mismatch: a valid multibyte file below
  the character ceiling must be read fully, while decoded content above the
  ceiling must be refused without silent truncation.
- Apply binary detection to the complete bounded payload for both lanes; map's
  documentation already promises the same binary guard as `read_files`.

Do not move stdin, map JSONL/cumulative gathering, repository walking, gutters,
diffs, secret policy, prompt construction, or command orchestration in 2C2A.
Any descriptor-race hardening that cannot preserve cross-platform regular-file
behavior in this three-file checkpoint must be recorded for 2C3, not hidden in
an expanding patch.

Phase 2C2A RED observed: all 11 direct ownership/behavior tests errored because
`ambient_codex.intake` did not exist, its import-purity subprocess failed, and
both facade wrapper tests failed because `_intake_core` was absent. The failures
are confined to the planned ownership seam.

Phase 2C2A local verification:

- Review-driven RED exposed that the first extraction still repeated the old
  `lstat`/path-open race. File descriptors now open non-following and nonblocking
  where supported and are revalidated with `fstat`, so a path swapped to a
  symlink, FIFO, device, or directory cannot become a blocking text read.
- Pre/post comparison against `b27fcab` proves exact chunks, diagnostics, and
  map-item results for normal/invalid-UTF-8 text, empty, binary, directory,
  symlink, and missing-file scenarios. The only intended behavior changes are
  the RED-locked map multibyte character-ceiling fix and full-payload NUL guard.
- All 1,214 guarded tests pass on the canonical Python 3.12 run; the earlier
  1,211-test checkpoint also passed independently on Python 3.11, 3.12, and
  3.14 before three additional error-branch contracts were added. The new
  `intake.py` module has 100% line coverage and total runtime coverage is 82%.
- Full ruff/compile, isolated-venv installation, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) pass.
- A clean archive of final commit `73e71cd` passes recursive compile, all 1,215
  guarded tests, and isolated installation. GitHub run `29112858149` passes all
  18 jobs, including every Windows runtime and package lane.
- Cache-busted install `1.9.0+codex.20260710180025` passes all 36 focused intake/
  config-write contracts, plugin validation, offline stress (26/26), MCP
  initialize/list/self-test/offline-control with 14 tools, and no-Node startup.
  The source manifest is restored to `1.9.0`; source `HEAD` and `origin/main`
  match cleanly before this closeout-only ledger update.

## Phase 2C2B plan — liveness-safe stdin intake

Production/test file boundary (three files):

1. `tests/test_refactor_phase2_intake_stdin.py` — readiness, timeout, binary,
   invalid text, over-limit, read-error, worker-error propagation, no-hang,
   ignored-data, import-purity, and facade-patch contracts.
2. `ambient_codex/intake.py` — extend the lower layer with explicit stream,
   selector, environment, thread-factory, and optional `fcntl` adapters;
   immutable worker outcomes replace the facade's shared mutable result
   dictionary.
3. `bin/ambient` — compatibility wrappers retain `read_stdin_if_piped`,
   `_stdin_read_and_decode`, `_read_stdin_bounded`, and
   `warn_if_stdin_ignored`, including existing user-facing wording.
4. `tests/test_refactor_phase2_intake_files.py` — extend the exact module-export
   ownership tuple; every 2C2A file contract remains otherwise unchanged.

The exact lower-layer export set after 2C2B is:

- Existing `read_files` and `read_map_item`.
- `stdin_wait_seconds(environment, default_wait, maximum_wait)` parses a finite,
  positive, bounded wait from `AMBIENT_STDIN_WAIT` without reading `os.environ`
  itself.
- `read_stdin_text(stream, char_cap)` returns immutable
  `(text, warnings, error)` values; it neither prints nor exits.
- `read_stdin_bounded(reader, wait_s, thread_factory)` returns immutable
  `(text, timed_out)` values and re-raises worker exceptions on the caller
  thread instead of converting them to empty input.
- `stdin_ready(stream, selector, wait_s)` distinguishes ready, timed-out, and
  unsupported-selector states.
- `stdin_has_waiting_data(stream, selector, fcntl_module)` performs the current
  zero-timeout/FIONREAD check and returns only a boolean.

Facade constants retain the ten-second default and add a named sixty-second
maximum; facade wrappers retain all four public/private stdin names, patchable
`sys.stdin`, `select.select`, `threading.Thread`, `fcntl`, environment, error
category, and exact existing diagnostics. Binary NUL stripping/warning applies
to the complete bounded payload, invalid/failed reads become explicit `input`
errors, invalid or non-finite wait overrides fall back safely, and selector
incompatibility still takes the daemon-thread timeout path.

Do not absorb setup-key input, interactive takeover/chat input, MCP stdio, map
JSONL semantics, command-level stdin precedence, or prompt construction.
Unexpected stream failures must not be silently converted to empty input.

Phase 2C2B RED observed: 19 direct stdin contracts errored because the five
planned lower-layer APIs were absent; import purity alone stayed green. The
existing exact-export ownership test failed on the intentionally expanded set,
and both facade-path tests errored at the absent core patch points. RED is
confined to the four-file ownership boundary.

Phase 2C2B local verification:

- The facade keeps all four stdin entry points while `intake.py` now owns finite
  wait parsing, bounded lossy decoding, readiness classification, immutable
  thread outcomes, and conservative ignored-data probing through explicit
  adapters. It has no import-time stream/environment/thread effects.
- Review-driven RED closes three prior liveness/integrity gaps: non-finite or
  extreme wait overrides cannot exceed sixty seconds; unexpected reader-thread
  failures reappear on the caller thread; and NUL stripping cannot hide that a
  raw byte stream exceeded the maximum UTF-8 byte budget.
- Pre/post comparison against `1e2114d` proves exact data and diagnostics across
  six TTY, binary, plain-text, timeout, unsupported-selector, and invalid-wait
  scenarios. Existing valid behavior is unchanged; only the RED-locked unsafe
  cases differ.
- All 1,237 guarded tests pass on the canonical Python 3.12 run; the preceding
  1,236-test checkpoint passed independently on Python 3.11, 3.12, and 3.14.
  The expanded `intake.py` module has 100% line coverage and total runtime
  coverage remains above the 80% release floor.
- Full ruff/compile, isolated-venv installation, plugin/skill validators,
  offline stress (26/26), and no-Node MCP startup (14 tools) pass. Clean-archive,
  GitHub matrix, and installed-cache gates remain pending.
- A prior docs-only run (`29113071849`) exposed a second timing-sensitive
  baseline: one macOS runner needed 0.328 seconds for the 0.300-second 300-line
  C-signature adversary. Deterministic RED proves marker-free C-family lines
  must not enter regex matching at all. A semantic `(`/type-declaration marker
  precheck preserves signature/depth behavior and reduces the complete local
  signature safety class to about 0.006 seconds without relaxing any threshold.
  All 1,238 guarded tests and offline stress remain green after the follow-up.
- A clean archive of final commit `536b345` passes recursive compile, all 1,238
  guarded tests, and isolated installation. The stdin-only commit's GitHub run
  `29113671444` and the final signature-optimized run `29113877023` each pass all
  18 runtime, coverage, package, plugin, and no-Node jobs.
- Cache-busted install `1.9.0+codex.20260710181726` passes all 48 focused file/
  stdin/signature contracts, plugin validation, offline stress (26/26), MCP
  initialize/list/self-test/offline-control with 14 tools, and no-Node startup.
  The source manifest is restored to `1.9.0`; source `HEAD` and `origin/main`
  match cleanly before this closeout-only ledger update.

## Phase 2C3 program — repository and git intake

Phase 2C3 is split into three independently installed checkpoints:

- 2C3A: pure line gutters plus descriptor-safe bounded gutter-size accounting.
- 2C3B: git/plain candidate discovery, containment, type/size/binary
  classification, and immutable skip/coverage metadata.
- 2C3C: bounded git-diff/status capture, NUL-delimited changed paths, and thin
  facade composition with the existing safe file reader/gutter layer.

This split prevents a repository walker rewrite from being reviewed in the same
patch as subprocess framing. No 2C3 lower layer may import command handlers,
audit orchestration, prompts, models, transport, spend, map/reduce, generation,
integrations, MCP, or the facade. `repo_audit_inputs` stays in the facade until
Phase 4 because it owns cost/partial policy and coverage-note orchestration.

## Phase 2C3A plan — gutters and bounded size accounting

Production/test file boundary (three files):

1. `tests/test_refactor_phase2_repository_gutters.py` — RED-first export,
   numbering/width/trailing-line, immutable result, ASCII/multibyte size,
   missing/symlink/FIFO, growth bound, import-purity, and facade patchability
   contracts.
2. `ambient_codex/repository.py` — `with_line_gutters(labeled)` and
   `guttered_file_size(path, size)` only; imports standard-library filesystem
   primitives and performs no work at import time.
3. `bin/ambient` — compatibility `with_line_gutters` and `_guttered_size`
   wrappers retain list return values and independently patchable core bindings.

The lower size reader opens non-following/nonblocking descriptors where
supported, revalidates them as regular with `fstat`, reads no more than the
caller-supplied snapshot size plus one byte, and returns the conservative raw
size on any classification/read failure. It must never open a FIFO/device or
chase a swapped symlink. Existing line labels and size estimates remain exact for
stable files.

Do not move candidate discovery, skip counters, containment, binary sniffing,
git subprocesses, coverage-note policy, `repo_audit_inputs`, or diff intake in
2C3A.

Phase 2C3A RED observed: all ten direct gutter/size contracts errored because
`ambient_codex.repository` did not exist, its import-purity subprocess failed,
and the facade contract errored because `_repository_core` was absent. RED is
confined to the planned three-file ownership seam.

Phase 2C3A local verification:

- Core gutter results are immutable tuples; the facade preserves historical
  list results. Stable ASCII, multibyte, empty, missing, numbering-width, and
  trailing-line behavior matches pre-extraction commit `00c2989` exactly.
- Size accounting now opens non-following/nonblocking descriptors where
  supported, revalidates with `fstat`, refuses nonregular paths, bounds reads to
  snapshot-size-plus-one, and falls back conservatively across every open/
  stat/read/type/close failure. The new 81-line module has 100% line coverage.
- All 1,251 guarded tests pass on Python 3.11, 3.12, and 3.14. Full ruff/compile,
  isolated-venv installation, plugin/skill validators, offline stress (26/26),
  and no-Node MCP startup (14 tools) pass. Clean-archive, GitHub matrix, and
  installed-cache gates remain pending.

### Phase 2C3A Windows fixture follow-up

- Checkpoint commit `09b03b1` passed every Linux/macOS runtime, package, lint,
  coverage, plugin, and no-Node job in GitHub run `29115188845`; all four
  Windows runtime jobs failed the same three-digit-width fixture assertion.
- The fixture used `Path.write_text()` to create an LF-only in-memory string.
  Windows translated those writes to CRLF, so the file snapshot and descriptor
  correctly contained 99 additional carriage returns while the expected value
  still measured the original LF-only string. The production repository reader
  uses `newline=""` and preserves CRLF, so the raw-byte estimate remains exact
  for the text actually sent; changing runtime accounting would undercount it.
- The fixture now writes explicit LF bytes, and a separate explicit-CRLF
  contract proves preserved Windows-style text is also estimated exactly. No
  production behavior changes in this corrective checkpoint.
- All 14 focused gutter contracts and all 1,252 guarded tests pass locally on
  Python 3.11, 3.12, and 3.14. Pinned coverage is 83% total with
  `repository.py` at 100%; full ruff/compile, plugin/skill validators, and
  offline stress (26/26) pass before the corrective commit.
- Corrective commit `cdde512` is pushed to `origin/main`. Its clean Git archive
  passes recursive compile, all 1,252 guarded tests, isolated installation, and
  direct package import/gutter behavior. Replacement GitHub run `29115745009`
  passes all 18 jobs on exact SHA `cdde512`, including Linux/macOS/Windows,
  Python 3.8/3.10/3.12/3.13, lint/coverage, package, plugin, and no-Node gates.
- Cache-busted install `1.9.0+codex.20260710185426` byte-matches the source
  repository module and passes all 14 focused contracts, plugin validation,
  offline stress (26/26), and MCP initialize/list/self-test/offline-control with
  14 tools on a Python-only PATH with no Node. Codex lists that cache version as
  installed and enabled; the source manifest is restored to stable `1.9.0`.

## Phase 2C3B plan — repository discovery and classification

Purpose: move candidate enumeration and text-source classification behind an
immutable, independently testable lower-layer API while preserving the public
`_repo_candidate_paths()` and `repo_walk()` list/dict contracts.

Production/test file boundary (four files):

1. `tests/test_refactor_phase2_repository_discovery.py` — RED-first Git command/
   NUL framing, undecodable-byte, fallback walk, traversal, vendor/dotdir,
   lockfile, empty/binary/oversize, descriptor identity, containment, immutable
   metadata, input-validation, import-purity, and facade contracts.
2. `ambient_codex/repository.py` — add immutable `RepositorySkips`,
   `candidate_paths(...)`, and `classify_repository_files(...)`; standard-library
   filesystem calls occur only when invoked and Git execution is injected.
3. `bin/ambient` — retain thin `_repo_candidate_paths()` and `repo_walk()`
   wrappers, passing patchable `subprocess`, constants, and historical defaults;
   convert lower-layer tuples/records back to lists/dicts for compatibility.
4. `tests/test_refactor_phase2_repository_gutters.py` — extend only the exact
   module-export ownership tuple; all 2C3A contracts remain unchanged.

Tracking updates remain allowed in this ledger and do not consume the four-file
production/test boundary.

Required lower-layer contracts:

- Git discovery invokes `git -C ROOT ls-files -z --cached --others
  --exclude-standard` without a shell, with the existing 30-second timeout.
  Capture bytes, split only on NUL, and decode paths with the filesystem codec so
  valid non-UTF-8 POSIX names cannot crash discovery. Nonzero exit, timeout,
  launch/value failure, or malformed output falls back to the plain walker.
- Plain discovery preserves deterministic sorting, prunes known generated/
  vendored and dot directories before descent, and never follows directory
  symlinks.
- Classification treats every candidate as untrusted data: reject absolute and
  parent-traversing names, skip vendored paths on both lanes and dotdirs on the
  plain lane, skip lockfiles, and require resolved containment under the repo.
- Binary sniffing must use a non-following/nonblocking descriptor where the OS
  supports it, revalidate regular-file type and descriptor identity with
  `fstat`, and read at most 8,192 bytes. A path swap must be omitted, never read.
- Return immutable file tuples and `RepositorySkips`; retain the 40-path
  oversize evidence cap. Validate the per-file ceiling as a positive integer.
  The facade preserves the historical file list and skipped dict/list shape.
- Explicit safety fixes in this checkpoint are limited to binary Git-path
  decoding, fail-fast invalid ceilings, descriptor identity, and current
  descriptor size. Each requires a deterministic RED contract and must not
  change normal stable-repository results.

Research decision: GitHub code/repository metadata and current GitPython,
`pygit2`, and `pathspec` registry options were reviewed. No dependency is
adopted: the existing NUL-framed Git command plus stdlib filesystem APIs retain
Python 3.8, source/plugin/pipx portability, and no-install/no-Node behavior.

Do not move gutter code again, git diff/status capture, changed-path parsing,
coverage-note policy, input-ceiling selection, `repo_audit_inputs`, prompts,
models, transport, spend, map/reduce, generation, integrations, MCP, or command
handlers in 2C3B.

Phase 2C3B RED observed: the 27 focused discovery-plus-gutter contracts fail
with 16 missing-API errors and two export-ownership failures because
`RepositorySkips`, `candidate_paths`, `classify_repository_files`, and their
facade delegation do not exist yet. Import purity and all unchanged 2C3A
behavior stay green, confining RED to the planned ownership seam. The RED
surface also locks OSError/timeout/value/nonzero/malformed Git fallback without
leaving test directories behind.

Phase 2C3B implementation checkpoint:

- The expanded 330-line repository module owns exactly five public exports and
  keeps discovery/classification results immutable. The facade alone converts
  them to the historical list/dict shape.
- Git candidate capture is byte/NUL-framed and filesystem-decoded; a real Git
  integration proves tracked plus untracked-not-ignored paths are included and
  `.gitignore` exclusions hold. The fallback scanner is deterministic, prunes
  before descent, and does not descend through directory symlinks. Diff review
  caught an initial breadth-first ordering drift; a nested-tree RED contract now
  preserves the historical sorted depth-first order through an immutable
  persistent stack with no recursive depth risk.
- Classification validates its ceiling, rejects untrusted traversal/absolute/
  NUL paths, preserves Git-lane dotfiles, filters vendors/locks, bounds oversize
  evidence to 40 paths, and returns complete omission counts.
- Binary sniffing opens non-following/nonblocking descriptors where supported,
  revalidates type plus file identity, uses the opened descriptor's current
  size, reads at most 8,192 bytes, and closes across success, mismatch, read,
  and `fstat` failures. Initial GREEN exposed and fixed one descriptor leak and
  one premature `*.lock` normalization bug without weakening tests.
- All 32 focused discovery/gutter contracts and all 1,270 guarded tests pass on
  Python 3.11, 3.12, and 3.14. Pinned runtime coverage is 83% total and 96% for
  `repository.py`. Stable Git-lane behavior over 96 files and fallback behavior
  over 94 files match boundary commit `a632ecd` exactly for files, sizes, skip
  metadata, and lane selection.
- Full ruff/compile, plugin/skill validators, offline stress (26/26), and no-Node
  MCP initialize/list/self-test/offline-control with 14 tools pass. A synthetic
  100,000-path byte/NUL Git listing parses in 0.009 seconds locally. Clean-
  archive, GitHub matrix, and installed-cache gates remain pending.
- Checkpoint commit `ae34b98` is pushed to `origin/main`. Its clean Git archive
  passes recursive compile, all 1,270 guarded tests, isolated installation, and
  direct package discovery/record behavior. GitHub run `29118198336` passes all
  18 jobs on exact SHA `ae34b98`, including Linux/macOS/Windows, Python 3.8/
  3.10/3.12/3.13, lint/coverage, package, plugin, and no-Node gates.
- Cache-busted install `1.9.0+codex.20260710193235` byte-matches the source
  runtime and focused test files and passes all 32 discovery/gutter contracts,
  plugin validation, offline stress (26/26), and MCP initialize/list/self-test/
  offline-control with 14 tools on a Python-only PATH with no Node. Codex lists
  that cache version as installed and enabled; the source manifest is restored
  to stable `1.9.0`.

## Phase 2C3C plan — bounded Git diff and changed-file intake

Purpose: make `audit --staged` / `audit --diff REF` memory-bounded and safe for
arbitrary Git filenames while preserving existing CLI output, full-current-file
context, subdirectory behavior, and audit orchestration.

Production/test file boundary (five files):

1. `tests/test_refactor_phase2_repository_diff.py` — RED-first immutable record,
   bounded process, timeout/launch/read/overflow, revision validation, real Git,
   NUL filename, subdirectory/root, containment, aggregate-cap, import-purity,
   and facade contracts.
2. `ambient_codex/repository.py` — add immutable `GitDiffSnapshot`,
   `GitDiffFailure`, and `capture_git_diff(...)`; keep the bounded process runner
   private and standard-library-only.
3. `bin/ambient` — keep `git_diff_inputs(staged, ref)` as a thin compatibility/
   error-orchestration facade over the lower capture plus existing safe intake
   and gutter modules.
4. `tests/test_refactor_phase2_repository_discovery.py` — extend only the exact
   repository export ownership tuple; all 2C3B contracts remain unchanged.
5. `tests/test_refactor_phase2_repository_gutters.py` — extend only the same
   export tuple; all 2C3A contracts remain unchanged.

Required lower-layer contracts:

- Launch Git without a shell through injected `Popen`. Drain stdout and stderr
  concurrently as bytes, retain no more than each explicit cap, terminate on
  overflow, kill after bounded termination failure, and close every pipe.
  Launch, read, timeout, malformed-stream, and overflow states return explicit
  immutable failures; none may hang or silently become an empty diff.
- Preserve the existing 30-second Git timeout. Bound rev-parse outputs to 64 KiB,
  stderr evidence to 4 KiB, and diff/path output to the caller's positive byte
  ceiling. Oversized diffs fail explicitly before model/API work; partial Git
  output is never presented as complete.
- Validate `--diff` revision strings before launch: nonempty string, at most
  4,096 characters, no NUL/control characters, and no leading `-`. Users must
  use `--staged` instead of smuggling Git options such as `--cached` through the
  revision value. End revision parsing with `--` in every diff command.
- Check inside-repo, diff, repo-root, and changed-path command results
  independently. Keep the historical outside-repo, bad-diff, and empty-diff
  messages for their existing cases; root/path-list failures become explicit
  input errors instead of silently degrading to diff-only coverage.
- Request changed paths with `--name-only -z`; split only on NUL and decode with
  the filesystem codec. Preserve leading/trailing spaces and embedded newlines.
  Reject absolute, NUL, and parent-traversing entries, resolve every path against
  the real top-level, and return outside-root omissions explicitly.
- `GitDiffSnapshot` contains decoded diff text, resolved root, immutable
  `(portable_label, full_path)` changed-file tuples, and immutable omitted-path
  evidence. Invalid diff bytes decode with replacement rather than crashing.
- The facade reserves diff size from `ABS_MAX_CHARS`, reads all changed files in
  one aggregate bounded intake call, applies line gutters, and verifies the
  final diff-plus-gutters character count. Overflow fails with a clear split/
  narrow-range message before catalog lookup or spend.

Explicit RED-locked fixes are limited to bounded process memory/liveness,
byte/NUL Git framing, revision option-injection refusal, checked root/path-list
commands, containment evidence, and one aggregate context ceiling. Do not move
secret policy, audit prompts, model/catalog routing, cost/partial policy,
map/reduce, consensus/deep passes, hooks, generation, integrations, MCP, or
command dispatch in 2C3C.

Research decision: GitHub code/repository metadata and current `subprocess-tee`,
`plumbum`, and `sh` registry options were reviewed. No dependency is adopted:
the runtime remains Python 3.8+, stdlib-only, no-Node, and installable from
source/plugin cache/pipx without dependency or API drift.

Phase 2C3C RED observed: the 46 focused diff/discovery/gutter contracts fail
with three export-ownership failures and 23 missing record/capture/facade API
errors because `GitDiffSnapshot`, `GitDiffFailure`, `capture_git_diff`, and the
new facade composition do not exist. Existing repository import purity and all
unchanged 2C3A/2C3B behavior stay green, confining RED to the frozen seam.

Phase 2C3C implementation checkpoint:

- The 763-line repository module owns three new immutable exports while every
  production function remains below 50 lines. Git stdout/stderr are drained
  concurrently as bytes, capped independently, and terminated with a one-second
  kill escalation on overflow/timeout; malformed pipes and every launch/read/
  wait state return explicit failures.
- Staged and revision diff commands are option-terminated, revision values are
  validated, changed paths use NUL framing/filesystem decoding, all four Git
  command results are checked, and snapshot path/omission data is immutable.
- The facade reads changed files once under the remaining aggregate character
  budget, adds exact line gutters, and refuses post-gutter overflow before any
  catalog/API/spend work. Stable staged-diff output from a subdirectory matches
  boundary commit `6a10ce3` exactly for patch text, labels, and full-file text.
- Real Git integrations cover staged/subdirectory, Unicode/space/newline paths,
  `--diff HEAD`, and forced 512-byte overflow. A child that ignores termination
  is killed and returns no partial snapshot.

### Critical Git helper/environment security fix

Security review found that the historical plain `git diff` could honor
repository `diff.external`/textconv helpers while inheriting Ambient and other
token environment variables. A POSIX adversarial repo deterministically
executed its configured helper and suppressed the real patch, proving the issue.

- Every diff/path command now uses `--no-ext-diff`, `--no-textconv`,
  `core.fsmonitor=false`, and `--no-pager`; changed-path and candidate commands
  run through bounded capture where the facade invokes them.
- Child Git environments remove Ambient/shared keys, token/secret/password/
  credential/auth variables, `GIT_EXTERNAL_DIFF`, and Git config-injection
  variables case-insensitively for Windows parity; pagers are disabled and
  system attributes are ignored.
- The hostile external/textconv fixture no longer executes, secret-environment
  contracts pass, and all source runtime Git call sites were reviewed. The one
  remaining direct call is hook-directory `rev-parse`, which cannot invoke
  diff/textconv/fsmonitor helpers and remains scoped to the later integrations
  phase.
- The full suites exposed one compatibility regression in legacy tests that
  inject a `run`-only subprocess double. The production facade still selects
  bounded `Popen`; injected doubles without `Popen` now retain the historical
  runner seam. Its focused regression failed before the fix and passes after.
- Mixed/lowercase Git helper/config environment names now have an explicit
  RED/GREEN contract, closing the Windows case-insensitive bypass before commit.
- Changed-file intake warnings and overflow paths are terminal-sanitized; an
  adversarial ANSI filename/warning contract failed before the fix and passes.
- All 52 focused diff/discovery/gutter contracts and all 1,290 guarded tests pass
  on Python 3.11, 3.12, and 3.14. Pinned runtime coverage is 84% total and 92%
  for `repository.py`; full ruff, recursive compile, plugin/skill validators,
  version/manifests/hooks, offline stress (26/26), and no-Node MCP startup with
  14 tools pass. The new test file is 790 lines and `repository.py` is 763 lines,
  both below the 800-line ceiling.
- A synthetic 100,000-path byte/NUL listing parses in 0.010 seconds, and a real
  staged 2 MB diff is terminated/refused at a 1 MB byte ceiling in 0.025 seconds.
  Exact pre/post stable staged-diff behavior remains green.
- Checkpoint commit `4ba1015` is pushed to `origin/main`. Its clean Git archive
  passes recursive compile, all 1,290 guarded tests, and a real isolated-venv
  package install. GitHub run `29120423507` passes all 18 jobs on the exact SHA,
  including Linux/macOS/Windows, Python 3.8/3.10/3.12/3.13, lint/coverage,
  package, plugin, and no-Node gates.
- Cache-busted install `1.9.0+codex.20260710201127` byte-matches source runtime
  and focused tests and passes all 52 diff/discovery/gutter contracts, both
  validators, offline stress (26/26), and MCP initialize/list/self-test/offline-
  control with 14 tools on a Python-only PATH with no Node. The source manifest
  is restored to stable `1.9.0`.

## Phase 2D program — cache, usage, spend, and fleet state

Phase 2D is split so persistence mechanics, reporting, pricing decisions, and
cross-process reservations never move in one high-risk checkpoint:

1. 2D1 extracts content-addressed cache key/read/atomic-write/prune state.
2. 2D2 extracts bounded usage-ledger append/spool/trim/read and summary records.
3. 2D3 extracts pure pricing, reference comparison, estimation, and spend gates.
4. 2D4 extracts fleet reservation parsing, locking, atomic rewrite, reserve, and
   release behavior after 2D3 supplies an explicit decision boundary.

Each subphase keeps facade names/signatures patchable, changes at most five
production/test files, writes RED ownership and behavior contracts first, and
must independently pass the full release ladder. Transport, live catalog/model
routing, map/reduce, audit/generation workflows, command dispatch, integrations,
MCP, and takeover behavior do not move in Phase 2D.

### Phase 2D1 frozen boundary — cache state

Production/test files (three; below the five-file ceiling):

1. New `ambient_codex/cache_store.py` owns `cache_key`, bounded defensive cache
   reads, private atomic writes, and deterministic oldest-entry pruning.
2. `bin/ambient` retains `CACHE_DIR`, limits/defaults, and the patchable
   `_cache_key`, `_cache_get`, `_cache_put` facade signatures as thin adapters.
3. New `tests/test_refactor_phase2_cache_store.py` owns module location/import,
   exact key compatibility, malformed/untrusted entry, path, TTL, permission,
   cleanup, pruning-race, concurrent same-key, and facade patchability contracts.

Stable behavior: valid SHA-256 addresses, response-format/salt sensitivity,
missing/expired/corrupt misses, 0600 atomic entries, private cache directory,
oldest approximate-cap pruning, best-effort write failures, concurrent same-key
read/write integrity, source/cache/package imports, and all caller-visible cache
hit/miss behavior. Security hardening may fail closed on nonregular entries,
unsafe key path components, non-string cached payloads, and malformed JSON
objects; cache data is disposable, so these states become misses rather than
runtime crashes or reads outside the cache root.

Research decision: GitHub repository/code search and current `diskcache` and
`cachetools` registry options were reviewed as untrusted reference data. No
dependency is adopted: SQLite-backed `diskcache` is robust but would change the
on-disk format and install surface, while in-memory `cachetools` does not solve
cross-process persistence. The current stdlib `mkstemp` plus same-directory
`os.replace` design remains the compatible Python 3.8+/no-Node approach.

Do not move `cmd_cache`, usage/telemetry state, pricing, spend/fleet gates,
transport retries, models, workflows, integrations, MCP, or parser/dispatch in
2D1.

Phase 2D1 RED observed: all 13 initial cache contracts fail with 12 missing
module/adapter errors and one import failure; no unrelated contract fails.

Phase 2D1 implementation checkpoint:

- The 191-line `cache_store.py` module owns stable content addresses, bounded
  descriptor-based reads, validated cache-local keys, string/object JSON
  validation, private same-directory atomic writes, deterministic approximate
  pruning, and best-effort cleanup. The facade preserves all three historical
  `_cache_*` signatures and runtime-patchable `CACHE_DIR`/limit/private-dir seam.
- Security hardening turns traversal/absolute/separator keys, symlinks,
  directories, oversized entries, malformed/non-object/non-string/deep JSON,
  and invalid write payloads into disposable misses rather than outside-root
  reads, unbounded loads, crashes, or writes.
- Two explicit RED/GREEN resource tests found descriptor leaks when `fstat` or
  `fdopen` failed after a successful open. Both paths now close exactly once;
  temp files are also removed after replace failure.
- Final cross-version stress found Python 3.11 raises `RecursionError` for a
  deeply nested bounded JSON entry where newer decoders return a normal parse
  failure. The 3.11 contract failed before the fix; deep cache JSON now becomes
  a miss consistently on every supported runtime.
- Stable SHA-256 key fixtures include response-format and best-of salt behavior;
  0600 entry/0700 directory modes, TTL, pruning races, concurrent same-key
  readers/writers, import purity, and facade call composition pass.
- All 15 focused cache contracts, 66 combined cache/repository contracts, and
  all 1,305 guarded tests pass on Python 3.11, 3.12, and 3.14. Pinned coverage
  is 84% total and 84% for `cache_store.py`; full ruff/compile, plugin/skill
  validators, offline stress (26/26), and no-Node MCP startup with 14 tools pass.
- Checkpoint commit `0b12b10` is pushed to `origin/main`. Its clean Git archive
  passes recursive compile, all 1,305 guarded tests, and a real isolated-venv
  package install. GitHub run `29121317434` passes all 18 jobs on the exact SHA,
  including Linux/macOS/Windows, Python 3.8/3.10/3.12/3.13, lint/coverage,
  package, plugin, and no-Node gates.
- Cache-busted install `1.9.0+codex.20260710202712` byte-matches source cache
  runtime/tests and passes all 15 focused contracts, both validators, offline
  stress (26/26), and MCP initialize/list/self-test/offline-control with 14 tools
  on a Python-only PATH with no Node. The source manifest is restored to stable
  `1.9.0`.

### Phase 2D2A frozen boundary — usage ledger persistence

Persistence and reporting are separate checkpoints: ledger writes coordinate
threads/processes and recover spools, while `cmd_usage` applies catalog pricing,
reference-price, and display policy. Moving both would couple state extraction
to the later spend boundary.

Production/test files (three; below the five-file ceiling):

1. New `ambient_codex/usage_store.py` owns in-process serialization, bounded
   per-process spooling, safe dead-owner spool merging, private ledger append,
   permission healing, and newest-line trim persistence.
2. `bin/ambient` retains enrichment (`usage_cost`, reference price, telemetry),
   `USAGE_PATH`/limits/wait knobs, `_fs_lock`, `_pid_alive`, `_private_dir`, and
   the patchable `log_usage` facade while delegating persistence explicitly.
3. New `tests/test_refactor_phase2_usage_store.py` owns import/location,
   facade delegation with patchable knobs, record-byte compatibility, late-bound
   `getpid` parity, permission heal, line-based trim, lock-timeout spooling,
   spool cap, merge liveness (own/dead/unknown), malformed and out-of-range
   spool-name skips, missing-dir no-op, best-effort/fail-open behavior,
   corrupt-UTF-8 tolerance, deterministic in-process lock ordering, and
   in-process append concurrency. Symlink/nonregular refusal, cross-process
   concurrency, and fd-cleanup are deferred hardening (see 2D2A verification).

Stable behavior: additive JSONL record format/order, full-precision enrichment,
estimated/character telemetry markers, 0600 ledger/spools, bounded newest-line
trim, lock-timeout spooling rather than unlocked append, own/dead spool merge,
live/unknown spool preservation, fail-open metering, and every existing facade
patch seam. Security hardening may refuse symlink/nonregular stores, malformed
spool names/data, oversized lines, and partial/torn files without following or
executing them; metering remains best effort and never blocks a model result.

Research decision: GitHub repository/code search and current `filelock` and
`portalocker` registries were reviewed as untrusted reference data. No runtime
dependency is adopted: the existing injected `_fs_lock` already provides POSIX
`flock` plus the tested Windows `O_EXCL` policy, while adding a lock package
would alter the stdlib-only/no-install surface without replacing spool recovery
or ledger-specific atomicity.

Do not move usage enrichment, telemetry learning, `cmd_usage`, pricing/reference
math, spend/fleet decisions, `_fs_lock` implementation, transport, models,
workflows, integrations, MCP, or parser/dispatch in 2D2A. 2D2B will own bounded
record reads and report composition only after 2D2A is independently released.

## Phase 2D2A verification

- Extraction `114966e`: `spool_line`/`merge_spools`/`_trim_ledger`/`append_line`
  moved to `ambient_codex/usage_store.py`; `log_usage` keeps enrichment and
  delegates via patchable facade knobs. RED-first contracts observed.
- Parity follow-up `b91d26f`: fixed a Codex-found late-binding regression —
  `getpid` was an early-bound default argument; now a `None` sentinel resolves
  `os.getpid` at call time. Dropped the unused injectable `serialize` seam.
- Codex adversarial audit (frozen tree, independent second pass): runtime parity
  green, NO material production regression. Fix-now items applied:
  - `merge_spools` resolves `getpid` per candidate (matches the original's
    per-iteration `os.getpid()`), closing the call-timing delta.
  - Fail-open hardening: `append_line`'s boundary swallows any `Exception`
    (metering must never break a chat turn); `_trim_ledger`/`merge_spools`
    tolerate a corrupt (invalid-UTF-8) ledger; out-of-range spool pids are
    skipped before `pid_alive`, closing an `OverflowError` reaching `os.kill`.
  - Docstrings corrected: no absolute "bounded"/"never raises"/"costs nothing".
  - New contracts: append_line default-getpid, deterministic lock enter/exit
    order + denied-lock-no-append, corrupt-UTF-8 no-raise, out-of-range pid skip.
- Gates: 1330 guarded tests pass; `ruff check .` clean; plugin + skill validators
  pass; no-Node MCP startup lists 14 tools with 0-byte stderr; CI green on all 18
  jobs at `b91d26f` (coverage >= 80%); usage-touching subset 157 pass.

### Deferred hardening (PRE-EXISTING; explicitly tracked, not 2D2A regressions)

Codex enumerated durability gaps that predate this refactor and are out of scope
for a behavior-preserving extraction. Tracked for a dedicated hardening pass:
- Strict byte budget for spools/ledger + aggregate per-install spool quota
  (current caps are approximate/line-based).
- Torn/partial JSONL record framing repair or quarantine on crash/ENOSPC.
- Bounded/streaming reads under the lock (full-file `read()`/`readlines()` can
  exhaust memory; a FIFO could block while holding `_LEDGER_SERIALIZE`).
- Symlink/nonregular refusal (`lstat`/`fstat`/`O_NOFOLLOW`) for ledger + spools.
- Windows spool reclamation via a process nonce + conservative TTL (unknown
  liveness currently strands foreign spools off POSIX).
- Duplicate-replay avoidance when `os.unlink` fails after a spool merge.
- `fchmod` on the open FD + heal-before-merge; guaranteed FD close on `fdopen`
  failure; timestamp/sequence-aware recovery ordering.

## Phase 2D2B verification

- New `ambient_codex/usage_report.py` owns `read_records(usage_path)` (JSONL →
  well-formed dict records + bad-line count; blank lines skipped; OS error
  family raised to the caller) and `filter_recent(records, cutoff, ts_of)`.
- `cmd_usage` now delegates its read + recency filter to the module and keeps
  its own `sys.exit` messages, the "skipped N corrupt" report, and ALL pricing /
  reference / savings math (that stays for 2D3). `observed_cpt` was deliberately
  left untouched (telemetry read; its own concern), scoping 2D2B to the report.
- 9 RED-first contracts (exports, import purity, parse/skip/bad-count,
  FileNotFound + OSError propagation, empty ledger, recency filter, facade
  delegation on missing-ledger + bad-line reporting).
- Gates: full guarded suite + `ruff check .` clean; validators pass; no-Node MCP
  14 tools; cmd_usage-touching suites (v8/v9/v10) green; CI 18 jobs green on
  `92354c0` (Windows incl.).
- Codex audit (frozen tree): NO CRITICAL/HIGH/MEDIUM; pricing/reference/savings
  tail SHA-256 identical, `observed_cpt` byte-identical. Fix-now items applied:
  documented + tested the intentional `except ValueError` broadening (a 4300+
  digit integer line is counted corrupt, not crashed); added exact-`OSError`
  message + reader/recency wiring facade tests; fixed a PRE-EXISTING time-bomb in
  `test_audit_fixes.py` (fixed 2026-07 ts + 30-day window would fail after
  2026-08-05). DEFERRED (pre-existing, matches original): a byte-corrupted
  (invalid-UTF-8) ledger still tracebacks `ambient usage` (the writer only ever
  emits UTF-8) — added to the deferred-hardening list.

## Exact resume point (updated 2026-07-14)

SHIPPED: **v1.10.0 released** (`f9ef3fc`, tag `v1.10.0`) — first public release.
Done since 2D2B: 2D3a pricing primitives; savings-display-off-by-default HARD
RULE (Codex-audited, HIGH `--json` cost leak fixed); the ENTIRE spend-cap /
gate / fleet-reservation subsystem DELETED (so 2D3c + 2D4 are gone); 2D3b-1 cost
math extracted. All CI-green incl Windows.

NEXT: **Phase 3 — transport, models, map/reduce** (the biggest remaining facade
bloat). A mapping agent is producing the bounded sub-checkpoint plan (3A
transport primitives → 3B HTTP/stream → 3C catalog → 3D routing → 3E telemetry
→ 3F chunk-packing → 3G orchestration). Execute each RED-first, ≤5 files, full
gate + CI. Then Phase 4 (audit/generation), Phase 5 (integrations + facade
reduction, incl. deferred `savings_note*`). AUDIT NOTE: behavior-preserving
mechanical extractions get full test+CI per checkpoint + a comprehensive Codex
audit at each Phase boundary (batched, for cost/time); behavior CHANGES get a
per-change frozen-tree Codex audit (as savings + spend-cap did).

T5 backup cleanup: NO-OP — only the bundle+tarball safety net exists at
`/Users/z/ambient-codex-backups/pre-refactor-8104930/` (KEEP); no redundant
working copy exists to delete.
