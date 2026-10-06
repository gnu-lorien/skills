# Forks

Third-party skills this fork carries locally, tracked against their upstreams. They're excluded from the plugin, the top-level README and `ask-matt`, they get no docs pages, and `scripts/link-skills.sh` links them like any other non-retired bucket.

From [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) (Apache-2.0, see [LICENSES/caveman](./LICENSES/caveman/)):

- **[caveman](./caveman/SKILL.md)**: Terse caveman voice: answer first, fluff gone, every technical fact kept. Stays on until "stop caveman" or "normal mode".
- **[ultracave](./ultracave/SKILL.md)**: Caveman at maximum compression: fragments, each fact once. User-invoked.
- **[megacave](./megacave/SKILL.md)**: Caveman in Classical Chinese (文言文 register), technical terms verbatim. User-invoked.
- **[caveman-help](./caveman-help/SKILL.md)**: Quick-reference card for the caveman skills and their commands.
- **[caveman-commit](./caveman-commit/SKILL.md)**: Conventional Commits message compressed to intent only.
- **[caveman-review](./caveman-review/SKILL.md)**: Compressed code review, one line per finding with location, problem and fix.
- **[caveman-compress](./caveman-compress/SKILL.md)**: Compress a memory file such as `CLAUDE.md` into caveman format, keeping a readable backup out of tree.
- **[investigate-first](./investigate-first/SKILL.md)**: Diagnose ambiguous failures with evidence-ranked hypotheses before editing.
- **[lean-build](./lean-build/SKILL.md)**: Build feature work with high overbuilding risk: reuse first, strict scope, explicit stop condition.
- **[migration](./migration/SKILL.md)**: Implement reversible, compatibility-safe schema, data, API or dependency transitions.
- **[safe-refactor](./safe-refactor/SKILL.md)**: Restructure code while preserving behavior, with verification bracketing the edits.
- **[surgical-patch](./surgical-patch/SKILL.md)**: Fix bugs and small behavior changes at the narrowest responsible layer.
- **[verify-and-stop](./verify-and-stop/SKILL.md)**: Prove existing work meets acceptance conditions without expanding scope.

From [Leonxlnx/unlazy](https://github.com/Leonxlnx/unlazy) (MIT, license inside the skill folder):

- **[unlazy](./unlazy/SKILL.md)**: Completion discipline for substantial work: acceptance gates written before execution, a Depth Tree of leaves, runnable checks re-verified before reporting.

## Syncing

[`upstreams.tsv`](./upstreams.tsv) maps each local folder to its upstream repo, ref and path, and records the upstream commit it was last synced to. `scripts/sync-forks.sh [name...]` fetches each upstream and applies the diff since that commit with a 3-way merge, so local edits survive and real clashes show up as conflict markers. It stages the result and advances the manifest but never commits.

To add a skill, append a row with `-` as its synced commit and run the script. A skill can come from a subfolder (`skills/caveman`) or a repo root (`.`). Re-run `scripts/link-skills.sh` afterwards.

Only skill folders come across. Caveman's hooks, statusline, runtime and the Native Core prompt its runtime injects are not imported, so `/caveman status` reports `unknown` and the `lean-build` line about Native Core points at nothing.

## Local divergences

Every intentional difference from upstream is listed here, so a sync conflict can be resolved in its favour. None yet: every folder above is a pristine upstream copy.
