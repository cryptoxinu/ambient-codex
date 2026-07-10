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

The production architecture is intentionally hybrid: the Codex skill owns
routing and safety policy, MCP owns fast bounded controls, the bundled CLI owns
heavy execution, and hooks are opt-in only. See
[plugins/ambient-codex/docs/CODEX_NATIVE_ARCHITECTURE.md](plugins/ambient-codex/docs/CODEX_NATIVE_ARCHITECTURE.md).

## Validate

```bash
cd plugins/ambient-codex
python3 -m py_compile bin/ambient mcp/ambient_mcp.py
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" .
python3 "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" skills/ambient
python3 -m unittest discover -s tests -q
```

## Install Locally In Codex

For the public repository:

```bash
codex plugin marketplace add cryptoxinu/ambient-codex
codex plugin add ambient-codex@ambient-codex
```

For local development, run this from the repository root:

```bash
codex plugin marketplace add "$PWD"
codex plugin add ambient-codex@ambient-codex
```

The local marketplace file is:

```text
.agents/plugins/marketplace.json
```

Start a new Codex thread after install or reinstall. Then invoke the skill with
`$ambient` or by asking Codex to use Ambient for an audit, build, summary,
second opinion, or token-saving delegation.

Native control smoke test from the plugin root:

```bash
cd plugins/ambient-codex
./bin/ambient control --offline
```

See [plugins/ambient-codex/README.md](plugins/ambient-codex/README.md) for the
plugin details.

## Security And Maintenance

- [Public-use threat model](ambient-codex-threat-model.md)
- [Post-1.9 CLI refactor scope](plugins/ambient-codex/docs/CLI_REFACTOR_SCOPE.md)
