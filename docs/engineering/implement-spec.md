## What it does

`implement-spec` takes a [spec](https://www.aihero.dev/ai-coding-dictionary/spec) and its [tickets](https://www.aihero.dev/ai-coding-dictionary/ticket) and lands the whole thing in one run. The orchestrating [agent](https://www.aihero.dev/ai-coding-dictionary/agent) hands each ticket to an implementer [subagent](https://www.aihero.dev/ai-coding-dictionary/subagent) working in its own git worktree, merges each finished branch into a single **integration branch**, runs [code-review](https://aihero.dev/skills-code-review) once over the result, turns its findings into tickets, and checks the full suite before resolving the tickets.

It reads the tickets as a **task graph**, not a list. Blocking edges decide what can start, so at any moment there is a **frontier** of tickets whose blockers have all landed, and every ticket on the frontier runs at once. That is the difference from working the tickets one by one. The graph's shape sets the pace, not the tickets' order on the tracker.

## When to reach for it

You invoke this by typing `/implement-spec`, and the agent won't reach for it on its own.

| Your situation | Reach for |
| --- | --- |
| A spec, split into tickets with blocking edges, that you want landed in one run | `/implement-spec` |
| One ticket at a time, in your own [context window](https://www.aihero.dev/ai-coding-dictionary/context-window), [clearing](https://www.aihero.dev/ai-coding-dictionary/clearing) between tickets | [implement](https://aihero.dev/skills-implement) |
| A spec that isn't split into tickets yet | [to-tickets](https://aihero.dev/skills-to-tickets) first |
| A small piece of work with no real graph to it | [implement](https://aihero.dev/skills-implement) directly |

## Prerequisites

- **An issue tracker.** The skill reads the tickets from, and resolves them on, the tracker [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills) configured. If none has been configured, it stops and tells you to run that first rather than guessing.
- **Tickets with blocking edges**, as [to-tickets](https://aihero.dev/skills-to-tickets) writes them. Without edges the graph is flat and every ticket starts at once.
- **A [harness](https://www.aihero.dev/ai-coding-dictionary/harness) that runs subagents in parallel and gives each one a git worktree.** The skill exists to run tickets at the same time, so on a harness that runs subagents one at a time, it is only a slower `implement`.

## The integration branch

Everything lands on one branch. Each implementer:

1. confirms its worktree is based on the integration branch before it starts,
2. builds its ticket with [tdd](https://aihero.dev/skills-tdd), red-green one slice at a time,
3. merges the integration branch tip into its own branch before reporting done, so landing it is a fast-forward.

The tracker decides whether a pull request exists at all. If your tracker closes work through PRs, or you ask for one, the skill opens a draft PR after the first merge and marks it ready at the end. Otherwise the run stops on the integration branch with every ticket resolved the way your tracker closes work, which works fully offline against a local markdown tracker.

Implementers talk to the orchestrator through [context pointers](https://www.aihero.dev/ai-coding-dictionary/context-pointer) (the spec, the ticket, shared exploration notes, earlier commits) rather than pasted summaries. This keeps each subagent's prompt small and leaves room in the orchestrator's window for the graph.

## Common questions

**Where do shared exploration notes live?**

In a dedicated task subdirectory under the operating system's official temporary directory, accessible to subsequent subagents. They stay available through implementation and review, then the agent cleans up only the files it created for that task.

**How do existing tickets get the execution profiles this skill reads?**

Run [assign-models](https://aihero.dev/skills-assign-models) on the tickets or their [wayfinder](https://aihero.dev/skills-wayfinder) map. It assigns project profiles with a blast-radius rationale and matching metadata. [to-tickets](https://aihero.dev/skills-to-tickets) assigns profiles when creating new implementation tickets. Both validate configuration; this skill checks live dispatch through preflight before starting implementation.

**Can I choose models and effort levels in both Claude Code and Codex?**

Yes. Project execution profiles map the same ticket choice to a model and effort in each harness. [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills) records these in `docs/agents/execution.json` and generates native agents plus one shared implementer contract. A ticket can use `execution:standard`, for example, while each harness uses its own configured model. Existing `model:*` and `effort:*` choices remain explicit overrides. Exact IDs stay exact; family aliases allow family selection. Unsupported choices are resolved before work starts, and review or gate fixes use a configured review-fix profile. Runtime observations are reported separately from requested settings; missing metadata is marked unknown.

| Harness | Supporting agents | Dispatch control |
| --- | --- | --- |
| Claude Code | Effort-specific Markdown definitions in `.claude/agents/` | Native agent type sets effort; the invocation selects the model |
| Codex | Model/effort-specific TOML definitions in `.codex/agents/` | Custom agent settings, or direct spawn overrides where the host exposes them |

Installing the skill alone does not install these agents. Without execution configuration, unlabelled tickets retain inherited model and effort. GPT workers run natively in Codex and Claude workers in Claude Code; dispatching across providers requires a separate launcher. Generated files are refreshed during setup without overwriting user-owned or edited agents.

**What actually checks that my account can run the selected model and effort?**

The coordinator launches a no-edit probe for each model/effort combination needed by the tickets and review fixes, through the same dispatch path it will use for implementation. It records effective settings from runtime metadata and runs the helper's `preflight` command against that evidence. Pending probes, substitutions, missing observations, stale generated definitions, and evidence from a different session or configuration block the run before branch creation. Configuration validation and model menus alone do not pass this check. If the host cannot expose effective settings, it reports that limitation and leaves configured dispatch pending. The helper checks recorded evidence; the agent launches probes and captures the runtime records.

**Does every implementer run the full test suite?**

No. During a red-green slice an implementer runs only the test it is writing; before reporting, it runs typecheck where available and each test file it created or edited, once. If a ticket names broader tests, it runs those too. A merger checks types on the combined branch before unblocking dependents. The full suite runs once, at the **integration gate**, after every ticket and the review's fix tickets have landed, because that is the result you will ship. A ticket's full-suite criterion stays deferred until that gate passes. Each gate failure becomes a fix ticket on the frontier, followed by another full-suite run; a blocked check or skipped required test keeps completion pending.

**How is this different from running `/implement` on each ticket myself?**

This is the question the skill exists to answer. Before it shipped, people kept building their own versions, and one user described the need: they wanted "subagents implement the tickets" instead of having "to individually create new session and tell them to implement a ticket one by one, when a spec may contain over 5 tickets." With `implement` you are the dispatcher: one [session](https://www.aihero.dev/ai-coding-dictionary/session) per ticket, clearing in between, and keeping track yourself of which tickets are unblocked. `implement-spec` hands that job to one orchestrating session. The price is that you no longer read each ticket's work as it lands; you review the integration branch at the end. To start a run, clear the context and type `/implement-spec` with a pointer to the spec (an issue number or a file path). For a small change with no real graph, skip it and use `implement` directly.

**Does it need GitHub? I want it to stop at the branch.**

No, not any more. One user who liked the in-progress version had exactly this complaint: "it creates a PR at the end, which requires an online repository like GitHub. I wish it could do the same work offline and stop at the branch where all the work is merged." The run now ends on the integration branch. A PR opens only when the configured tracker closes work through PRs or you ask for one, so on a local markdown tracker the run ends with every ticket resolved and the work merged on the branch.

**Its review and fix loop ran for hours, or kept "fixing" tickets that hadn't been built yet.**

Both came from running `code-review` outside the graph. One user reported a five-ticket feature where "the review and fix loop took roughly four hours". Another run sent two dozen findings, most of them refactoring smells, to a single fix subagent that worked for hours with nothing to report until it finished.

The review is now a ticket of its own, blocked by every other ticket, so it runs only once everything has landed. The orchestrator sends each finding to exactly one place by the class and reach `code-review` tags it with: defects, spec gaps, false comments and standard breaches in new code become fix tickets on the frontier; smells and changes to code the spec didn't ask to touch become follow-up tickets outside the spec; scope creep goes in the PR body for you to decide. Closing the Review ticket records that the review ran, so a spec gets one review, and nothing after it (fix tickets, gate failures, a later session) opens another. Expect that review to find real problems. The run's output is a draft that the review completes, not something to ship on its own.

**An implementer went quiet for hours.**

A subagent reports only when it finishes, so a long task is a long silence. Small tickets keep each silence short, and the implementer contract tells it to stop and report when a test still fails after two fix attempts, a single command runs past 15 minutes, or the fix needs a change outside its ticket. Some hosts also end background subagents when you send a message; there, the orchestrator dispatches the frontier in the foreground, all in one message, and checks the worktrees before telling you what earlier work did.

**Does it drive tdd like implement does?**

It does now, though it didn't at first. Users running the in-progress version noticed that "the implementer subagents don't inherit the /tdd directive", so red-green stopped as soon as they scaled up from one ticket to a whole spec. Each implementer now builds its ticket with `tdd`. There is still no step where you agree seams interactively, as there is in an `implement` session, so name the seams in the spec or the tickets if you want them pinned.

**Two implementers running in parallel collided on the same file, or picked different names for the same thing.**

Worktrees don't remove collisions; they postpone them to merge time. A blocking edge written from ticket text is a guess about which files each ticket will touch, and two tickets on "different parts of the codebase" still share a message catalogue, a config registry, or a type. Each implementer sees only its own ticket and the shared notes, never the other's work in progress, so one user's web and mobile tickets added the same string as `blockedSince` and `blockedOn`. When two frontier tickets touch one shared file, either add a blocking edge between them so they run one after the other, or have the exploration notes fix the exact names each ticket adds.

**Blocked tickets never start, even after their blocker has merged.**

This is a known problem on GitHub. The tracker's blocked-by count only drops when a blocker *closes*, and tickets typically close when the PR merges, which is the end of the run. The tracker is the right source for the starting graph but a stale one mid-run. Tell the orchestrator to track which tickets have merged into the integration branch itself and compute the frontier from that.

**Does this replace Sandcastle or an AFK script?**

No. People ask because the skills now reach into implementation: "is Sandcastle still relevant? Your skills now seem to be able to handle implementation as well." `implement-spec` puts an agent in charge of orchestration inside one harness session, which needs no infrastructure and lets you watch and steer. For work that is truly [AFK](https://www.aihero.dev/ai-coding-dictionary/afk), a deterministic loop ([Sandcastle](https://github.com/mattpocock/sandcastle), a shell script, a CI job) is faster, cheaper, and more reliable, because no agent makes the orchestration decisions.

**A ticket's key test was skipped inside its worktree, and it reported green.**

A worktree holds only what git tracks. Tests that read gitignored fixtures, local databases, or credentials can silently skip there. For a ticket whose verification depends on untracked material, tell the orchestrator to run it in the main checkout instead.

## It's working if

- Several implementers are running at once whenever the graph allows, not one after another.
- Configured execution choices resolve before a branch is created, and each dispatch records its requested model and effort.
- A ticket starts as soon as its last blocker lands on the integration branch, not when the whole run ends.
- Every ticket's trace shows `tdd` running, with a failing test before the code.
- Merges into the integration branch are fast-forwards, not conflict resolutions.
- The review runs once: its ticket closes with a comment naming every finding's destination, and only fix tickets join the PR.
- The full suite runs once on the combined integration branch, after the review's fix tickets, before the PR becomes ready or the run closes tickets.
- The run ends on one branch with every ticket resolved, and a PR only if your tracker wanted one.

## Where it fits

`implement-spec` is the build step of the main chain, as the parallel alternative to running [implement](https://aihero.dev/skills-implement) once per ticket:

```txt
grill-with-docs → to-spec → to-tickets → implement-spec → retro-matt
```

Its neighbours are [to-tickets](https://aihero.dev/skills-to-tickets), which declares the blocking edges it reads as a task graph, and [code-review](https://aihero.dev/skills-code-review), which it runs over the integration branch before closing out. [ask-matt](https://aihero.dev/skills-ask-matt) is the router over the whole set when you are not sure which flow you are in.
