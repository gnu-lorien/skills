---
name: assign-models
description: Assign project execution profiles or explicit model/effort overrides to a wayfinder map's open tickets or named issues, with rationale and matching tracker metadata for Claude Code or Codex.
disable-model-invocation: true
---

The input is a wayfinder map (URL, number, or local path) or a list of tickets. Assign execution choices by **blast radius**: what goes wrong downstream if the agent gets the decision or implementation wrong. Ticket size alone is not a reason to raise a tier.

## 1. Read the project and tickets

Read `docs/agents/issue-tracker.md` and `docs/agents/execution.json`. If either is missing, tell the user to run `/setup-matt-pocock-skills` and leave assignments pending. Locate the installed `implement-spec` skill and read its `references/dispatch.md`; use its `scripts/dispatch.py` resolver without invoking that user-only skill. If those resources are missing, report that this skill requires `implement-spec`'s dispatch resources.

For a map, fetch the map and enumerate all open child tickets through the configured tracker workflow. On GitHub, paginate `gh api repos/<owner>/<repo>/issues/<map>/sub_issues`; a local map uses its linked ticket files. For named tickets, use exactly the requested set. Read each whole body, type, blockers, existing execution/model labels, and relevant code or decision records before choosing. Capture current bodies and labels so unrelated content can be preserved.

## 2. Choose an execution profile

Read `profile_guidance` in execution configuration when present, plus the map's standing preferences. Profiles are project choices, not a universal ranking of Claude and GPT models. Prefer one profile that resolves in every configured harness. Use the default for contained, reversible work with good verification; use an appropriate configured profile for shared contracts, hard-to-reverse decisions, uncertain diagnoses that gate dependents, or a wider blast radius. If profile intent is unclear, ask for that missing preference rather than infer a ranking from model names or effort values.

Preserve explicit user model/effort choices and existing consistent assignments unless the user asks to reassign them. Existing `## Model` sections and `model:*`/`effort:*` labels are explicit overrides; interpret them using the dispatch configuration's alias rules. Conflicting labels and body choices require clarification. A provider-specific override stays provider-specific: report the harnesses it cannot run in, without substituting a model from another provider. Use only configured profiles, models, aliases, and efforts; extend configuration through setup when a requested choice is missing.

For each assignment, resolve it for every configured harness with `dispatch.py resolve`, supplying `execution:<profile>` and any explicit `model:*`/`effort:*` overrides. Record the model/effort each harness resolves, or the exact incompatibility. A profile unavailable in a configured harness blocks a new portable assignment until resolved; an intentional provider-specific override can be recorded with its limitation. This is configuration validation only. Runtime access is checked by the executing session's Dispatch preflight, not by changing labels.

A HITL decision ticket still needs grounded options and a human answer. Choosing a model does not resolve the decision, invoke its skill, or authorize unattended work. This skill changes ticket metadata, not the current session's model or effort.

Give each assignment one or two sentences about the touched code or decision, blast radius, and why that profile fits. Refer to similar earlier tickets only when their actual assignment and outcome are available; never invent precedent. Ask only about unresolved conflicts or missing preferences. The user's invocation authorizes publishing routine assignments.

## 3. Write and verify ticket metadata

Use the same representation as `to-tickets`:

```markdown
## Execution

Profile: <configured profile>
Reason: <the ticket's blast radius and why this profile fits>
```

For explicit overrides add `Model: <configured model or alias>` and/or `Effort: <value>` on their own lines. Add `execution:<profile>` and only the corresponding explicit `model:*`/`effort:*` labels on trackers with labels. The profile's per-harness models belong in configuration and the final report, not as contradictory provider-specific labels on a portable ticket.

Update the existing Execution section in place, or replace the legacy Model section while preserving its explicit choices and rationale. Otherwise insert below parent/map references and above Question or What to build. Preserve all unrelated body text, labels, status, parent relationships, and blocking edges. Remove only superseded execution/model/effort labels for an authorized reassignment. Create missing assignment labels through the configured tracker workflow before applying them; keep their spelling consistent with configuration. For GitHub edits, pass the complete body through a temporary file with `--body-file`, and single-quote labels when invoking native commands from PowerShell.

Read each body and label set back after mutation and check that they agree with the resolved assignment and preserved content. Record failures per ticket; never claim the whole set is assigned if some writes failed.

## 4. Keep a map's standing note current

For map input, add or update one execution-assignment bullet in `## Notes`, before any Handoff line. Preserve other notes. Replace only the old model-assignment bullet and its tier guide when migrating from the source convention:

```markdown
- **Every ticket on this map names its execution choice.** Each child ticket gets an Execution section with its configured profile and a reason based on blast radius, plus matching execution labels where supported. Explicit model/effort overrides stay explicit. This also applies to tickets graduated later and implementation tickets derived through to-spec and to-tickets. Use this project's execution profiles and profile guidance; do not invent provider rankings. The session that creates a ticket assigns the metadata directly, and the session that works it honors the resolved settings and performs Dispatch preflight before configured agent dispatch. HITL tickets keep human decisions with the human.
```

This standing note instructs creators directly; it does not implicitly invoke `assign-models`. Read the updated map back and enumerate its open children again. If new children appeared during the run, assign them too or report them pending.

## Done when

Every requested ticket (or every open child on the map) has a consistent Execution section and matching labels where supported, a grounded reason, and a configuration-valid assignment. A map also has one current standing note. Report one table: linked ticket name, profile/overrides, resolved Claude Code and/or Codex model/effort, reason, and any pending verification or compatibility limits. For local files, use clickable ticket paths. Do not claim runtime availability or live preflight passed from resolver output alone.
