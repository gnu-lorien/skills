"""PreToolUse guard: refuse to close a tracker ticket without pushed evidence.

A resolution comment is a claim; a pushed commit is the evidence. Closing a
ticket whose resolution asserts work that exists only on this machine leaves a
reader of that closed ticket no way to verify it happened.
"""

import json
import re
import subprocess
import sys

# Anchored to a command position (string start, newline, or just after a shell
# operator) so a mere mention of the phrase -- in a commit message, a heredoc,
# a doc edit -- is not mistaken for an invocation.
CLOSE = re.compile(r"(?:\A|[\n;&|(])\s*(?:gh|glab)\s+issue\s+close\b")


def git(*args):
    """Return stripped stdout, or None if the git command failed."""
    try:
        result = subprocess.run(
            ("git",) + args, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> int:
    try:
        command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    if not CLOSE.search(command or ""):
        return 0

    reasons = []
    dirty = git("status", "--porcelain")
    if dirty:
        reasons.append("Uncommitted changes:\n" + dirty)

    # A clean tree is not evidence either if the commits never left the machine.
    if git("rev-parse", "--abbrev-ref", "@{u}") is not None:
        ahead = git("rev-list", "--count", "@{u}..HEAD")
        if ahead and ahead != "0":
            log = git("log", "--oneline", "@{u}..HEAD") or ""
            reasons.append("Unpushed commits (%s):\n%s" % (ahead, log))

    if not reasons:
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Refusing to close the ticket: its evidence is not on the "
                    "remote yet.\n\nIf any of this is the artifact the "
                    "resolution claims, commit and push it first, then link the "
                    "commit in the resolution comment. If none of it is related, "
                    "say so and re-run.\n\n" + "\n\n".join(reasons)
                ),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
