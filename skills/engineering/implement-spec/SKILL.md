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

All implementation work is a ticket on the frontier, including the review and every fix after it, so each one has acceptance criteria, a merge point and a report.

Dispatch every **frontier** ticket in one message, so the **implementer subagents** run concurrently. Background dispatch lets you merge each one as it finishes; use it only where background agents survive the user's next message.

## Steps

1. Read the spec and tickets to understand the task graph. Follow [Dispatch](references/dispatch.md) to resolve every ticket's execution profile or explicit model/effort overrides and the review-fix profile. For configured dispatch, run its harmless runtime probes and require the helper's `preflight` command to pass with current-session evidence before creating a branch. Missing observed model or effort blocks this check. If the graph has no **Review ticket**, add one through the issue tracker: a ticket under the spec, blocked by every other ticket, that you work yourself in step 7.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files. Save exploration notes in a dedicated task subdirectory under the operating system's official temporary directory, accessible to all subsequent subagents. Keep them until implementation and review are complete, then clean up only the files created for this task. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. Dispatch through the active harness's adapter with the resolved model and effort. Supply pointers to the ticket, spec, integration branch, and [implementer contract](references/implementer.md). The contract governs TDD, branch synchronization, focused verification, and reporting.

5. Once an **implementer subagent** completes, record requested and observed model/effort from available runtime metadata as described in Dispatch. Stop on a known mismatch; mark unavailable observations unknown. Merge its work to the integration branch with a **merger subagent**. The merger runs the repo's typecheck, if available, on the merged result and resolves failures before dependent tickets start.

6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.

7. When the **Review ticket** reaches the frontier, work it yourself: invoke the installed `code-review` skill on the integration branch, then send every finding to exactly one destination by its class and reach:
   - **Fix ticket**, under the spec, joining the frontier: `defect`, `spec-gap`, `comment`, and `standard` with reach `new`. Slice them like any ticket: one coherent change each, with acceptance criteria naming the tests that verify it, dispatched with the review-fix profile. Batch the `comment` findings into one ticket.
   - **Follow-up ticket**, outside the spec, blocking nothing, left open by the PR: `smell`, `standard` with reach `existing`, and any change to code the spec didn't ask to change. Group them by area.
   - **The PR body**: `scope`, for the human reviewer to decide.
   - **Dropped**: a finding you judge wrong, with the reason.

   Close the Review ticket with a comment naming the reviewed commit and every finding's destination. The closed Review ticket is the record that the review ran: **a spec gets one review**. Fix tickets, gate failures and later sessions all go through the frontier, and none of them opens another review.

8. Run the **integration gate** once the frontier is empty and the Review ticket is closed: the repo's full test suite on the integration branch. This discharges every ticket's deferred "full suite is green" criterion. Each failure becomes a fix ticket per root cause, worked through the frontier; when the frontier empties again, run the gate again. Proceed only when it passes; if verification is blocked, report the blocker and leave completion pending.

9. If a draft PR exists, add the fix tickets to its closing references and mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

10. Clean up all **implementer subagent** worktrees.

## Verification

Each ticket's branch is provisional until the remaining tickets merge. The implementer contract sets ticket verification scope and reports full-suite criteria as **deferred to the integration gate**.

The integration gate runs the full suite on the combined result, once after the review's fix tickets and again only after a failure's fix tickets. Use the repo's documented verification commands and ensure required fixtures and services are available; skipped required tests leave verification pending.
