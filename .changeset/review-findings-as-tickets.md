---
"mattpocock-skills": minor
---

`implement-spec` turns its review into tickets. The review is now a **Review ticket**, blocked by every other ticket, that the orchestrator works itself once everything has landed. `code-review` tags each finding with a class (`defect`, `spec-gap`, `scope`, `comment`, `standard`, `smell`) and a reach (`new` or `existing` code), and the orchestrator routes each one: fix tickets on the frontier for defects, spec gaps, false comments and standard breaches in new code; follow-up tickets outside the spec for smells and unrequested changes; the PR body for scope creep. Closing the Review ticket records that the review ran, so a spec gets one review. Gate failures become fix tickets too, so no step hands a pile of findings to a single implementer.

The implementer contract runs each test once (only the test being written during a slice, each touched test file before reporting) and leaves the full suite to the integration gate. It also stops and reports when a test still fails after two attempts, a command runs past 15 minutes, or the fix needs a change outside the ticket. `implement-spec-serial` gets the same Review ticket.
