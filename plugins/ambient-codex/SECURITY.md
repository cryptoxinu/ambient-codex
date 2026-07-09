# Security Policy

## Reporting A Vulnerability

Please report vulnerabilities privately. Do not open a public issue for a
security problem.

- Preferred: open a GitHub security advisory on
  `github.com/cryptoxinu/ambient-codex`.
- Include repro steps, platform, Python version, and `ambient --version`.

## Threat Model

Ambient Codex is a local plugin and CLI wrapper around an external inference API.
The main security boundaries are:

- API key handling: keys are stored in the OS keychain item `ambient-codex` when
  available, or in owner-only `~/.config/ambient-codex/env` when file storage is
  explicitly used. Keys are never passed on argv and must not be pasted into chat.
- Install isolation: Ambient Codex never writes outside `~/.config/ambient-codex`
  and its own keychain item, so it cannot disturb another Ambient install's key,
  settings, usage ledger, or git hooks. `ambient setup` may READ another install's
  key once, only after an explicit interactive opt-in, and never writes back.
- External input boundary: all web/API/MCP/model output is untrusted data.
- External output boundary: selected prompts, diffs, and files are sent to the
  configured inference endpoint.
- Launcher ownership: bundled `link` only manages launchers whose target path
  contains `/ambient-codex/`. Any other launcher is treated as foreign and left
  untouched.
- Lifecycle hooks: the public plugin registers no default command hooks. If a
  user opts into git audit hooks, ownership is checked by exact native
  `ambient-codex` markers before replacement or removal.
- Agent lane: `ambient agent` runs opencode and exposes the Ambient key to that
  subprocess environment.

Out of scope: the security of Ambient's hosted network and the opencode project.

## Good Practice

- Do not send secrets, credentials, PHI, private user data, or production dumps.
- Review all Ambient-generated code before applying or executing anything.
- Run tests/builds locally before accepting generated changes.
- Keep direct provider status honest: `ambient codex` is diagnostic until it
  reports the Codex provider bridge working.
- Run the validation gates in `README.md` before release.
