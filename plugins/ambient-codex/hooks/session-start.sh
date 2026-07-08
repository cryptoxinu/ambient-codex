#!/usr/bin/env bash
# SessionStart hook (startup|resume|clear|compact):
#  1. Self-heal the ~/.local/bin/ambient launcher — plugin updates move the
#     versioned install dir, and the old dir is garbage-collected later, which
#     would leave the user's terminal `ambient` dangling.
#  2. Remind Codex when Ambient delegate mode is ON.
# Prints nothing (adds no context) in the normal case.
set -eu

plugin_root="${PLUGIN_ROOT:-}"
case "${plugin_root:-}" in
  */ambient-codex/*) ;;
  *) plugin_root="" ;;
esac

if [ -n "$plugin_root" ] && [ -x "${plugin_root}/bin/ambient" ]; then
  link="$HOME/.local/bin/ambient"
  real="${plugin_root}/bin/ambient"
  # Heal ONLY this well-known path, and ONLY when it is a SYMLINK we OWN:
  #  - dangling (a plugin update GC'd the old versioned dir it pointed at), or
  #  - a stale ambient-codex launcher (target exists but is not the ACTIVE
  #    install).
  # OWNERSHIP is proven by an `ambient-codex` path component in the stored
  # target (every real install — dev `.../ambient-codex/...` or
  # marketplace `.../ambient-codex/<ver>/...` — has it; a DIFFERENT tool merely
  # named `ambient` does not). A real (non-symlink) file, or a symlink to any
  # non-ambient-codex target, is NEVER touched — never clobber a foreign
  # `ambient` the user installed themselves. readlink still reports the stored
  # target of a broken (dangling) symlink, so the same guard covers both cases.
  if [ -L "$link" ]; then
    target="$(readlink "$link" 2>/dev/null || true)"
    case "$target" in
      */ambient-codex/*)
        if [ ! -e "$link" ] || [ "$target" != "$real" ]; then
          "$real" link >/dev/null 2>&1 || true
        fi
        ;;
    esac
  fi
fi

conf="$HOME/.config/ambient/env"
[ -f "$conf" ] || exit 0
# Last assignment wins AND key/value whitespace is trimmed, matching the CLI's
# config parser (key.strip()/val.strip()) — a duplicate OR hand-spaced
# AMBIENT_DELEGATE line must not make the hook disagree with `ambient mode`.
mode="$(sed -n 's/^[[:space:]]*AMBIENT_DELEGATE[[:space:]]*=[[:space:]]*//p' "$conf" 2>/dev/null \
        | sed 's/[[:space:]]*$//' | tail -1)"
if [ "$mode" = "takeover" ]; then
  cat <<'MSG'
Ambient TAKEOVER mode is ON (persisted setting). Per the ambient skill's takeover
contract, route EVERY substantive turn through Ambient so the user spends AMBIENT
tokens, not Codex's: conversation/questions/explanations via the bundled `ask`
subcommand (use bundled `chat` only for a user-opened interactive terminal);
code via bundled `build`/`code`; reviews via bundled `audit`. Codex stays the thin
router/safety/integration layer: it briefs Ambient, runs the outbound secret
tripwire, reviews + tests + integrates the result, and keeps its own token use
minimal. Keep these with Codex (never route to Ambient): trivial one-liners; any
safety-critical/destructive/irreversible turn (auth, crypto, secret handling, rm,
force-push, migrations, prod ops); and NEVER send secrets or user/health data.
Begin each substantive turn with exactly this one line:
Ambient Takeover ON - running substantive work through Ambient; use ambient control mode off to stop.
The user turns it off with ambient control mode off.
MSG
elif [ "$mode" = "on" ]; then
  cat <<'MSG'
Ambient delegate mode is ON (persisted setting). Per the ambient skill's delegate
contract: the user plans with Codex, Ambient writes the code or audit draft, Codex
reviews and integrates. Route substantive code writing through the bundled `build`
(multi-file, manifest + --apply) or bundled `code` (single file); review every
generated diff and run the tests yourself. Trivial edits stay with Codex. The user
toggles this with ambient control mode off.
MSG
fi
exit 0
