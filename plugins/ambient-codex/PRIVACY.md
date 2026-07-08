# Privacy

`ambient-codex` is local-first. It sends only the prompts, code, diffs, or files
you explicitly route to the configured Ambient-compatible inference endpoint.

## What Leaves Your Machine

- Prompt and file content passed to `ambient ask`, `ambient audit`,
  `ambient map`, `ambient code`, `ambient build`, or `ambient agent`.
- Requests go to `https://api.ambient.xyz` by default, or to the endpoint the
  user explicitly configured and trusted.

No analytics, crash reporting, or background telemetry is sent by this plugin.

## What Stays Local

- API key: OS keychain when available, or `~/.config/ambient/env` with owner-only
  permissions when file storage is explicitly used.
- Usage ledger: `~/.config/ambient/usage.jsonl`.
- Chunk cache: `~/.config/ambient/cache/`.
- Build resume state: `<build-dir>/.ambient-build.json`.
- Codex plugin files: under the local plugin install/cache.

## User Responsibility

Auditing or building against code publishes that selected content to the network
you configured. The CLI refuses obvious credential-looking content and `.env`
files, but the tripwire is a backstop. Do not send secrets, credentials, private
user data, health data, or unrelated proprietary material.

## Agent Boundary

`ambient agent` launches opencode as a separate tool and passes the Ambient key
to that subprocess through the environment. This privacy statement covers the
Ambient Codex plugin and CLI; opencode has its own behavior.

## Purge Commands

```bash
ambient setup --remove
ambient cache clear
rm -f ~/.config/ambient/usage.jsonl
rm -f ~/.config/ambient/env
```

Delete `.ambient-build.json` files from build directories when you no longer
need resume state.
