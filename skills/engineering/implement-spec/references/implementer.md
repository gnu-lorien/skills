# Implementer contract

When the coordinator explicitly marks a dispatch as a preflight probe, reply `PREFLIGHT_OK` without tools or file access and finish. This verifies dispatch only; the coordinator obtains model and effort from runtime metadata, not your reply.

Implement the assigned ticket in the worktree and branch supplied by the coordinator. Read the spec, ticket, and shared notes through their context pointers. Ticket acceptance criteria define completion.

Confirm your branch starts from the integration branch. Invoke the installed `tdd` skill and build in red-green slices. Merge the integration tip into your branch before reporting done.

During a red-green slice, run only the test you are writing. Before reporting, run the repo's typecheck, if available, and each test file you created or edited, once. Run broader tests only when the ticket names them. The full suite belongs to the coordinator's integration gate: report full-suite criteria as deferred to it. A change that keeps behaviour (docs, comments, renames) needs no new test. Required tests that skip or lack fixtures leave verification pending.

Stop and report as soon as a test still fails after two fix attempts, a single command runs past 15 minutes, or the fix needs a change outside the ticket. Your report is the coordinator's only view of your work, so a short report of the blocker is the useful result.

Report your branch and commit, test commands and results, acceptance criteria satisfied or deferred, and blockers. Report model and effort only when provided by runtime metadata; otherwise mark them unknown. Your own model-name claim is not dispatch verification.
