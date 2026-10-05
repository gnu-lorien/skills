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

1. Read the spec and tickets to understand the task graph.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files - it should save its markdown notes in a directory outside the repo, accessible by all future subagents. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - calls the Skill tool with `tdd` to build the ticket;
   - merges the integration branch tip into its own branch before reporting done;
   - verifies its work using the **Verification** scope below and reports the commands run, their results, and any criteria deferred to the integration gate.

5. Once an **implementer subagent** completes, merge its work to the integration branch with a **merger subagent**. The merger runs the repo's typecheck, if available, on the merged result and resolves failures before dependent tickets start.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer subagent**.

8. Run the **integration gate**: the repo's full test suite on the integration branch after all tickets and review fixes have landed. This discharges every ticket's deferred "full suite is green" criterion. On failure, use a single **implementer subagent** to fix it and re-run the failing tests, then run the gate again. Proceed only when it passes; if verification is blocked, report the blocker and leave completion pending.

9. If a draft PR exists, mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

10. Clean up all **implementer subagent** worktrees.

## Verification

Each ticket's branch is provisional until the remaining tickets merge. Implementers run the repo's typecheck, if available, and the test files they create or edit. A ticket that requires broader testing before its dependents proceed gets that testing before it lands. Report a "full suite is green" criterion as **deferred to the integration gate**, rather than satisfied by focused tests.

The integration gate runs the full suite on the combined result, once after review fixes and again only if a failure requires changes. Use the repo's documented verification commands and ensure required fixtures and services are available; skipped required tests leave verification pending.
