---
name: implement-spec-serial
description: "Implement the result of /to-spec and /to-tickets in code, one ticket at a time."
disable-model-invocation: true
---

You have been provided a spec. This spec should have tickets associated with it, describing how to implement the spec.

The issue tracker should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

The goal is the entire spec implemented on a single **integration branch**, with every ticket resolved the way the issue tracker closes work.

The tickets are not a list of steps. They are a **task graph** with blocking relationships between them. This means there is always a **frontier** of tickets which are ready to be grabbed.

Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don't duplicate information already available via pointers.

All implementation work is a ticket on the frontier, including the review and every fix after it, so each one has acceptance criteria, a merge point and a report.

**Implementer subagents** should be run serially. Use **minimum concurrency**: run at most one **implementer subagent** at a time. Run it in the background only where background agents survive the user's next message.

## Steps

1. Read the spec and tickets to understand the task graph. If the graph has no **Review ticket**, add one through the issue tracker: a ticket under the spec, blocked by every other ticket, that you work yourself in step 7.

2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the exploration subagent can save files. Save exploration notes in a dedicated task subdirectory under the operating system's official temporary directory, accessible to all subsequent subagents. Keep them until implementation and review are complete, then clean up only the files created for this task. This lets **implementer subagents** focus on implementation rather than exploration.

3. Create the integration branch. If the issue tracker closes work through PRs, or the user asks for one, open a draft PR after the first merge in step 5 (a branch with no commits ahead of main can't open one), marked as closing the spec and tickets.

4. Use a single **implementer subagent** to implement one **frontier** ticket, in its own worktree on its own branch. Each implementer subagent:
   - confirms its worktree is based on the integration branch before starting, and resets onto it if not;
   - calls the Skill tool with `tdd` to build the ticket;
   - merges the integration branch tip into its own branch before reporting done

5. Once an **implementer subagent** completes, merge its work to the integration branch with a **merger subagent**.

6. If this changes the **frontier** of available tickets, ensure they will be considered for the next **implementer subagent**. Kick off the next one only after the previous one's work is merged.

7. When the **Review ticket** reaches the frontier, work it yourself: call the Skill tool with `code-review` on the integration branch, then send every finding to exactly one destination by its class and reach:
   - **Fix ticket**, under the spec, joining the frontier: `defect`, `spec-gap`, `comment`, and `standard` with reach `new`. Slice them like any ticket: one coherent change each, with acceptance criteria naming the tests that verify it. Batch the `comment` findings into one ticket.
   - **Follow-up ticket**, outside the spec, blocking nothing, left open by the PR: `smell`, `standard` with reach `existing`, and any change to code the spec didn't ask to change. Group them by area.
   - **The PR body**: `scope`, for the human reviewer to decide.
   - **Dropped**: a finding you judge wrong, with the reason.

   Close the Review ticket with a comment naming the reviewed commit and every finding's destination. The closed Review ticket is the record that the review ran: **a spec gets one review**. Fix tickets and later sessions go through the frontier, and none of them opens another review.

8. If a draft PR exists, add the fix tickets to its closing references and mark it ready for review. Otherwise, resolve each ticket the way the issue tracker closes work, and report the integration branch.

9. Clean up all **implementer subagent** worktrees.
