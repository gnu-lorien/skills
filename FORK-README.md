# Fork: pushed evidence before a ticket closes

A fork of [mattpocock/skills](https://github.com/mattpocock/skills) carrying one
behavioural change to `/wayfinder`, plus a hook that enforces it.

Everything else tracks upstream. `upstream` is wired as a remote, so
`git fetch upstream && git merge upstream/main` pulls new skills in.

## The problem

Wayfinder's resolve step read like this:

> Record the resolution: post the answer as a **resolution comment**, **close**
> the issue, and **append a context pointer** to the map's Decisions-so-far.

Three tracker operations. No repo operation anywhere in the list. So when a map
carries execution — which is exactly when a ticket produces an artifact — an
agent can follow that step literally, write a resolution saying *"recorded in
`CONTEXT.md`"*, close the ticket, and never commit the file.

Anyone opening that closed issue then has a **claim and no artifact**. They
cannot see your working tree. In the worst case the file is never committed at
all and the resolution is simply false.

This is not hypothetical — it is what prompted the fork. A wayfinder ticket was
closed asserting a glossary entry that existed only as an uncommitted local
edit, and the gap only surfaced because a human asked "is this pushed?".

The skill *almost* covers it. It already says:

> Assets created while resolving a ticket are linked from the issue, not pasted
> in.

But that line sits in the ticket-body section, it is passive, and it never says
that a repo change counts as an asset or that the link is a precondition of the
close. It reads as "don't paste big files inline".

## The change

The framing added throughout: **a resolution comment is a claim; a pushed commit
is the evidence.** The push becomes a precondition of the close, not a follow-up.

Six edits, in five files:

| File | Change |
| --- | --- |
| `skills/engineering/wayfinder/SKILL.md` | Resolve step (step 4) now requires commit + push + a commit link *before* comment/close, and says to leave the ticket open if the change is not ready to commit |
| `skills/engineering/wayfinder/SKILL.md` | The "assets are linked from the issue" line now states that a repo change **is** such an asset, its commit is the link, and it is pushed before the close |
| `…/setup-matt-pocock-skills/issue-tracker-github.md` | `Resolve` recipe gains the `git commit` / `git push` step ahead of `gh issue comment` |
| `…/setup-matt-pocock-skills/issue-tracker-gitlab.md` | Same, ahead of `glab issue note` |
| `…/setup-matt-pocock-skills/issue-tracker-local.md` | Same — and it matters *more* here, since the map and tickets are themselves repo files |
| `docs/engineering/wayfinder.md` | The prose summary of a session now mentions committing and linking |

Note the tracker files are **templates**. `/setup-matt-pocock-skills` copies the
matching one into a consuming repo as `docs/agents/issue-tracker.md`. Patching
only the generated copy in your project gets silently reverted the next time
setup runs — which is the main reason this fork exists rather than a local edit.

## The hook

Docs you have to read carefully are a weak guarantee. `hooks/block-issue-close-when-dirty.py`
makes the rule mechanical: a `PreToolUse` hook that **denies** an issue-close
invocation while the working tree is dirty or the branch has unpushed commits,
and prints exactly what is outstanding.

It checks both, deliberately. A clean tree is not evidence either if the commits
never left the machine.

### Install it in a project

1. Copy the script in:

   ```bash
   mkdir -p .claude/hooks
   curl -fsSL https://raw.githubusercontent.com/gnu-lorien/skills/main/hooks/block-issue-close-when-dirty.py \
     -o .claude/hooks/block-issue-close-when-dirty.py
   ```

2. Wire it into `.claude/settings.json` (merge with any existing `hooks` block —
   do not replace the file):

   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Bash",
           "hooks": [
             {
               "type": "command",
               "command": "python \"${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/block-issue-close-when-dirty.py\"",
               "shell": "bash",
               "timeout": 20,
               "statusMessage": "Checking for uncommitted evidence"
             }
           ]
         }
       ]
     }
   }
   ```

   Project settings (`.claude/settings.json`) applies it to everyone working in
   the repo; `.claude/settings.local.json` keeps it to you.

3. Verify it fires. This is harmless — it is only an `echo` — but a working hook
   must block it while your tree is dirty:

   ```bash
   echo "gh issue close 99999 -- only an echo"
   ```

   If nothing is blocked, open `/hooks` once to reload settings, or restart.
   Claude Code only watches directories that already had a settings file when
   the session started.

### How it works

Roughly 60 lines of dependency-free Python. No `jq` — it is not reliably on PATH
on Windows/Git Bash, and this needs to run everywhere.

1. Read the hook payload from stdin and pull out `.tool_input.command`.
2. Bail out silently unless that command actually *invokes* an issue close.
3. Collect reasons: `git status --porcelain` for uncommitted changes, and
   `git rev-list --count @{u}..HEAD` for unpushed commits (skipped when the
   branch has no upstream).
4. No reasons — exit 0, silent, tool proceeds. Otherwise emit
   `permissionDecision: "deny"` with a reason listing what is outstanding.

Any git failure exits 0. A guard that breaks your session when you are not in a
repo is worse than no guard.

### The one subtlety: anchoring

The naive trigger is a plain substring search. Don't — it fires on any command
that merely *mentions* the phrase, and it will bite you immediately:

- it blocked the edit script that was adding a feature to the hook, because that
  script contained a test fixture with the phrase in it;
- then it blocked the commit whose message described what the hook does.

So the pattern is anchored to a **command position** — start of string, a
newline, or just after a shell operator:

```python
CLOSE = re.compile(r"(?:\A|[\n;&|(])\s*(?:gh|glab)\s+issue\s+close\b")
```

| Command | Verdict |
| --- | --- |
| `gh issue close 5` | deny |
| `git push && gh issue close 5` | deny |
| `git push; gh issue close 5` | deny |
| `git push` ⏎ `gh issue close 5` | deny |
| `git commit -m "note about the gh issue close step"` | allow |
| a heredoc writing docs that mention the command | allow |

Writing *about* the command stays possible; running it does not.

### Known sharp edge

The hook blocks on **any** dirt, not only dirt related to the ticket. When the
outstanding files are unrelated, the fix is to say so and re-run. That is a
deliberate trade: a warning you can ignore is not a guarantee. If you would
rather it only warn, swap `permissionDecision` from `"deny"` to `"ask"`.

## Using this fork

The skills are plain markdown, so consume them however you already do — vendor
`skills/engineering/**` into your project's `.claude/skills/`, or point your
plugin marketplace config at this repo. Re-run `/setup-matt-pocock-skills` after
updating so `docs/agents/issue-tracker.md` is regenerated from the fixed
template.

## Upstreaming

The doc change is small and self-contained and would suit a PR to
`mattpocock/skills`. The hook is Claude-Code-specific and is probably better
kept here.
