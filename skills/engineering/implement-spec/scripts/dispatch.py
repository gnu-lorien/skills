"""Resolve execution profiles and generate project-scoped native implementers."""

import argparse
import hashlib
import json
from pathlib import Path
import re


HARNESSES = ("claude-code", "codex")
EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
SKILL = Path(__file__).resolve().parents[1]


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ValueError("execution config must have version 1")
    if not isinstance(config.get("models"), dict) or not config["models"]:
        raise ValueError("models must be a nonempty harness mapping")
    if not isinstance(config.get("profiles"), dict) or not config["profiles"]:
        raise ValueError("profiles must be a nonempty mapping")
    for harness, models in config["models"].items():
        if harness not in HARNESSES or not isinstance(models, dict) or not models:
            raise ValueError(f"unsupported or empty harness: {harness}")
        names = set()
        for model, options in models.items():
            if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/\[\]-]*", model):
                raise ValueError("invalid model ID or family alias")
            if not isinstance(options, dict):
                raise ValueError(f"invalid model options: {model}")
            efforts = options["efforts"]
            if not isinstance(efforts, list) or not efforts or any(not isinstance(e, str) or e not in EFFORTS for e in efforts):
                raise ValueError(f"invalid efforts for {model}")
            if harness == "claude-code" and any(e in {"none", "minimal", "ultra"} for e in efforts):
                raise ValueError("Claude Code does not expose that effort")
            aliases = options.get("aliases", [])
            if not isinstance(aliases, list):
                raise ValueError(f"aliases must be a list: {model}")
            for name in [model, *aliases]:
                if not isinstance(name, str) or not name or name in names:
                    raise ValueError(f"duplicate or invalid model alias: {name}")
                names.add(name)
    for name, profile in config["profiles"].items():
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or not isinstance(profile, dict) or not profile:
            raise ValueError(f"invalid or empty profile: {name}")
        for harness, choice in profile.items():
            if not isinstance(choice, dict) or not isinstance(choice.get("model"), str) or not isinstance(choice.get("effort"), str):
                raise ValueError(f"invalid profile choice: {name}/{harness}")
            model = choice["model"]
            options = config["models"].get(harness, {}).get(model)
            if options is None or choice["effort"] not in options["efforts"]:
                raise ValueError(f"unsupported profile choice: {name}/{harness}")
    for key in ("default_profile", "review_fix_profile"):
        if config[key] not in config["profiles"]:
            raise ValueError(f"unknown {key}: {config[key]}")
    guidance = config.get("profile_guidance", {})
    if not isinstance(guidance, dict):
        raise ValueError("profile_guidance must be a profile-to-purpose mapping")
    for name, purpose in guidance.items():
        if name not in config["profiles"] or not isinstance(purpose, str) or not purpose.strip():
            raise ValueError(f"invalid guidance for profile: {name}")
    return config


def agent_name(harness, model, effort):
    if harness == "claude-code":
        return f"spec-implementer-{effort}"
    digest = hashlib.sha256(f"{model}\0{effort}".encode()).hexdigest()[:12]
    return f"spec-implementer-{digest}"


def resolve(config, harness, labels=(), review_fix=False):
    fields = {}
    for label in labels:
        key, sep, value = label.partition(":")
        if key not in {"execution", "model", "effort"}:
            continue
        if not sep or not value or (key in fields and fields[key] != value):
            raise ValueError(f"missing or conflicting {key} labels")
        fields[key] = value
    if review_fix and fields:
        raise ValueError("review-fix selection cannot include ticket overrides")
    profile = fields.get("execution", config["review_fix_profile" if review_fix else "default_profile"])
    profiles = config["profiles"]
    if profile not in profiles or harness not in profiles[profile]:
        raise ValueError(f"profile unavailable for {harness}: {profile}")
    choice = dict(profiles[profile][harness])
    models = config["models"].get(harness, {})
    requested_model = fields.get("model", choice["model"])
    candidates = [m for m, opts in models.items()
                  if requested_model == m or requested_model in opts.get("aliases", [])]
    if len(candidates) != 1:
        raise ValueError(f"model unavailable for {harness}: {requested_model}")
    choice["model"] = candidates[0]
    choice["effort"] = fields.get("effort", choice["effort"])
    if choice["effort"] not in models[choice["model"]]["efforts"]:
        raise ValueError(f"unsupported effort for {choice['model']}: {choice['effort']}")
    return {"harness": harness, "profile": profile, **choice,
            "agent": agent_name(harness, choice["model"], choice["effort"])}


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def preflight_plan(config, harness, tickets, session, client):
    if not session or not client or not isinstance(tickets, list):
        raise ValueError("preflight needs tickets, current session ID, and client/version")
    for ticket in tickets:
        if (not isinstance(ticket, dict) or not isinstance(ticket.get("labels"), list)
                or any(not isinstance(label, str) for label in ticket["labels"])):
            raise ValueError("each ticket needs a labels array of strings")
    choices = [resolve(config, harness, ticket["labels"]) for ticket in tickets]
    choices.append(resolve(config, harness, review_fix=True))
    unique = {(c["model"], c["effort"]): c for c in choices}
    return {"version": 1, "harness": harness, "session": session, "client": client,
            "config_hash": sha(json.dumps(config, sort_keys=True)),
            "artifacts_hash": sha(json.dumps(generated_files(config), sort_keys=True)),
            "probes": [{"model": c["model"], "effort": c["effort"], "agent": c["agent"],
                        "status": "pending", "observed_model": None, "observed_effort": None,
                        "response": None, "runtime_evidence": "", "substitution": False}
                       for c in unique.values()]}


def model_matches(requested, observed):
    if not isinstance(observed, str):
        return False
    if requested in {"sonnet", "opus", "haiku", "fable"}:
        return observed.startswith(f"claude-{requested}-")
    return requested == observed


def preflight(config, harness, tickets, evidence, session, client, project, mode):
    if not isinstance(evidence, dict) or mode not in {"native", "direct"}:
        raise ValueError("invalid preflight evidence or mode")
    expected = preflight_plan(config, harness, tickets, session, client)
    for key in ("version", "harness", "session", "client", "config_hash", "artifacts_hash"):
        if evidence.get(key) != expected[key]:
            raise ValueError(f"missing or stale preflight evidence: {key}")
    project = Path(project).resolve()
    files = generated_files(config)
    required = {"docs/agents/implement-spec/implementer.md"}
    if mode == "native":
        for probe in expected["probes"]:
            folder, suffix = ((".claude", "md") if harness == "claude-code" else (".codex", "toml"))
            required.add(f"{folder}/agents/{probe['agent']}.{suffix}")
    for relative in required:
        target = project / relative
        if not target.resolve().is_relative_to(project) or target.read_text(encoding="utf-8") != files[relative]:
            raise ValueError(f"missing or stale generated definition: {relative}")
    probes = evidence.get("probes", [])
    if not isinstance(probes, list) or any(not isinstance(p, dict) for p in probes):
        raise ValueError("probe evidence must be a list")
    for requested in expected["probes"]:
        matches = [p for p in probes if p.get("model") == requested["model"]
                   and p.get("effort") == requested["effort"]]
        if len(matches) != 1:
            raise ValueError(f"missing or duplicate probe: {requested['model']}/{requested['effort']}")
        probe = matches[0]
        if (probe.get("status") != "completed" or probe.get("response") != "PREFLIGHT_OK"
                or probe.get("substitution") is not False
                or not model_matches(requested["model"], probe.get("observed_model"))
                or probe.get("observed_effort") != requested["effort"]
                or probe.get("mode") != mode
                or not isinstance(probe.get("runtime_evidence"), str)
                or not probe["runtime_evidence"].strip()
                or (mode == "native" and probe.get("agent") != requested["agent"])):
            raise ValueError(f"unverified dispatch probe: {requested['model']}/{requested['effort']}")
    return {"status": "passed", "probes": len(expected["probes"]), "session": session,
            "harness": harness, "mode": mode}


def generated_files(config):
    contract_path = "docs/agents/implement-spec/implementer.md"
    files = {contract_path: (SKILL / "references/implementer.md").read_text(encoding="utf-8")}
    instructions = f"For a dispatch explicitly marked as a preflight probe, reply PREFLIGHT_OK without tools or file access and finish. Otherwise read {contract_path} in the project checkout before starting and follow its implementer contract. The coordinator supplies the ticket, spec, worktree and integration branch."
    for harness, models in config["models"].items():
        for model, options in models.items():
            for effort in options["efforts"]:
                name = agent_name(harness, model, effort)
                description = "Implements spec tickets and review or integration-gate fixes."
                if harness == "claude-code":
                    files[f".claude/agents/{name}.md"] = (
                        f"---\nname: {name}\ndescription: {description}\n"
                        f"model: inherit\neffort: {effort}\n---\n\n{instructions}\n")
                else:
                    values = {"name": name, "description": description, "model": model,
                              "model_reasoning_effort": effort, "developer_instructions": instructions}
                    files[f".codex/agents/{name}.toml"] = "".join(
                        f"{key} = {json.dumps(value, ensure_ascii=False)}\n" for key, value in values.items())
    return files


def generate(config, project):
    project = Path(project).resolve()
    manifest = project / "docs/agents/implement-spec/generated.json"
    owned = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    files = generated_files(config)
    # Check every destination before writing any file. Preserve user-owned changes.
    for relative, content in files.items():
        target = project / relative
        if not target.resolve().is_relative_to(project):
            raise ValueError(f"destination escapes project: {relative}")
        if target.exists():
            existing = target.read_text(encoding="utf-8")
            if relative not in owned or sha(existing) != owned[relative]:
                raise ValueError(f"refusing to overwrite unowned or edited file: {relative}")
    if not manifest.resolve().is_relative_to(project):
        raise ValueError("manifest escapes project")
    for relative, content in files.items():
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
        if target.read_text(encoding="utf-8") != content:
            raise ValueError(f"generated file verification failed: {relative}")
        owned[relative] = sha(content)
    manifest.write_text(json.dumps(owned, indent=2) + "\n", encoding="utf-8")
    if json.loads(manifest.read_text(encoding="utf-8")) != owned:
        raise ValueError("generated manifest verification failed")
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    resolver = commands.add_parser("resolve")
    resolver.add_argument("--config", required=True)
    resolver.add_argument("--harness", choices=HARNESSES, required=True)
    resolver.add_argument("--label", action="append", default=[])
    resolver.add_argument("--review-fix", action="store_true")
    generator = commands.add_parser("generate")
    generator.add_argument("--config", required=True)
    generator.add_argument("--project", required=True)
    for command in ("preflight-plan", "preflight"):
        check = commands.add_parser(command)
        check.add_argument("--config", required=True)
        check.add_argument("--harness", choices=HARNESSES, required=True)
        check.add_argument("--tickets", required=True, help="JSON array of tickets with labels arrays")
        check.add_argument("--session", required=True, help="current session ID or newly generated run nonce")
        check.add_argument("--client", required=True, help="active host name and version")
        if command == "preflight":
            check.add_argument("--evidence", required=True)
            check.add_argument("--project", required=True)
            check.add_argument("--mode", choices=("native", "direct"), required=True)
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.command == "resolve":
            result = resolve(config, args.harness, args.label, args.review_fix)
        elif args.command == "generate":
            result = generate(config, args.project)
        else:
            tickets = json.loads(Path(args.tickets).read_text(encoding="utf-8"))
            if args.command == "preflight-plan":
                result = preflight_plan(config, args.harness, tickets, args.session, args.client)
            else:
                evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
                result = preflight(config, args.harness, tickets, evidence, args.session,
                                   args.client, args.project, args.mode)
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"dispatch error: {error}\n")


if __name__ == "__main__":
    main()
