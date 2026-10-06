# Execution profiles and dispatch

Read the target project's `docs/agents/execution.json`. If absent, retain inherited model/effort for unlabelled tickets and review fixes. A ticket with execution/model/effort metadata requires configuration first; direct the user to `/setup-matt-pocock-skills`. Skill installation alone does not install native agents.

## Configuration

Use `execution.example.json` as a starting point, not an availability guarantee. Setup verifies each configured model and effort against the installed client and account. Remove unsupported rows or adjust them before generating agents. `models` is the project's approved capability list, not a live discovery service. Refresh it when clients or models change.

Each profile maps harness names to a model and effort. `default_profile` applies to tickets without a profile; `review_fix_profile` applies to review and integration-gate fixes. Model keys may be family aliases or full IDs. Full IDs request that exact model; family aliases permit the family's runtime resolution. `aliases` explicitly maps legacy ticket spellings to a configured key. Map a versioned label to a family alias only when the user accepts family selection; otherwise configure the exact full ID.

Optional `profile_guidance` maps profile names to their intended use, based on blast radius or other project criteria. `to-tickets` uses it for new tickets; the user-invoked `assign-models` skill uses it for existing tickets and maps. Guidance describes purpose, not a cross-provider strength ranking. Assignment validates configuration but does not establish runtime access; preflight below does that for configured dispatch.

Tickets carry `execution:<profile>` labels on a real tracker and `## Execution` with `Profile: <profile>` in their bodies (a local ticket uses the same section). Existing `model:*` and `effort:*` labels remain explicit overrides. If body and labels disagree, or multiple values exist for a field, resolve the conflict with the user before creating a branch. Preserve an explicitly requested provider; never translate a Claude model to GPT or vice versa.

Use Python 3.11 or newer to run the helper from this skill's `scripts/dispatch.py`:

```text
python <skill>/scripts/dispatch.py resolve --config docs/agents/execution.json --harness codex --label execution:standard
python <skill>/scripts/dispatch.py resolve --config docs/agents/execution.json --harness claude-code --label model:opus --label effort:xhigh
python <skill>/scripts/dispatch.py resolve --config docs/agents/execution.json --harness codex --review-fix
python <skill>/scripts/dispatch.py generate --config docs/agents/execution.json --project .
```

The helper outputs a resolved native agent name, model, and effort, or fails without substituting another value. It validates configuration but cannot establish account access or runtime support. Pass normalized body metadata as the same `--label` inputs only after checking agreement. Generate again after configuration or contract changes; the generator refreshes only its unchanged owned files. It refuses collisions and edited generated files. Stale generated definitions remain on disk but are no longer selected by the resolver.

## Preflight

The coordinator runs this procedure before creating the integration branch. Setup uses it for the default and review-fix profiles in the active harness. Other harnesses stay unverified until checked in their own client. Model menus, documentation, and config validation alone do not establish account access.

1. Record the active host name/version and inspect its actual dispatch tool schema. Use the client version command only for the client actually doing dispatch (`claude --version` or `codex --version` for those CLIs); a wrapper host needs its own version. Confirm native agent discovery or explicit model/effort controls. Capture the schema or discovery output in a task directory under the OS temp directory, without credentials.
2. Make a temporary `tickets.json`: a JSON array with one object per ticket, such as `[{"labels": ["execution:standard"]}]`. Include normalized body overrides after checking label agreement. Generate a fresh UUID run nonce for this attempt and retain it throughout the check. Run `preflight-plan` below. It deduplicates ticket combinations and includes review fixes automatically; setup uses an empty array to probe review fixes and adds the default profile explicitly.
3. Inspect model/effort support through the host's available model metadata and tool controls. Unsupported combinations block here. For every combination in the plan, dispatch one short-lived subagent through the same native definition or direct controls intended for implementation, with the exact resolved model and effort. Use a fresh or bounded context if required. Send: `This is a preflight probe. Reply PREFLIGHT_OK without tools, file access, or changes, then finish.` Do not pass tickets, secrets, or repo content. Wait for the probe to finish and close it when the host supports closing. A probe is a small model call using the current account, not an API call under a different credential.
4. Fill the plan's probe entries from trusted runtime task/session metadata. Set `status` to `completed` only after successful completion; record the probe reply in `response` (it must be `PREFLIGHT_OK`), `observed_model`, `observed_effort`, `mode` (`native` or `direct`), and `runtime_evidence` pointing to the captured metadata or transcript event ID. Record every substitution with `substitution: true`, including silent fallback or effort clamping. Claude Code exposes task model/effort in `/tasks` on supported releases; inspect that task's metadata, not the model menu. Codex hosts differ: use their task/session metadata or spawn result only when it reports effective settings, not merely echoed request parameters. A model's self-report is not evidence. Missing effective model or effort leaves status `unverified` and blocks configured dispatch.
5. Run `preflight` with the evidence and the same nonce/client. It checks current config and generated-artifact hashes, selected native definitions (or the shared contract in direct mode), probe coverage, completion, model/effort matches, and evidence references. It exits nonzero on failure. Only `status: passed` allows the branch to be created. This checks the evidence record; the coordinator remains responsible for capturing it truthfully from the runtime.

```text
python <skill>/scripts/dispatch.py preflight-plan --config docs/agents/execution.json --harness codex --tickets <temp>/tickets.json --session <run-uuid> --client <host-and-version>
python <skill>/scripts/dispatch.py preflight --config docs/agents/execution.json --harness codex --tickets <temp>/tickets.json --session <run-uuid> --client <host-and-version> --evidence <temp>/evidence.json --project . --mode native
```

Save the first command's JSON output as the evidence skeleton using structured file writing; initially every probe is pending. Use `--mode direct` only when both settings are supplied through supported direct controls. Native agent definitions must match the current generator output. Generated Codex definitions pin both settings and take precedence over spawn overrides, so use the selected definition consistently.

Re-run in each new implementation session and after changing configuration, definitions, client, account, or dispatch mode. Evidence is temporary and must not be committed or reused under a new nonce. On authentication, availability, unsupported-control, mismatch, or metadata failure, report the exact blocker and leave dispatch pending. Ask for a compatible choice if needed; do not downgrade automatically. If the host cannot expose effective settings, explicitly report that limitation instead of declaring preflight passed.

## Claude Code adapter

Select the generated `.claude/agents/spec-implementer-<effort>.md` type and pass the resolved model through the Agent tool's per-invocation model parameter. The definition sets effort and points to the installed project copy of the shared contract. If the invocation accepts only aliases and the request pins a full ID, use a native mechanism that honors the exact ID or report the unsupported dispatch. Worktrees created by the harness may start from the default branch: explicitly base them on the integration branch.

Use runtime task metadata (including `/tasks` where available) to record the observed model and effort. A family alias permits resolution within that family; an exact ID must match exactly. Stop on a known substitution outside the request and report it. If metadata is unavailable, record verification as unknown instead of claiming a match.

## Codex adapter

Select the generated `.codex/agents/spec-implementer-<digest>.toml` type, which pins both `model` and `model_reasoning_effort`. Where the host exposes direct spawn overrides, pass both resolved values and provide the shared contract pointer in the dispatch prompt instead. Use a fresh or bounded context when the host requires it for overrides; full-history forks can inherit settings without allowing changes. Never select a custom agent whose pinned settings conflict with the direct overrides.

Codex worktrees are supplied explicitly by the coordinator unless the host provides isolation. Check each worker's working directory and branch before edits. Record model and effort from spawn/session metadata when exposed, and distinguish requested settings from observed settings. Unknown observations are recorded as unknown; known mismatches stop dispatch.

Native dispatch operates within the active harness's provider. Running GPT workers from Claude Code or Claude workers from Codex requires a separate configured launcher, which this skill does not supply.

Official native configuration references: [Claude Code subagents](https://code.claude.com/docs/en/sub-agents) and [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
