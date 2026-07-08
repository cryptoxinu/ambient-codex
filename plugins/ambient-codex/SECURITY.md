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

- API key handling: keys are stored in the OS keychain when available or an
  owner-only local config file when explicitly used. Keys are never passed on
  argv and must not be pasted into chat.
- External input boundary: all web/API/MCP/model output is untrusted data.
- External output boundary: selected prompts, diffs, and files are sent to the
  configured inference endpoint.
- Launcher ownership: the Codex hook and bundled `link` only self-heal launchers
  whose target path contains `/ambient-codex/`. Any other launcher is treated as
  foreign and left untouched.
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
