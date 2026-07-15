"""Argument-parser construction for Ambient's largest workflow commands."""

import argparse


def add_common_flags(parser, *, default_timeout_s, max_parallel_chunks):
    """Add model, budget, fallback, cache, and progress controls."""
    parser.add_argument(
        "-m", "--model", default=None, metavar="ID",
        help="model id for this run only (see: ambient-codex models); overrides "
             "the sticky default. 'auto' delegates: cheapest READY model that "
             "fits the input, resolved per call and printed "
             "(auto:cheapest / auto:largest)")
    parser.add_argument(
        "--reduce-model", default=None, metavar="ID",
        help="model for the map-reduce SYNTHESIS step only (cheap map, strong "
             "reduce); default: the same model as the map step")
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="output token budget (default: auto-sized per model; reasoning "
             "models get more so thinking AND the answer both fit)")
    parser.add_argument("--temperature", type=float, default=0.1,
                        help="sampling temperature 0.0-2.0 (default 0.1)")
    parser.add_argument(
        "--timeout", type=int, default=default_timeout_s,
        help="per-call SILENCE timeout in seconds — data flow resets it; not "
             "a total cap (default 300)")
    parser.add_argument("--raw", action="store_true",
                        help="print full JSON response")
    parser.add_argument(
        "--fallback", action="store_true",
        help="auto-retry on the first READY model if the chosen one isn't "
             "serving right now (or set AMBIENT_FALLBACK=on)")
    parser.add_argument(
        "--allow-partial", action="store_true",
        help="accept an incomplete result (some chunks failed/truncated) with "
             "exit 0 instead of the default loud non-zero exit")
    parser.add_argument(
        "--allow-large-input", dest="allow_cost", action="store_true",
        help="audit an oversized repo anyway — proceed past the built-in "
             "input-size ceiling, keeping the files that fit")
    parser.add_argument("--allow-cost", dest="allow_cost", action="store_true",
                        help=argparse.SUPPRESS)
    parser.add_argument("--yes", "-y", action="store_true",
                        help="skip interactive confirmation prompts")
    parser.add_argument(
        "--no-cache", action="store_true",
        help="don't reuse cached chunk results from a previous run (map-reduce)")
    parser.add_argument(
        "--cache-ttl", type=int, default=None, metavar="SECONDS",
        help="max age of a reusable cached chunk (default 7 days)")
    parser.add_argument(
        "--parallel", type=int, default=None, metavar="N",
        help="max concurrent chunk/model calls, 1-16 (default "
             f"{max_parallel_chunks}; or set AMBIENT_MAX_PARALLEL)")
    parser.add_argument(
        "--progress", dest="progress", action="store_true",
        default=argparse.SUPPRESS,
        help="force the live progress display on (heartbeat + build phase "
             "lines); default on (or AMBIENT_PROGRESS=on)")
    parser.add_argument(
        "--no-progress", dest="progress", action="store_false",
        default=argparse.SUPPRESS,
        help="silence the streamed progress display — the smart stall/hard-wall "
             "timeout still runs (or AMBIENT_PROGRESS=off)")


def add_best_of_flag(parser, *, best_of_max):
    parser.add_argument(
        "--best-of", type=int, default=None, metavar="K", dest="best_of",
        help=f"draw K independent samples (2-{best_of_max}) at temperature>0 "
             "and pick/corroborate the best — quality from cheap samples "
             "(cache-resumable across re-runs)")


def configure_audit(sub, *, add_common, add_best_of):
    p = sub.add_parser(
        "audit", help="second-opinion code audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  git diff | ambient-codex audit
  ambient-codex audit src/pay.py --focus security --format report
  ambient-codex audit --staged --json
  ambient-codex audit src/*.py --dry-run       (plan, nothing sent)
  ambient-codex audit --repo . --focus security   (whole repo — git-aware walker)
  ambient-codex audit app.py --consensus moonshotai/kimi-k2.7-code,z-ai/glm-5.2""")
    p.add_argument("paths", nargs="*",
                   help="files to audit (or pipe a diff on stdin)")
    p.add_argument(
        "--repo", metavar="DIR", nargs="?", const=".",
        help="audit a whole repository/directory (default .): text source files "
             "via git ls-files (.gitignore respected) or a safe walk; binaries, "
             "lockfiles and vendored dirs skipped; file count, input size "
             "reported BEFORE anything is sent")
    p.add_argument(
        "--deep", dest="deep", action="store_true", default=None,
        help="after a chunked audit, run ONE bounded cross-file confirmation "
             "pass over files pass-1 flagged across chunks (default: on for "
             "--repo, off otherwise)")
    p.add_argument("--no-deep", dest="deep", action="store_false",
                   help="skip the cross-file confirmation pass")
    p.add_argument("--focus", help="e.g. 'security', 'concurrency'")
    p.add_argument("--allow-secrets", action="store_true",
                   help="bypass the credentials tripwire (false positives only)")
    p.add_argument(
        "--format", choices=["prose", "json", "report"], default="prose",
        help="prose (default) | json (machine-readable findings) | report "
             "(clean findings table)")
    p.add_argument("--json", dest="format", action="store_const", const="json",
                   help="shorthand for --format json")
    p.add_argument("--dry-run", action="store_true",
                   help="show the plan (model, chunks) and exit — no call")
    p.add_argument(
        "--staged", action="store_true",
        help="audit `git diff --cached` WITH full context of each changed file")
    p.add_argument(
        "--diff", metavar="REF", nargs="?", const="HEAD",
        help="audit `git diff REF` (default HEAD) with full changed-file context")
    p.add_argument(
        "--consensus", metavar="M1,M2",
        help="audit with several models and rank findings corroborated by 2+ "
             "first (`ambient-codex models` shows what's serving)")
    p.add_argument(
        "--install-hook", metavar="HOOK", nargs="?", const="pre-commit",
        choices=["pre-commit", "pre-push"], dest="install_hook",
        help="install a FIXED git hook that runs `ambient-codex audit` on the "
             "staged/outgoing diff and blocks on verdict FIX FIRST (default: "
             "pre-commit; needs no API key)")
    p.add_argument(
        "--uninstall-hook", metavar="HOOK", nargs="?", const="pre-commit",
        choices=["pre-commit", "pre-push"], dest="uninstall_hook",
        help="remove the ambient-installed git hook (only ours — a foreign hook "
             "is never touched)")
    p.add_argument(
        "--force", action="store_true",
        help="with --install-hook: replace an existing non-ambient hook (the "
             "original is backed up to <hook>.pre-ambient.bak)")
    add_best_of(p)
    add_common(p)


def configure_map(sub, *, add_common):
    p = sub.add_parser(
        "map", help="bulk lane: run ONE prompt independently over MANY items "
                    "(files or stdin lines), streaming one result per item",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  ambient-codex map "summarize this file in one sentence" src/*.py
  cat titles.txt | ambient-codex map "classify: bug, feature, or question?"
  cat q.jsonl | ambient-codex map "answer concisely" --jsonl --json
Each item is ONE single-shot call (the prompt is the system instruction,
the item is the user message). Output streams per item as it completes —
under --json as JSONL (one envelope per line, always carrying the item id).
Re-runs serve finished items from the cache and re-bill only the missing
ones.""")
    p.add_argument("prompt", help="the instruction applied INDEPENDENTLY to each item")
    p.add_argument(
        "paths", nargs="*", help="files — each file is ONE item (glob via your "
                                  "shell); omit to read one item per stdin line")
    p.add_argument(
        "--jsonl", action="store_true",
        help='stdin lines are JSON objects: {"input": "...", "id": ...} '
             "(id optional; falls back to the line's item index)")
    p.add_argument("--json", action="store_true",
                   help="emit one JSON envelope per item (JSONL) instead of prose")
    p.add_argument("--allow-secrets", action="store_true",
                   help="bypass the credentials tripwire (false positives only)")
    add_common(p)


def configure_build(sub, *, add_common):
    p = sub.add_parser(
        "build", help="plan + generate a set of files from a task "
                      "(manifest-first; never executes anything)")
    p.add_argument("task", nargs="*", help="what to build, in plain words")
    p.add_argument(
        "--dir", default=None, metavar="DIR",
        help="target directory (default: current dir; REQUIRED for headless --apply)")
    p.add_argument("-f", "--context", action="append", metavar="FILE",
                   help="context file the build should match (repeatable)")
    p.add_argument("--apply", action="store_true",
                   help="write the generated files into --dir (default: manifest only)")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing files (originals saved to "
                        ".ambient-build.bak/)")
    p.add_argument("--plan-only", action="store_true",
                   help="run just the cheap planning call, print the plan, stop")
    p.add_argument("--dry-run", action="store_true",
                   help="show model/budget/caps with NO API calls")
    p.add_argument("--max-files", type=int, default=32,
                   help="cap on planned files (default 32)")
    p.add_argument("--max-file-bytes", type=int, default=200_000,
                   help="cap on one generated file (default 200,000)")
    p.add_argument("--no-resume", action="store_true",
                   help="ignore a previous interrupted run's cached plan/files")
    p.add_argument("--json", action="store_true",
                   help="emit the machine-readable manifest envelope")
    p.add_argument("--allow-secrets", action="store_true",
                   help="bypass the credentials tripwire (false positives only)")
    add_common(p)


__all__ = ("add_common_flags", "add_best_of_flag", "configure_audit",
           "configure_map", "configure_build")
