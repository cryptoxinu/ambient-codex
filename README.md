# Ambient Codex

Standalone Codex-native Ambient plugin repository.

The plugin lives at:

```text
plugins/ambient-codex
```

The local marketplace lives at:

```text
.agents/plugins/marketplace.json
```

This repo is intentionally separate from any Claude Ambient install. Ambient
Codex should not inspect, invoke, or route through Claude plugin files during
normal development or runtime use.

## Validate

```bash
cd plugins/ambient-codex
python3 -m py_compile bin/ambient mcp/ambient_mcp.py
python3 /Users/z/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
python3 /Users/z/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ambient
python3 -m unittest discover -s tests -q
```

## Install Locally In Codex

Point Codex at:

```text
/Users/z/ambient-codex/.agents/plugins/marketplace.json
```

Then invoke the skill with `$ambient` or by asking Codex to use Ambient for an
audit, build, summary, second opinion, or token-saving delegation.

Native control smoke test from the plugin root:

```bash
cd plugins/ambient-codex
./bin/ambient control --offline
```

See [plugins/ambient-codex/README.md](plugins/ambient-codex/README.md) for the
plugin details.
