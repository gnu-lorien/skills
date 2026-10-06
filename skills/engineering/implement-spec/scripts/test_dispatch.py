"""Offline checks for dispatch resolution and safe native-agent generation."""

import copy
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
import subprocess
import sys

from dispatch import SKILL, generate, generated_files, load_config, preflight, preflight_plan, resolve


class DispatchTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(SKILL / "references/execution.example.json")

    def test_profiles_and_review_fixes(self):
        self.assertEqual(resolve(self.config, "claude-code")["model"], "sonnet")
        fix = resolve(self.config, "codex", review_fix=True)
        self.assertEqual((fix["model"], fix["effort"]), ("gpt-6.1-sol", "xhigh"))

    def test_explicit_overrides_and_legacy_alias(self):
        choice = resolve(self.config, "claude-code", ["model:opus-5.5", "effort:max"])
        self.assertEqual((choice["model"], choice["effort"]), ("opus", "max"))

    def test_rejects_wrong_provider_effort_and_conflicts(self):
        for labels in (["model:opus"], ["effort:none"], ["effort:high", "effort:low"],
                       ["execution:missing"], ["model:"]):
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                resolve(self.config, "codex", labels)

    def test_pinned_model_stays_pinned(self):
        config = copy.deepcopy(self.config)
        config["models"]["claude-code"]["claude-opus-5-5"] = {"efforts": ["high"]}
        choice = resolve(config, "claude-code", ["model:claude-opus-5-5"])
        self.assertEqual(choice["model"], "claude-opus-5-5")

    def test_native_definitions_parse_and_pin_settings(self):
        files = generated_files(self.config)
        for effort in self.config["models"]["codex"]["gpt-6.1-sol"]["efforts"]:
            name = resolve(self.config, "codex", [f"effort:{effort}"])["agent"]
            data = tomllib.loads(files[f".codex/agents/{name}.toml"])
            self.assertEqual(data["model"], "gpt-6.1-sol")
            self.assertEqual(data["model_reasoning_effort"], effort)
        self.assertIn("effort: xhigh\n", files[".claude/agents/spec-implementer-xhigh.md"])

    def test_generate_is_repeatable_and_preserves_user_edits(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            project = Path(directory)
            paths = generate(self.config, project)
            self.assertEqual(generate(self.config, project), paths)
            target = project / ".claude/agents/spec-implementer-high.md"
            target.write_text("user edit", encoding="utf-8")
            with self.assertRaises(ValueError):
                generate(self.config, project)
            self.assertEqual(target.read_text(), "user edit")

    def test_collision_fails_before_other_writes(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            project = Path(directory)
            target = project / ".claude/agents/spec-implementer-high.md"
            target.parent.mkdir(parents=True)
            target.write_text("user agent", encoding="utf-8")
            with self.assertRaises(ValueError):
                generate(self.config, project)
            self.assertFalse((project / "docs/agents/implement-spec/implementer.md").exists())

    def test_configuration_update_preserves_unrelated_agents(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            project = Path(directory)
            generate(self.config, project)
            custom = project / ".codex/agents/custom.toml"
            custom.write_text('name = "custom"', encoding="utf-8")
            config = copy.deepcopy(self.config)
            config["models"]["codex"]["gpt-6.1-sol"]["efforts"].append("ultra")
            generated = generate(config, project)
            choice = resolve(config, "codex", ["effort:ultra"])
            self.assertIn(f".codex/agents/{choice['agent']}.toml", generated)
            self.assertEqual(custom.read_text(), 'name = "custom"')

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            root = Path(directory)
            project, outside = root / "project", root / "outside"
            project.mkdir()
            outside.mkdir()
            try:
                (project / ".claude").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            with self.assertRaises(ValueError):
                generate(self.config, project)
            self.assertEqual(list(outside.iterdir()), [])

    def test_invalid_config_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            config = copy.deepcopy(self.config)
            config["models"]["codex"]["other"] = {"efforts": ["high"], "aliases": ["gpt-6.1-sol"]}
            path = Path(directory) / "execution.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_profile_guidance_is_optional_and_references_known_profiles(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            path = Path(directory) / "execution.json"
            config = copy.deepcopy(self.config)
            del config["profile_guidance"]
            path.write_text(json.dumps(config), encoding="utf-8")
            self.assertEqual(resolve(load_config(path), "codex")["profile"], "standard")
            for guidance in ({"missing": "Broad changes"}, {"standard": ""}, []):
                config["profile_guidance"] = guidance
                path.write_text(json.dumps(config), encoding="utf-8")
                with self.subTest(guidance=guidance), self.assertRaises(ValueError):
                    load_config(path)

    def probe_evidence(self, harness="codex", mode="native"):
        evidence = preflight_plan(self.config, harness, [{"labels": []}], "run-1", "test-host/1")
        for probe in evidence["probes"]:
            probe.update(status="completed", observed_model=probe["model"],
                         observed_effort=probe["effort"], mode=mode,
                         response="PREFLIGHT_OK", runtime_evidence="test-fixture:session-event")
        return evidence

    def test_preflight_covers_tickets_and_review_fix(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            generate(self.config, directory)
            evidence = self.probe_evidence()
            result = preflight(self.config, "codex", [{"labels": []}], evidence,
                               "run-1", "test-host/1", directory, "native")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["probes"], 2)

    def test_preflight_rejects_missing_unknown_mismatched_and_stale_evidence(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            generate(self.config, directory)
            mutations = [("status", "pending"), ("observed_model", "other-model"),
                         ("observed_effort", None), ("substitution", True),
                         ("runtime_evidence", ""), ("mode", "direct"), ("agent", "wrong"),
                         ("response", "something else")]
            for field, value in mutations:
                evidence = self.probe_evidence()
                evidence["probes"][0][field] = value
                with self.subTest(field=field), self.assertRaises(ValueError):
                    preflight(self.config, "codex", [{"labels": []}], evidence,
                              "run-1", "test-host/1", directory, "native")
            for field in ("session", "client", "config_hash", "artifacts_hash"):
                evidence = self.probe_evidence()
                evidence[field] = "stale"
                with self.subTest(field=field), self.assertRaises(ValueError):
                    preflight(self.config, "codex", [{"labels": []}], evidence,
                              "run-1", "test-host/1", directory, "native")
            evidence = self.probe_evidence()
            evidence["probes"].pop()
            with self.assertRaises(ValueError):
                preflight(self.config, "codex", [{"labels": []}], evidence,
                          "run-1", "test-host/1", directory, "native")

    def test_preflight_rejects_stale_generated_agent(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            generate(self.config, directory)
            evidence = self.probe_evidence()
            agent = evidence["probes"][0]["agent"]
            (Path(directory) / f".codex/agents/{agent}.toml").write_text("old agent", encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight(self.config, "codex", [{"labels": []}], evidence,
                          "run-1", "test-host/1", directory, "native")

    def test_claude_alias_requires_matching_concrete_family(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            generate(self.config, directory)
            evidence = self.probe_evidence("claude-code")
            for probe in evidence["probes"]:
                probe["observed_model"] = f"claude-{probe['model']}-test-version"
            self.assertEqual(preflight(self.config, "claude-code", [{"labels": []}], evidence,
                                       "run-1", "test-host/1", directory, "native")["status"], "passed")

    def test_direct_preflight_needs_contract_but_not_native_definitions(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            contract = Path(directory) / "docs/agents/implement-spec/implementer.md"
            contract.parent.mkdir(parents=True)
            contract.write_text(generated_files(self.config)["docs/agents/implement-spec/implementer.md"], encoding="utf-8")
            evidence = self.probe_evidence(mode="direct")
            self.assertEqual(preflight(self.config, "codex", [{"labels": []}], evidence,
                                       "run-1", "test-host/1", directory, "direct")["status"], "passed")

    def test_cli_rejects_pending_plan_and_accepts_completed_fixture(self):
        with tempfile.TemporaryDirectory(prefix="skill-dispatch-") as directory:
            root = Path(directory)
            generate(self.config, root)
            tickets = root / "tickets.json"
            tickets.write_text('[{"labels": []}]', encoding="utf-8")
            args = [sys.executable, str(SKILL / "scripts/dispatch.py"), "preflight-plan",
                    "--config", str(SKILL / "references/execution.example.json"),
                    "--harness", "codex", "--tickets", str(tickets),
                    "--session", "run-1", "--client", "test-host/1"]
            plan = subprocess.run(args, capture_output=True, text=True, check=True)
            evidence = root / "evidence.json"
            evidence.write_text(plan.stdout, encoding="utf-8")
            args[2] = "preflight"
            args.extend(["--evidence", str(evidence), "--project", str(root), "--mode", "native"])
            pending = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(pending.returncode, 2)
            self.assertIn("unverified dispatch probe", pending.stderr)
            evidence.write_text(json.dumps(self.probe_evidence()), encoding="utf-8")
            completed = subprocess.run(args, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(completed.stdout)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
