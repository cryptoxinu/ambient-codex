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
| 0B | CI/package gate integration | Committed | `4c8e31f` | Local gates green; GitHub pending |
| 1 | Pure constants and records | Pending | — | — |
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
- [ ] Reinstall the cache-busted plugin and run installed MCP smoke.
- [ ] Commit Phase 0 and require GitHub's full matrix to pass.

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

## Exact resume point

1. Push the committed Phase 0 checkpoints and require the full GitHub runtime
   and cross-platform package matrix to pass.
2. Reinstall the cache-busted plugin and run installed MCP smoke before Phase 1.

Do not begin Phase 1 yet.
