## What it does

`assign-models` assigns execution profiles to existing [tickets](https://www.aihero.dev/ai-coding-dictionary/ticket), either a named set or the open children of a [wayfinder](https://aihero.dev/skills-wayfinder) map. It reads each ticket and the code or decisions it touches, then records a profile, a reason, and matching tracker metadata. The choice follows **blast radius**: what depends on getting this work right, rather than how large the ticket looks.

Profiles live in the project configuration. The same profile can resolve to a Claude model in Claude Code and a GPT model in Codex, with an effort level for each. This skill assigns those choices to tickets; it does not change the current session's model, implement the tickets, or claim that a model is available to your account.

## When to reach for it

You invoke this by typing `/assign-models`, and the agent won't reach for it on its own.

| Your situation | Reach for |
| --- | --- |
| Existing tickets or a map need execution choices and rationale | `/assign-models` with a map or ticket references |
| New implementation tickets need splitting and execution profiles | [to-tickets](https://aihero.dev/skills-to-tickets) |
| Project model choices or supporting agents need configuring | [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills) |
| Assigned implementation tickets are ready to run as a task graph | [implement-spec](https://aihero.dev/skills-implement-spec) |

## Prerequisites

The project needs a configured issue tracker and `docs/agents/execution.json`. The installed `implement-spec` skill supplies the shared dispatch resolver and rules; `assign-models` reads those resources without invoking it. Optional `profile_guidance` records what each project profile is intended for. Setup establishes these choices before tickets are assigned.

## Blast radius and portable choices

A short change to a shared contract can deserve a different profile from a long, contained content ticket. The rationale names the touched code or decision and what depends on it. Earlier tickets count as precedent only when their assignments and outcomes are available.

| Assignment | What it means |
| --- | --- |
| Execution profile | Resolves to a configured model and effort in each supported harness |
| Explicit model/effort override | Preserves the requested provider and reports incompatible harnesses |
| Human decision ticket | Keeps the answer with the human, regardless of assigned model |

For a map, the skill also leaves a standing note so later tickets carry execution choices. It preserves unrelated notes, parent links, blocking edges, labels, and ticket content. Local markdown trackers use the same Execution section without requiring labels.

## Common questions

**Can I use this with Claude Code and Codex?**

Yes. It selects project profiles and validates their configured resolution in both harnesses. Native agent dispatch and live access checks belong to the executing session. A ticket with an explicit Claude override remains Claude-specific; the skill reports the Codex incompatibility rather than replacing the model.

**What happens to existing Model sections and model/effort labels?**

Consistent assignments are preserved unless you request reassignment. Legacy Model sections become Execution sections with the explicit choices retained. Labels and body must agree, so conflicting choices require clarification. A portable profile gets an execution label; provider-specific model labels are used only for explicit overrides.

**Does successful assignment prove that the model is available?**

No. The resolver checks project configuration. [implement-spec](https://aihero.dev/skills-implement-spec) checks live dispatch using no-edit probes and runtime evidence before creating an integration branch. Missing observed model or effort leaves configured dispatch pending. Assigning a profile also does not switch the model of the session reading the ticket.

## It's working if

- Each ticket names an execution choice and explains its blast radius.
- The report shows the configured Claude Code and Codex choices, or an explicit compatibility limit.
- Ticket bodies and labels agree, and unrelated content and relationships remain intact.
- A map has one standing assignment note that also covers future tickets.
- Pending writes or live verification are reported plainly rather than hidden behind a success claim.

## Where it fits

`assign-models` is a reach-for-it-anytime maintenance step for existing tickets, including [wayfinder](https://aihero.dev/skills-wayfinder) decision maps. [to-tickets](https://aihero.dev/skills-to-tickets) assigns profiles while creating new implementation tickets; [implement-spec](https://aihero.dev/skills-implement-spec) resolves their choices and runs the implementation graph. [ask-matt](https://aihero.dev/skills-ask-matt) routes you when you are unsure which flow fits.
