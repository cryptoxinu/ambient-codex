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
| 1A | Immutable runtime constants | Ready to commit | — | Local gates green; docs/CI pending |
| 1B | Immutable records and model metadata | Pending | — | — |
| 2 | State, safety, and spend boundaries | Pending | — | — |
| 3 | Transport, models, and map/reduce | Pending | — | — |
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
- Clean archive, installed-cache, and GitHub cross-platform gates remain pending
  until the Phase 1A implementation commit exists.

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

## Exact resume point

1. Commit the green five-file Phase 1A implementation checkpoint.
2. Synchronize documented unittest commands to guarded discovery in bounded
   documentation-only checkpoints.
3. Run clean-archive, GitHub, and cache-busted installed-plugin gates before
   marking Phase 1A complete or beginning Phase 1B.

Do not begin Phase 2 until Phase 1 is green, committed, pushed, and recorded.
