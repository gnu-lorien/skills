---
name: implement-spec
description: "Implement the result of /to-spec and /to-tickets in code."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

**Implementer subagents** should be run in the background where possible for maximum concurrency.

## Steps

1. Read the spec and tickets to understand the task graph. Follow [Dispatch](references/dispatch.md) to resolve every ticket's execution profile or explicit model/effort overrides and the review-fix profile. For configured dispatch, run its harmless runtime probes and require the helper's `preflight` command to pass with current-session evidence before creating a branch. Missing observed model or effort blocks this check.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files. Save exploration notes in a dedicated task subdirectory under the operating system's official temporary directory, accessible to all subsequent subagents. Keep them until implementation and review are complete, then clean up only the files created for this task. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. Dispatch through the active harness's adapter with the resolved model and effort. Supply pointers to the ticket, spec, integration branch, and [implementer contract](references/implementer.md). The contract governs TDD, branch synchronization, focused verification, and reporting.

5. Once an **implementer subagent** completes, record requested and observed model/effort from available runtime metadata as described in Dispatch. Stop on a known mismatch; mark unavailable observations unknown. Merge its work to the integration branch with a **merger subagent**. The merger runs the repo's typecheck, if available, on the merged result and resolves failures before dependent tickets start.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, invoke the installed `code-review` skill on the integration branch. Fix all issues raised by the code review in a single **implementer subagent** using the configured review-fix profile and shared contract.

8. Run the **integration gate**: the repo's full test suite on the integration branch after all tickets and review fixes have landed. This discharges every ticket's deferred "full suite is green" criterion. On failure, use a single **implementer subagent** with the review-fix profile and shared contract to fix it and re-run the failing tests, then run the gate again. Proceed only when it passes; if verification is blocked, report the blocker and leave completion pending.

9. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

10. Clean up all **implementer subagent** worktrees.

## Verification

Each ticket's branch is provisional until the remaining tickets merge. The implementer contract sets ticket verification scope and reports full-suite criteria as **deferred to the integration gate**.

The integration gate runs the full suite on the combined result, once after review fixes and again only if a failure requires changes. Use the repo's documented verification commands and ensure required fixtures and services are available; skipped required tests leave verification pending.
