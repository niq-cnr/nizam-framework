#!/usr/bin/env python3
"""Permanent regression tests for the convergent review standard and CLI."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "tools/convergent_review.py"
PROMPT_EVAL = ROOT / "tools/evaluate_convergent_review_prompt.py"
PROMPT_TEMPLATE = ROOT / "templates/convergent-review-prompt.md"
FAKE_RUNNER = ROOT / "tools/fixtures/convergent_review/fake_prompt_runner.py"
LINUX_SANDBOX = ROOT / "tools/linux_trial_sandbox.sh"
FIXTURES = ROOT / "tools/fixtures/convergent_review"
SCHEMAS = (
    "review_packet.schema.json",
    "review_trial.schema.json",
    "review_ledger.schema.json",
    "review_suppression.schema.json",
    "review_replay.schema.json",
)
SPEC = importlib.util.spec_from_file_location("convergent_review", CLI)
cr = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cr)


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump(path: Path, value) -> None:
    path.write_bytes(cr.canonical_json_bytes(value))


def command_for(case: Path, output: Path) -> list[str]:
    command = [
        "python3", str(CLI), "converge", "--packet", str(case / "packet.json"),
        "--trial", str(case / "trial-1.json"), "--trial", str(case / "trial-2.json"),
        "--trial", str(case / "trial-3.json"), "--output-dir", str(output),
    ]
    if (case / "prior-ledger.json").exists():
        command.extend(["--prior-ledger", str(case / "prior-ledger.json")])
    if (case / "suppression.json").exists():
        command.extend(["--suppression", str(case / "suppression.json")])
    return command


def run_case(case: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command_for(case, output), cwd=ROOT, text=True, capture_output=True, check=False)


class FixtureCorpusTests(unittest.TestCase):
    maxDiff = None

    def test_manifest_is_frozen_twelve_case_corpus(self) -> None:
        manifest = load(FIXTURES / "manifest.json")
        self.assertEqual(manifest["schema_version"], "1.0.0")
        self.assertEqual(len(manifest["cases"]), 12)
        self.assertEqual(
            [item["id"] for item in manifest["cases"]],
            sorted(path.name for path in FIXTURES.iterdir() if path.is_dir() and path.name[:1].isdigit()),
        )
        for item in manifest["cases"]:
            case = FIXTURES / item["id"]
            for required in ("packet.json", "trial-1.json", "trial-2.json", "trial-3.json", "expected.json"):
                self.assertTrue((case / required).is_file(), f"missing {item['id']}/{required}")

    def test_all_fixture_cases_and_replay_retention(self) -> None:
        manifest = load(FIXTURES / "manifest.json")
        with tempfile.TemporaryDirectory() as temporary:
            temp = Path(temporary)
            for item in manifest["cases"]:
                with self.subTest(case=item["id"]):
                    case = FIXTURES / item["id"]
                    expected = load(case / "expected.json")
                    output = temp / item["id"]
                    result = run_case(case, output)
                    if expected["outcome"] == "error":
                        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertIn(expected["error_contains"], result.stderr)
                        continue
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    ledger = load(output / "ledger.json")
                    self.assertEqual(ledger["verdict"], expected["verdict"])
                    self.assertEqual(len(ledger["findings"]), expected["findings"])
                    if expected["lifecycle"] is not None:
                        self.assertEqual(ledger["findings"][0]["lifecycle"], expected["lifecycle"])
                    if "fingerprint" in expected:
                        self.assertEqual(ledger["findings"][0]["fingerprint"], expected["fingerprint"])
                    replay = load(output / "replay.json")
                    trials = [artifact for artifact in replay["artifacts"] if artifact["role"] == "trial"]
                    self.assertEqual([artifact["trial_number"] for artifact in trials], [1, 2, 3])
                    for artifact in replay["artifacts"]:
                        retained = output / artifact["path"]
                        self.assertTrue(retained.is_file())
                        raw = retained.read_bytes()
                        self.assertEqual(len(raw), artifact["bytes"])
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), artifact["digest"])
                    verified = subprocess.run(
                        ["python3", str(CLI), "verify-replay", "--replay", str(output / "replay.json")],
                        cwd=ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_canonical_byte_stability_and_markdown_count_alignment(self) -> None:
        case = FIXTURES / "02-consensus-blocker"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first"
            second = Path(temporary) / "second"
            self.assertEqual(run_case(case, first).returncode, 0)
            self.assertEqual(run_case(case, second).returncode, 0)
            for relative in ("ledger.json", "review.md", "replay.json"):
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes(), relative)
            ledger_raw = (first / "ledger.json").read_bytes()
            ledger = json.loads(ledger_raw)
            self.assertEqual(ledger_raw, cr.canonical_json_bytes(ledger))
            markdown = (first / "review.md").read_text(encoding="utf-8")
            for key, value in ledger["counts"].items():
                self.assertIn(f"| `{key}` | {value} |", markdown)
            extracted = subprocess.run(
                ["python3", str(CLI), "extract-ledger", "--markdown", str(first / "review.md")],
                cwd=ROOT, capture_output=True, check=False,
            )
            self.assertEqual(extracted.returncode, 0, extracted.stderr.decode())
            self.assertEqual(extracted.stdout, ledger_raw)
            rendered = subprocess.run(
                ["python3", str(CLI), "render", "--ledger", str(first / "ledger.json")],
                cwd=ROOT, capture_output=True, check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr.decode())
            self.assertEqual(rendered.stdout, (first / "review.md").read_bytes())

    def test_tamper_detection_fixture(self) -> None:
        case = FIXTURES / "12-tamper-detection"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "output"
            self.assertEqual(run_case(case, output).returncode, 0)
            trial = output / load(case / "expected.json")["tamper"]
            trial.write_bytes(trial.read_bytes() + b" ")
            verified = subprocess.run(
                ["python3", str(CLI), "verify-replay", "--replay", str(output / "replay.json")],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertNotEqual(verified.returncode, 0)
            self.assertIn("digest/size mismatch", verified.stderr)


class SemanticMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp = Path(self.temporary.name)
        self.case = self.temp / "case"
        shutil.copytree(FIXTURES / "02-consensus-blocker", self.case)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _rewrite_packet_and_bind_trials(self, mutate) -> None:
        packet = load(self.case / "packet.json")
        mutate(packet)
        dump(self.case / "packet.json", packet)
        digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        for number in (1, 2, 3):
            path = self.case / f"trial-{number}.json"
            trial = load(path)
            trial["packet_digest"] = digest
            trial["head_sha"] = packet["head_sha"]
            dump(path, trial)

    def test_trial_rejects_model_owned_fields(self) -> None:
        trial = load(self.case / "trial-1.json")
        trial["verdict"] = "approve"
        dump(self.case / "trial-1.json", trial)
        result = run_case(self.case, self.temp / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown field", result.stderr)

    def test_stale_trial_head_rejected(self) -> None:
        trial = load(self.case / "trial-1.json")
        trial["head_sha"] = "f" * 40
        dump(self.case / "trial-1.json", trial)
        result = run_case(self.case, self.temp / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("current head", result.stderr)

    def test_exactly_three_unique_trials_required(self) -> None:
        command = command_for(self.case, self.temp / "out")
        command[command.index(str(self.case / "trial-3.json"))] = str(self.case / "trial-2.json")
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate trial_number", result.stderr)

    def test_duplicate_semantic_observation_in_one_trial_is_rejected(self) -> None:
        trial = load(self.case / "trial-1.json")
        trial["observations"].append(copy.deepcopy(trial["observations"][0]))
        dump(self.case / "trial-1.json", trial)
        result = run_case(self.case, self.temp / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate semantic finding", result.stderr)

    def test_severity_disagreement_uses_most_severe_distinct_trial(self) -> None:
        for number, severity in ((1, "minor"), (2, "important")):
            trial = load(self.case / f"trial-{number}.json")
            trial["observations"][0]["finding"]["severity"] = severity
            dump(self.case / f"trial-{number}.json", trial)
        output = self.temp / "out"
        self.assertEqual(run_case(self.case, output).returncode, 0)
        ledger = load(output / "ledger.json")
        self.assertEqual(ledger["findings"][0]["severity"], "important")
        self.assertEqual(ledger["verdict"], "request_changes")

    def test_reopened_finding_adopts_more_severe_current_consensus(self) -> None:
        source = FIXTURES / "08-reopened-finding"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        prior = load(self.case / "prior-ledger.json")
        prior["findings"][0]["severity"] = "minor"
        dump(self.case / "prior-ledger.json", prior)
        for number in (1, 2):
            trial = load(self.case / f"trial-{number}.json")
            trial["observations"][0]["finding"]["severity"] = "blocker"
            dump(self.case / f"trial-{number}.json", trial)
        output = self.temp / "out"
        self.assertEqual(run_case(self.case, output).returncode, 0)
        ledger = load(output / "ledger.json")
        self.assertEqual(ledger["findings"][0]["lifecycle"], "reopened")
        self.assertEqual(ledger["findings"][0]["severity"], "blocker")
        self.assertEqual(ledger["verdict"], "request_changes")

    def test_semantic_mutation_changes_fingerprint_but_line_shift_does_not(self) -> None:
        trial = load(self.case / "trial-1.json")
        finding = trial["observations"][0]["finding"]
        original = cr.semantic_fingerprint("example/reviewed-repo", finding)
        shifted = copy.deepcopy(finding)
        self.assertEqual(original, cr.semantic_fingerprint("example/reviewed-repo", shifted))
        changed = copy.deepcopy(finding)
        changed["symbol"] = "different_symbol"
        self.assertNotEqual(original, cr.semantic_fingerprint("example/reviewed-repo", changed))

    def test_prior_head_must_equal_packet_base(self) -> None:
        source = FIXTURES / "05-prior-persisting"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        prior = load(self.case / "prior-ledger.json")
        prior["head_sha"] = "e" * 40
        for finding in prior["findings"]:
            finding["first_seen_head"] = prior["head_sha"]
            finding["last_seen_head"] = prior["head_sha"]
        dump(self.case / "prior-ledger.json", prior)
        result = run_case(self.case, self.temp / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must equal packet.base_sha", result.stderr)

    def test_unauthorized_or_unknown_suppression_rejected(self) -> None:
        source = FIXTURES / "11-authorized-suppression-retained"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        suppression = load(self.case / "suppression.json")
        suppression["fingerprint"] = "f" * 64
        dump(self.case / "suppression.json", suppression)
        result = run_case(self.case, self.temp / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not reference", result.stderr)

    def test_ledger_count_mutation_is_rejected(self) -> None:
        output = self.temp / "out"
        self.assertEqual(run_case(self.case, output).returncode, 0)
        ledger = load(output / "ledger.json")
        ledger["counts"]["new"] = 0
        dump(output / "bad-ledger.json", ledger)
        rendered = subprocess.run(
            ["python3", str(CLI), "render", "--ledger", str(output / "bad-ledger.json")],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(rendered.returncode, 0)
        self.assertIn("do not match", rendered.stderr)

    def test_consensus_invalid_lifecycle_cannot_render_an_approval(self) -> None:
        output = self.temp / "out"
        self.assertEqual(run_case(self.case, output).returncode, 0)
        ledger = load(output / "ledger.json")
        finding = ledger["findings"][0]
        finding["lifecycle"] = "resolved"
        finding["resolved_head"] = ledger["head_sha"]
        finding["resolution_evidence"] = copy.deepcopy(finding["evidence"])
        finding["evidence"] = []
        finding["consensus"] = {"active_trials": [], "resolved_trials": [1, 2]}
        ledger["counts"] = cr.calculate_counts(ledger["findings"])
        ledger["verdict"] = "approve"
        dump(output / "bad-lifecycle.json", ledger)
        rendered = subprocess.run(
            ["python3", str(CLI), "render", "--ledger", str(output / "bad-lifecycle.json")],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(rendered.returncode, 0)
        self.assertIn("initial ledger permits only new or suppressed findings", rendered.stderr)

    def test_existing_or_symlink_output_is_rejected_without_partial_verdict(self) -> None:
        output = self.temp / "existing"
        output.mkdir()
        (output / "inputs").write_text("collision", encoding="utf-8")
        result = run_case(self.case, output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "ledger.json").exists())
        target = self.temp / "target"
        target.mkdir()
        symlink = self.temp / "linked"
        symlink.symlink_to(target, target_is_directory=True)
        linked_result = run_case(self.case, symlink)
        self.assertNotEqual(linked_result.returncode, 0)
        self.assertFalse((target / "ledger.json").exists())

    def test_replay_rejects_multiple_prior_ledgers(self) -> None:
        output = self.temp / "out"
        self.assertEqual(run_case(FIXTURES / "05-prior-persisting", output).returncode, 0)
        replay = load(output / "replay.json")
        prior = next(item for item in replay["artifacts"] if item["role"] == "prior_ledger")
        duplicate = copy.deepcopy(prior)
        duplicate["path"] = "inputs/prior-ledger-copy.json"
        replay["artifacts"].append(duplicate)
        with self.assertRaisesRegex(cr.ReviewError, "one packet and trials"):
            cr.validate_replay(replay)

    def test_prompt_evaluator_runs_three_isolated_validated_trials(self) -> None:
        output = self.temp / "prompt-eval"
        result = subprocess.run(
            [
                "python3", str(PROMPT_EVAL),
                "--packet", str(FIXTURES / "01-no-findings/packet.json"),
                "--prompt-template", str(PROMPT_TEMPLATE),
                "--runner", str(FAKE_RUNNER),
                "--output-dir", str(output),
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = load(output / "prompt-evaluation.json")
        self.assertEqual([item["trial_number"] for item in receipt["trials"]], [1, 2, 3])
        self.assertEqual(load(output / "review/ledger.json")["verdict"], "approve")
        for number in (1, 2, 3):
            self.assertTrue((output / f"evaluation/trial-{number}/prompt.md").is_file())

    def test_closed_schemas_reject_additive_mutations(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:  # pragma: no cover - repository validator already requires it
            self.skipTest(str(exc))
        samples = {
            "review_packet.schema.json": load(FIXTURES / "01-no-findings/packet.json"),
            "review_trial.schema.json": load(FIXTURES / "01-no-findings/trial-1.json"),
        }
        output = self.temp / "out"
        self.assertEqual(run_case(FIXTURES / "01-no-findings", output).returncode, 0)
        samples["review_ledger.schema.json"] = load(output / "ledger.json")
        samples["review_replay.schema.json"] = load(output / "replay.json")
        samples["review_suppression.schema.json"] = load(FIXTURES / "11-authorized-suppression-retained/suppression.json")
        for schema_name, sample in samples.items():
            with self.subTest(schema=schema_name):
                schema = load(ROOT / "schema" / schema_name)
                jsonschema.Draft202012Validator.check_schema(schema)
                jsonschema.validate(sample, schema)
                mutated = copy.deepcopy(sample)
                mutated["model_verdict"] = "approve"
                with self.assertRaises(jsonschema.ValidationError):
                    jsonschema.validate(mutated, schema)

    def test_later_review_can_add_genuinely_new_finding(self) -> None:
        source = FIXTURES / "05-prior-persisting"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        packet = load(self.case / "packet.json")
        source_entry = packet["review_files"][0]
        source_entry["content"] = "new regression\n"
        source_entry["content_digest"] = hashlib.sha256(b"new regression\n").hexdigest()
        packet["delta"][0]["new_digest"] = source_entry["content_digest"]
        dump(self.case / "packet.json", packet)
        packet_digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        finding = {
            "severity": "important", "category": "correctness", "path": "src/auth.py",
            "symbol": "new_handler", "rule": "new_regression", "title": "New regression",
            "description": "A distinct current-head regression appears after the prior reviewed head.",
        }
        evidence = {
            "path": "src/auth.py", "start_line": 1, "end_line": 1, "excerpt": "new regression",
            "content_digest": source_entry["content_digest"],
        }
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["packet_digest"] = packet_digest
            trial["observations"] = [] if number == 3 else [{"action": "active", "finding": finding, "evidence": [evidence]}]
            dump(trial_path, trial)
        output = self.temp / "later-new"
        result = run_case(self.case, output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        led = load(output / "ledger.json")
        self.assertEqual(sorted(item["lifecycle"] for item in led["findings"]), ["new", "persisting"])
        self.assertIsNotNone(led["prior_ledger_digest"])

    def test_symbol_case_is_semantically_distinct(self) -> None:
        finding = load(self.case / "trial-1.json")["observations"][0]["finding"]
        upper = copy.deepcopy(finding)
        lower = copy.deepcopy(finding)
        upper["symbol"] = "Foo"
        lower["symbol"] = "foo"
        self.assertNotEqual(
            cr.semantic_fingerprint("host/org/team/repo", upper),
            cr.semantic_fingerprint("host/org/team/repo", lower),
        )

    def test_repository_and_path_grammars_accept_legal_names_and_reject_unsafe_paths(self) -> None:
        for value in ("host/org/team/repo", "registry/@scope/package", "組織/チーム/リポジトリ"):
            with self.subTest(repository=value):
                self.assertEqual(cr.validate_repository(value, "repository"), value)
        for value in ("src/space name.py", "src/日本語/構成.py", "packages/@scope/file.ts"):
            with self.subTest(path=value):
                self.assertEqual(cr.validate_path(value, "path"), value)
        for value in (
            "/etc/passwd", "../escape", "src/../escape", "src//file", "C:/absolute",
            "src\\windows.py", "src/evil\x00name", "src/c1\x85name",
        ):
            with self.subTest(unsafe=value):
                with self.assertRaises(cr.ReviewError):
                    cr.validate_path(value, "path")
        for value in ("host\\org/repo", "host/org/repo\\evil", "host/org/\x85repo"):
            with self.subTest(unsafe_repository=value):
                with self.assertRaises(cr.ReviewError):
                    cr.validate_repository(value, "repository")

    def test_packet_schema_plus_relational_validator_contract(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:
            self.skipTest(str(exc))
        schema = load(ROOT / "schema/review_packet.schema.json")
        packet = load(self.case / "packet.json")
        duplicate_path = copy.deepcopy(packet)
        duplicate_path["delta"].append(copy.deepcopy(duplicate_path["delta"][0]))
        equal_digest = copy.deepcopy(packet)
        equal_digest["delta"][0]["old_digest"] = equal_digest["delta"][0]["new_digest"]
        equal_digest["delta"][0]["old_content"] = packet["review_files"][0]["content"]
        duplicate_source = copy.deepcopy(packet)
        duplicate_source["review_files"].append(copy.deepcopy(duplicate_source["review_files"][0]))
        # These are intentionally legal at the structural JSON-Schema stage:
        # Draft 2020-12 cannot project uniqueness by path or compare siblings.
        for value in (duplicate_path, duplicate_source, equal_digest):
            with self.subTest(mutation=value):
                jsonschema.validate(value, schema)
                cr.validate_packet_schema_stage(value)
                with self.assertRaises(cr.ReviewError):
                    cr.validate_packet_relations(value)
                with self.assertRaises(cr.ReviewError):
                    cr.validate_packet(value)
        missing_old_bytes = copy.deepcopy(packet)
        missing_old_bytes["delta"][0]["old_content"] = None
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(missing_old_bytes, schema)
        with self.assertRaises(cr.ReviewError):
            cr.validate_packet_schema_stage(missing_old_bytes)

    def test_replay_schema_and_runtime_reject_duplicate_trial_numbers(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:
            self.skipTest(str(exc))
        output = self.temp / "replay-parity"
        self.assertEqual(run_case(FIXTURES / "01-no-findings", output).returncode, 0)
        replay = load(output / "replay.json")
        trials = [item for item in replay["artifacts"] if item["role"] == "trial"]
        for item in trials:
            item["trial_number"] = 1
        schema = load(ROOT / "schema/review_replay.schema.json")
        with self.assertRaises(cr.ReviewError):
            cr.validate_replay(replay)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(replay, schema)

    def test_ledger_schema_and_runtime_reject_duplicate_trial_digests(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:
            self.skipTest(str(exc))
        output = self.temp / "ledger-parity"
        self.assertEqual(run_case(FIXTURES / "01-no-findings", output).returncode, 0)
        ledger = load(output / "ledger.json")
        ledger["trial_digests"] = [ledger["trial_digests"][0]] * 3
        schema = load(ROOT / "schema/review_ledger.schema.json")
        with self.assertRaises(cr.ReviewError):
            cr.validate_ledger(ledger)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(ledger, schema)

    def test_trial_evidence_must_match_packet_digest_excerpt_and_range(self) -> None:
        packet = load(self.case / "packet.json")
        packet_digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        base = load(self.case / "trial-1.json")
        mutations = []
        bad_digest = copy.deepcopy(base)
        bad_digest["observations"][0]["evidence"][0]["content_digest"] = "f" * 64
        mutations.append((bad_digest, "authenticated current-head bytes"))
        bad_excerpt = copy.deepcopy(base)
        bad_excerpt["observations"][0]["evidence"][0]["excerpt"] = "fabricated"
        mutations.append((bad_excerpt, "authenticated line range"))
        bad_range = copy.deepcopy(base)
        bad_range["observations"][0]["evidence"][0]["end_line"] = 99999
        mutations.append((bad_range, "line range exceeds"))
        all_zero = copy.deepcopy(base)
        all_zero["observations"][0]["evidence"][0]["content_digest"] = "0" * 64
        mutations.append((all_zero, "all-zero digest"))
        unrelated = copy.deepcopy(base)
        unrelated["observations"][0]["evidence"][0]["path"] = "src/unrelated.py"
        mutations.append((unrelated, "authenticated current-head review universe"))
        for trial, message in mutations:
            with self.subTest(message=message):
                with self.assertRaisesRegex(cr.ReviewError, message):
                    cr.validate_trial(trial, packet, packet_digest, "trial")

    def test_noncanonical_inputs_are_rejected(self) -> None:
        packet = load(self.case / "packet.json")
        (self.case / "packet.json").write_text(json.dumps(packet, indent=2), encoding="utf-8")
        result = run_case(self.case, self.temp / "noncanonical")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical UTF-8 JSON", result.stderr)

    def test_prompt_evaluator_uses_per_trial_packet_copies(self) -> None:
        output = self.temp / "isolated"
        result = subprocess.run(
            ["python3", str(PROMPT_EVAL), "--packet", str(FIXTURES / "01-no-findings/packet.json"),
             "--prompt-template", str(PROMPT_TEMPLATE), "--runner", str(FAKE_RUNNER),
             "--output-dir", str(output)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = load(output / "prompt-evaluation.json")
        self.assertEqual(len({item["isolated_packet_digest"] for item in receipt["trials"]}), 1)
        for number in (1, 2, 3):
            trial_root = output / f"evaluation/trial-{number}"
            self.assertTrue((trial_root / "packet.json").is_file())
            prompt = (trial_root / "prompt.md").read_text(encoding="utf-8")
            self.assertIn(f"evaluation/trial-{number}/packet.json", prompt)
            for other in ({1, 2, 3} - {number}):
                self.assertNotIn(f"evaluation/trial-{other}", prompt)

    def test_full_audit_packet_contains_authenticated_unchanged_universe(self) -> None:
        packet = load(FIXTURES / "09-explicit-full-audit-discovery/packet.json")
        self.assertEqual(packet["mode"], "full_audit")
        delta_paths = {entry["path"] for entry in packet["delta"]}
        review_paths = {entry["path"] for entry in packet["review_files"]}
        self.assertIn("src/legacy.py", review_paths - delta_paths)
        for number in (1, 2):
            trial = load(FIXTURES / f"09-explicit-full-audit-discovery/trial-{number}.json")
            evidence = trial["observations"][0]["evidence"][0]
            source = next(item for item in packet["review_files"] if item["path"] == evidence["path"])
            self.assertEqual(evidence["content_digest"], source["content_digest"])

    def test_true_full_revert_is_representable_with_absence_tombstone(self) -> None:
        source = FIXTURES / "06-prior-resolution-two-of-three"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        packet = load(self.case / "packet.json")
        packet["delta"][0]["new_digest"] = None
        packet["delta"][0]["new_mode"] = None
        packet["review_files"][0]["content"] = None
        packet["review_files"][0]["content_digest"] = hashlib.sha256(b"").hexdigest()
        dump(self.case / "packet.json", packet)
        packet_digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["packet_digest"] = packet_digest
            if trial["observations"]:
                trial["observations"][0]["evidence"] = [{
                    "path": "src/auth.py", "start_line": 0, "end_line": 0, "excerpt": "",
                    "content_digest": hashlib.sha256(b"").hexdigest(),
                }]
            dump(trial_path, trial)
        output = self.temp / "full-revert"
        result = run_case(self.case, output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(load(output / "ledger.json")["findings"][0]["lifecycle"], "resolved")

    def test_rename_alone_never_resolves(self) -> None:
        source = FIXTURES / "06-prior-resolution-two-of-three"
        shutil.rmtree(self.case)
        shutil.copytree(source, self.case)
        packet = load(self.case / "packet.json")
        old_digest = packet["delta"][0]["old_digest"]
        packet["delta"][0]["new_digest"] = None
        packet["delta"][0]["new_mode"] = None
        packet["delta"].append({
            "path": "src/renamed.py", "old_digest": None, "old_content": None, "old_mode": None,
            "new_digest": old_digest, "new_mode": "100644",
        })
        packet["review_files"][0]["content"] = None
        packet["review_files"][0]["content_digest"] = hashlib.sha256(b"").hexdigest()
        packet["review_files"].append({"path": "src/renamed.py", "content": "same bytes\n", "content_digest": old_digest})
        # Make the old digest truly describe the added content.
        old_digest = hashlib.sha256(b"same bytes\n").hexdigest()
        packet["delta"][0]["old_digest"] = old_digest
        packet["delta"][0]["old_content"] = "same bytes\n"
        packet["delta"][1]["new_digest"] = old_digest
        packet["review_files"][1]["content_digest"] = old_digest
        dump(self.case / "packet.json", packet)
        packet_digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["packet_digest"] = packet_digest
            if trial["observations"]:
                trial["observations"][0]["evidence"] = [{
                    "path": "src/auth.py", "start_line": 0, "end_line": 0, "excerpt": "",
                    "content_digest": hashlib.sha256(b"").hexdigest(),
                }]
            dump(trial_path, trial)
        result = run_case(self.case, self.temp / "rename")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rename alone cannot resolve", result.stderr)

        # Without an invalid resolution claim, the same rename carries the prior
        # finding as persisting and the generated ledger remains renderable.
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["observations"] = []
            dump(trial_path, trial)
        carried_output = self.temp / "rename-carried"
        carried = run_case(self.case, carried_output)
        self.assertEqual(carried.returncode, 0, carried.stdout + carried.stderr)
        ledger = load(carried_output / "ledger.json")
        self.assertEqual(ledger["findings"][0]["lifecycle"], "persisting")
        cr.validate_ledger(ledger)
        self.assertTrue(cr.render_markdown(ledger).startswith("# Convergent Code Review"))

    def test_replay_reauthenticates_retained_packet_and_trial_together(self) -> None:
        output = self.temp / "auth-replay"
        self.assertEqual(run_case(self.case, output).returncode, 0)
        packet_path = output / "inputs/packet.json"
        packet = load(packet_path)
        packet["review_files"][0]["content"] = "tampered but internally digested\n"
        packet["review_files"][0]["content_digest"] = hashlib.sha256(b"tampered but internally digested\n").hexdigest()
        packet["delta"][0]["new_digest"] = packet["review_files"][0]["content_digest"]
        dump(packet_path, packet)
        replay = load(output / "replay.json")
        packet_artifact = next(item for item in replay["artifacts"] if item["role"] == "packet")
        packet_artifact["bytes"] = len(packet_path.read_bytes())
        packet_artifact["digest"] = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        dump(output / "replay.json", replay)
        verified = subprocess.run(
            ["python3", str(CLI), "verify-replay", "--replay", str(output / "replay.json")],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(verified.returncode, 0)
        self.assertIn("packet_digest", verified.stderr)

    def test_ordinary_packet_authenticates_old_and_new_bytes(self) -> None:
        packet = load(self.case / "packet.json")
        delta = packet["delta"][0]
        self.assertEqual(hashlib.sha256(delta["old_content"].encode()).hexdigest(), delta["old_digest"])
        tampered = copy.deepcopy(packet)
        tampered["delta"][0]["old_content"] += "tamper"
        with self.assertRaisesRegex(cr.ReviewError, "old_digest"):
            cr.validate_packet(tampered)

    def test_full_audit_fails_closed_on_omission_and_authenticates_empty_tree(self) -> None:
        packet = load(FIXTURES / "09-explicit-full-audit-discovery/packet.json")
        cr.validate_packet(packet)
        omitted = copy.deepcopy(packet)
        omitted["review_files"] = omitted["review_files"][:-1]
        with self.assertRaisesRegex(cr.ReviewError, "complete present review_files universe"):
            cr.validate_packet(omitted)
        forged_empty = copy.deepcopy(packet)
        forged_empty["review_files"] = []
        forged_empty["scope_commitment"]["entries"] = []
        forged_empty["scope_commitment"]["manifest_digest"] = hashlib.sha256(cr.canonical_json_bytes([])).hexdigest()
        with self.assertRaises(cr.ReviewError):
            cr.validate_packet(forged_empty)
        # A real empty Git tree/commit is accepted, proving empty is not forbidden,
        # merely required to be authenticated by the head commit.
        empty_tree = cr._git_object_id("tree", b"")
        commit_content = f"tree {empty_tree}\n\nempty fixture\n"
        empty = copy.deepcopy(packet)
        empty["head_sha"] = cr._git_object_id("commit", commit_content.encode())
        empty["delta"] = []
        empty["review_files"] = []
        empty["scope_commitment"] = {
            "object_format": "git-sha1", "commit_content": commit_content,
            "root_tree": empty_tree,
            "manifest_digest": hashlib.sha256(cr.canonical_json_bytes([])).hexdigest(),
            "entries": [],
        }
        cr.validate_packet(empty)

    def test_trusted_builder_binds_full_tree_and_old_bytes(self) -> None:
        repo = self.temp / "git-repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "review@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Review Test"], check=True)
        (repo / "changed.txt").write_text("old\n", encoding="utf-8")
        (repo / "unchanged.txt").write_text("keep\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        (repo / "changed.txt").write_text("new\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        packet_path = self.temp / "built.json"
        result = subprocess.run([
            "python3", str(CLI), "build-packet", "--repo", str(repo),
            "--repository", "host/org/repo", "--review-id", "trusted-builder",
            "--mode", "full_audit", "--base", base, "--head", "HEAD", "--output", str(packet_path),
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        packet = load(packet_path)
        self.assertEqual({item["path"] for item in packet["review_files"]}, {"changed.txt", "unchanged.txt"})
        self.assertEqual(packet["delta"][0]["old_content"], "old\n")
        cr.validate_packet(packet)

    def test_replay_rejects_manifest_ledger_and_markdown_symlinks(self) -> None:
        source = self.temp / "source"
        self.assertEqual(run_case(self.case, source).returncode, 0)
        for relative in ("replay.json", "ledger.json", "review.md"):
            with self.subTest(relative=relative):
                target = self.temp / f"symlink-{relative.replace('/', '-')}"
                shutil.copytree(source, target)
                original = target / relative
                real = target / f"real-{Path(relative).name}"
                original.rename(real)
                original.symlink_to(real.name)
                with self.assertRaises(cr.ReviewError):
                    cr.verify_replay_directory(target / "replay.json")

    def test_atomic_noreplace_publication_race_has_one_winner(self) -> None:
        destination = self.temp / "race-output"
        left = self.temp / "left"
        right = self.temp / "right"
        left.mkdir(); right.mkdir()
        (left / "winner").write_text("left", encoding="utf-8")
        (right / "winner").write_text("right", encoding="utf-8")
        script = self.temp / "race.py"
        script.write_text(
            "import importlib.util,sys\n"
            f"s=importlib.util.spec_from_file_location('cr',{str(CLI)!r});m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
            "try:m._rename_noreplace(__import__('pathlib').Path(sys.argv[1]),__import__('pathlib').Path(sys.argv[2]));raise SystemExit(0)\n"
            "except m.ReviewError:raise SystemExit(2)\n",
            encoding="utf-8",
        )
        processes = [subprocess.Popen(["python3", str(script), str(source), str(destination)]) for source in (left, right)]
        codes = sorted(process.wait() for process in processes)
        self.assertEqual(codes, [0, 2])
        self.assertIn((destination / "winner").read_text(encoding="utf-8"), {"left", "right"})

    def test_linux_sandbox_blocks_cross_trial_files_and_network(self) -> None:
        probe = self.temp / "isolation-probe.py"
        sentinel = self.temp / "sibling-secret"
        sentinel.write_text("secret", encoding="utf-8")
        probe.write_text(
            "#!/usr/bin/env python3\n"
            "import pathlib,socket,sys\n"
            "sentinel=pathlib.Path(sys.argv[-1])\n"
            "try: sentinel.read_text(); raise SystemExit(40)\n"
            "except (PermissionError,FileNotFoundError): pass\n"
            "try: socket.socket().connect(('127.0.0.1',9)); raise SystemExit(41)\n"
            "except OSError: pass\n"
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        probe.chmod(0o755)
        trial_root = self.temp / "trial-root"
        trial_root.mkdir()
        result = subprocess.run([
            str(LINUX_SANDBOX), "--root", str(trial_root), "--runner", str(probe),
            "--", str(probe), str(sentinel),
        ], cwd=trial_root, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def _git_repo(self) -> tuple[Path, str, str]:
        repo = self.temp / f"git-{len(list(self.temp.glob('git-*')))}"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "review@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Review Test"], check=True)
        (repo / "file.txt").write_text("old\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "file.txt"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        (repo / "file.txt").write_text("new\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "file.txt"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        return repo, base, head

    def test_git_object_reads_ignore_replace_refs_and_inherited_redirect_environment(self) -> None:
        repo, base, head = self._git_repo()
        subprocess.run(["git", "-C", str(repo), "replace", head, base], check=True)
        redirected = self.temp / "redirected-git-dir"
        inherited = os.environ.copy()
        inherited.update({
            "GIT_DIR": str(redirected), "GIT_WORK_TREE": str(self.temp / "elsewhere"),
            "GIT_OBJECT_DIRECTORY": str(self.temp / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(self.temp / "alternates"),
            "GIT_COMMON_DIR": str(self.temp / "common"), "GIT_INDEX_FILE": str(self.temp / "index"),
            "GIT_REPLACE_REF_BASE": "refs/hostile/replace/",
        })
        packet_path = self.temp / "immutable.json"
        result = subprocess.run([
            "python3", str(CLI), "build-packet", "--repo", str(repo),
            "--repository", "host/org/repo", "--review-id", "immutable-env",
            "--mode", "full_audit", "--base", base, "--head", head, "--output", str(packet_path),
        ], cwd=ROOT, env=inherited, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        packet = load(packet_path)
        self.assertEqual(packet["head_sha"], head)
        self.assertEqual(packet["review_files"][0]["content"], "new\n")
        self.assertEqual(packet["delta"][0]["old_content"], "old\n")

    def test_git_blob_failure_is_not_misclassified_as_path_absence(self) -> None:
        repo, base, head = self._git_repo()
        entry = cr._git_path_entry(repo, head, "file.txt")
        self.assertIsNotNone(entry)
        assert entry is not None
        object_path = repo / ".git/objects" / entry[1][:2] / entry[1][2:]
        object_path.unlink()
        with self.assertRaisesRegex(cr.ReviewError, "immutable Git blob read failed"):
            cr.build_packet_from_git(repo, "host/org/repo", "missing-object", "ordinary", base, head)

    def test_mode_only_delta_is_authenticated_in_ordinary_and_full_audit_packets(self) -> None:
        repo = self.temp / "mode-repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "review@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "Review Test"], check=True)
        script = repo / "script.sh"
        script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "script.sh"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        script.chmod(0o755)
        subprocess.run(["git", "-C", str(repo), "add", "script.sh"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "chmod"], check=True)
        head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
        for mode in ("ordinary", "full_audit"):
            with self.subTest(mode=mode):
                packet = cr.build_packet_from_git(repo, "host/org/repo", f"mode-only-{mode}", mode, base, head)
                self.assertEqual(len(packet["delta"]), 1)
                delta = packet["delta"][0]
                self.assertEqual(delta["old_digest"], delta["new_digest"])
                self.assertEqual((delta["old_mode"], delta["new_mode"]), ("100644", "100755"))
                cr.validate_packet(packet)
                forged = copy.deepcopy(packet)
                forged["delta"][0]["new_mode"] = "100644"
                with self.assertRaises(cr.ReviewError):
                    cr.validate_packet(forged)

    def test_full_audit_tree_header_ignores_message_text_and_rejects_extra_header(self) -> None:
        packet = copy.deepcopy(load(FIXTURES / "09-explicit-full-audit-discovery/packet.json"))
        commitment = packet["scope_commitment"]
        root_tree = commitment["root_tree"]
        content = commitment["commit_content"] + f"tree {root_tree}\n"
        commitment["commit_content"] = content
        packet["head_sha"] = cr._git_object_id("commit", content.encode())
        cr.validate_packet(packet)
        fabricated = copy.deepcopy(packet)
        content = fabricated["scope_commitment"]["commit_content"]
        header, message = content.split("\n\n", 1)
        forged_content = f"{header}\ntree {root_tree}\n\n{message}"
        fabricated["scope_commitment"]["commit_content"] = forged_content
        fabricated["head_sha"] = cr._git_object_id("commit", forged_content.encode())
        with self.assertRaisesRegex(cr.ReviewError, "exactly one valid root tree"):
            cr.validate_packet(fabricated)

    def test_linux_sandbox_blocks_execution_of_runner_generated_trial_file(self) -> None:
        probe = self.temp / "execution-probe.py"
        probe.write_text(
            "#!/usr/bin/env python3\n"
            "import os,pathlib,sys\n"
            "generated=pathlib.Path('generated.sh')\n"
            "generated.write_text('#!/bin/sh\\nexit 0\\n')\n"
            "generated.chmod(0o755)\n"
            "try: os.execv(str(generated.resolve()), [str(generated.resolve())])\n"
            "except PermissionError: raise SystemExit(0)\n"
            "except OSError: raise SystemExit(0)\n"
            "raise SystemExit(42)\n",
            encoding="utf-8",
        )
        probe.chmod(0o755)
        trial_root = self.temp / "execute-trial"
        trial_root.mkdir()
        result = subprocess.run([
            str(LINUX_SANDBOX), "--root", str(trial_root), "--runner", str(probe), "--", str(probe),
        ], cwd=trial_root, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prompt_evaluator_rejects_runner_symlink_substitution_for_post_run_files(self) -> None:
        runner = self.temp / "symlink-runner.py"
        runner.write_text(
            "#!/usr/bin/env python3\n"
            "import argparse,hashlib,json,pathlib\n"
            "p=argparse.ArgumentParser(); p.add_argument('--prompt'); p.add_argument('--packet'); "
            "p.add_argument('--trial-number',type=int); p.add_argument('--output'); p.add_argument('--prior-ledger'); a=p.parse_args()\n"
            "packet=pathlib.Path(a.packet); raw=packet.read_bytes(); data=json.loads(raw)\n"
            "out=pathlib.Path(a.output); real=out.with_name('real-trial.json')\n"
            "trial={'head_sha':data['head_sha'],'observations':[],'packet_digest':hashlib.sha256(raw).hexdigest(),"
            "'review_id':data['review_id'],'schema_version':'1.0.0','trial_number':a.trial_number}\n"
            "real.write_text(json.dumps(trial,sort_keys=True,separators=(',',':'))+'\\n'); out.symlink_to(real.name)\n"
            "pathlib.Path('runner.stdout').symlink_to('/dev/null')\n",
            encoding="utf-8",
        )
        runner.chmod(0o755)
        result = subprocess.run([
            "python3", str(PROMPT_EVAL), "--packet", str(FIXTURES / "01-no-findings/packet.json"),
            "--prompt-template", str(PROMPT_TEMPLATE), "--runner", str(runner),
            "--output-dir", str(self.temp / "symlink-evaluation"),
        ], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("regular non-symlink", result.stderr)

    def test_replay_rejects_symlinked_root_ancestor(self) -> None:
        source = self.temp / "ancestor-source"
        self.assertEqual(run_case(self.case, source).returncode, 0)
        real_parent = self.temp / "real-parent"
        real_parent.mkdir()
        target = real_parent / "review"
        shutil.copytree(source, target)
        linked_parent = self.temp / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        with self.assertRaisesRegex(cr.ReviewError, "without following symlinks"):
            cr.verify_replay_directory(linked_parent / "review/replay.json")

    def test_post_visibility_parent_fsync_failure_returns_committed_state(self) -> None:
        source = self.temp / "publish-source"
        destination = self.temp / "publish-destination"
        source.mkdir()
        (source / "value").write_text("committed", encoding="utf-8")
        original_fsync = cr.os.fsync
        calls = 0
        def fail_parent_fsync(descriptor):
            nonlocal calls
            calls += 1
            raise OSError("injected parent fsync failure")
        cr.os.fsync = fail_parent_fsync
        try:
            result = cr._rename_noreplace(source, destination)
        finally:
            cr.os.fsync = original_fsync
        self.assertTrue(result.visible)
        self.assertFalse(result.durable)
        self.assertIn("injected parent fsync failure", result.durability_error)
        self.assertEqual((destination / "value").read_text(encoding="utf-8"), "committed")
        self.assertFalse(source.exists())
        retry = self.temp / "retry-source"
        retry.mkdir()
        with self.assertRaises(cr.ReviewError):
            cr._rename_noreplace(retry, destination)

    def test_all_review_schemas_reject_backslash_and_c1_identities(self) -> None:
        try:
            import jsonschema
        except ImportError as exc:
            self.skipTest(str(exc))
        output = self.temp / "schema-patterns"
        self.assertEqual(run_case(FIXTURES / "01-no-findings", output).returncode, 0)
        samples = {
            "review_packet.schema.json": load(FIXTURES / "01-no-findings/packet.json"),
            "review_trial.schema.json": load(FIXTURES / "01-no-findings/trial-1.json"),
            "review_ledger.schema.json": load(output / "ledger.json"),
            "review_replay.schema.json": load(output / "replay.json"),
            "review_suppression.schema.json": load(FIXTURES / "11-authorized-suppression-retained/suppression.json"),
        }
        for schema_name, sample in samples.items():
            schema = load(ROOT / "schema" / schema_name)
            for bad in ("host\\org/repo", "host/org/\x85repo"):
                mutated = copy.deepcopy(sample)
                mutated["repository"] = bad
                with self.subTest(schema=schema_name, repository=repr(bad)):
                    with self.assertRaises(jsonschema.ValidationError):
                        jsonschema.validate(mutated, schema)
            if schema_name in ("review_packet.schema.json", "review_trial.schema.json", "review_ledger.schema.json", "review_replay.schema.json"):
                mutated = copy.deepcopy(sample)
                if schema_name == "review_packet.schema.json":
                    mutated["review_files"][0]["path"] = "src\\evil.py"
                elif schema_name == "review_trial.schema.json":
                    if not mutated["observations"]:
                        mutated = load(FIXTURES / "02-consensus-blocker/trial-1.json")
                    mutated["observations"][0]["finding"]["path"] = "src\\evil.py"
                elif schema_name == "review_ledger.schema.json":
                    ledger_path_output = self.temp / "ledger-path"
                    self.assertEqual(run_case(FIXTURES / "02-consensus-blocker", ledger_path_output).returncode, 0)
                    mutated = load(ledger_path_output / "ledger.json")
                    mutated["findings"][0]["path"] = "src\\evil.py"
                else:
                    mutated["artifacts"][0]["path"] = "inputs\\evil.json"
                with self.subTest(schema=schema_name, path="backslash"):
                    with self.assertRaises(jsonschema.ValidationError):
                        jsonschema.validate(mutated, schema)

    def test_standalone_ledger_enforces_lifecycle_consensus_and_evidence_relations(self) -> None:
        output = self.temp / "ledger-relations"
        self.assertEqual(run_case(FIXTURES / "02-consensus-blocker", output).returncode, 0)
        ledger = load(output / "ledger.json")
        missing_vote_evidence = copy.deepcopy(ledger)
        missing_vote_evidence["findings"][0]["evidence"] = missing_vote_evidence["findings"][0]["evidence"][:1]
        with self.assertRaisesRegex(cr.ReviewError, "active consensus"):
            cr.validate_ledger(missing_vote_evidence)
        bad_persisting = copy.deepcopy(ledger)
        finding = bad_persisting["findings"][0]
        finding["lifecycle"] = "persisting"
        bad_persisting["prior_ledger_digest"] = "a" * 64
        finding["consensus"] = {"active_trials": [], "resolved_trials": [1, 2]}
        finding["resolution_evidence"] = [
            {**finding["evidence"][0], "trial_number": 1}, {**finding["evidence"][0], "trial_number": 2},
        ]
        finding["evidence"] = []
        bad_persisting["counts"] = cr.calculate_counts(bad_persisting["findings"])
        with self.assertRaisesRegex(cr.ReviewError, "persisting cannot carry"):
            cr.validate_ledger(bad_persisting)
        bad_suppressed = copy.deepcopy(ledger)
        finding = bad_suppressed["findings"][0]
        finding["lifecycle"] = "suppressed"
        finding["consensus"] = {"active_trials": [], "resolved_trials": []}
        finding["evidence"] = []
        finding["suppression"] = {
            "record_digest": "b" * 64, "authorized_by": "human", "authorization_ref": "ticket/1",
            "authorized_at": "2026-09-17T00:00:00Z", "reason": "authorized",
        }
        bad_suppressed["counts"] = cr.calculate_counts(bad_suppressed["findings"])
        bad_suppressed["verdict"] = "approve"
        with self.assertRaisesRegex(cr.ReviewError, "initial suppressed finding requires"):
            cr.validate_ledger(bad_suppressed)

    def test_initial_suppressed_heads_rejected_by_validator_and_renderer(self) -> None:
        output = self.temp / "initial-suppressed-heads"
        self.assertEqual(run_case(FIXTURES / "11-authorized-suppression-retained", output).returncode, 0)
        ledger = load(output / "ledger.json")
        self.assertEqual(ledger["findings"][0]["lifecycle"], "suppressed")
        for field in ("first_seen_head", "last_seen_head"):
            altered = copy.deepcopy(ledger)
            altered["findings"][0][field] = "f" * 40
            message = rf"{field}: initial finding must equal ledger.head_sha"
            with self.subTest(field=field, surface="validate_ledger"):
                with self.assertRaisesRegex(cr.ReviewError, message):
                    cr.validate_ledger(altered)
            with self.subTest(field=field, surface="render_markdown"):
                with self.assertRaisesRegex(cr.ReviewError, message):
                    cr.render_markdown(altered)

    def test_initial_trial_three_extra_evidence_rejected_by_validator_and_renderer(self) -> None:
        output = self.temp / "initial-extra-evidence"
        self.assertEqual(run_case(FIXTURES / "02-consensus-blocker", output).returncode, 0)
        altered = load(output / "ledger.json")
        finding = altered["findings"][0]
        self.assertEqual(finding["consensus"]["active_trials"], [1, 2])
        extra = copy.deepcopy(finding["evidence"][0])
        extra["trial_number"] = 3
        finding["evidence"].append(extra)
        message = "trial attribution must exactly match active consensus"
        with self.assertRaisesRegex(cr.ReviewError, message):
            cr.validate_ledger(altered)
        with self.assertRaisesRegex(cr.ReviewError, message):
            cr.render_markdown(altered)

    def test_generated_later_suppressed_transition_validates_and_renders(self) -> None:
        shutil.rmtree(self.case)
        shutil.copytree(FIXTURES / "05-prior-persisting", self.case)
        shutil.copyfile(
            FIXTURES / "11-authorized-suppression-retained/suppression.json",
            self.case / "suppression.json",
        )
        output = self.temp / "later-suppressed"
        result = run_case(self.case, output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        ledger = load(output / "ledger.json")
        self.assertIsNotNone(ledger["prior_ledger_digest"])
        self.assertEqual(ledger["findings"][0]["lifecycle"], "suppressed")
        self.assertEqual(ledger["findings"][0]["evidence"], [])
        cr.validate_ledger(ledger)
        self.assertTrue(cr.render_markdown(ledger).startswith("# Convergent Code Review"))

    def test_generated_historical_resolution_carry_validates_and_renders(self) -> None:
        shutil.rmtree(self.case)
        shutil.copytree(FIXTURES / "08-reopened-finding", self.case)
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["observations"] = []
            dump(trial_path, trial)
        output = self.temp / "resolved-carried"
        result = run_case(self.case, output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        ledger = load(output / "ledger.json")
        finding = ledger["findings"][0]
        self.assertEqual(finding["lifecycle"], "resolved")
        self.assertEqual(finding["evidence"], [])
        self.assertEqual(finding["resolution_evidence"], [])
        cr.validate_ledger(ledger)
        self.assertTrue(cr.render_markdown(ledger).startswith("# Convergent Code Review"))

    def test_generated_prior_suppressed_carry_and_resolution_validate_and_render(self) -> None:
        initial_output = self.temp / "suppressed-prior"
        self.assertEqual(
            run_case(FIXTURES / "11-authorized-suppression-retained", initial_output).returncode,
            0,
        )
        prior = load(initial_output / "ledger.json")

        shutil.rmtree(self.case)
        shutil.copytree(FIXTURES / "06-prior-resolution-two-of-three", self.case)
        packet = load(self.case / "packet.json")
        packet["review_id"] = prior["review_id"]
        packet["base_sha"] = prior["head_sha"]
        packet["head_sha"] = "3" * 40
        dump(self.case / "packet.json", packet)
        packet_digest = hashlib.sha256((self.case / "packet.json").read_bytes()).hexdigest()
        for number in (1, 2, 3):
            trial_path = self.case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["review_id"] = prior["review_id"]
            trial["head_sha"] = packet["head_sha"]
            trial["packet_digest"] = packet_digest
            dump(trial_path, trial)
        dump(self.case / "prior-ledger.json", prior)

        carried_case = self.temp / "suppressed-carried-case"
        shutil.copytree(self.case, carried_case)
        for number in (1, 2, 3):
            trial_path = carried_case / f"trial-{number}.json"
            trial = load(trial_path)
            trial["observations"] = []
            dump(trial_path, trial)
        carried_output = self.temp / "suppressed-carried"
        carried_result = run_case(carried_case, carried_output)
        self.assertEqual(carried_result.returncode, 0, carried_result.stdout + carried_result.stderr)
        carried = load(carried_output / "ledger.json")
        self.assertEqual(carried["findings"][0]["lifecycle"], "suppressed")
        self.assertEqual(carried["findings"][0]["evidence"], [])
        cr.validate_ledger(carried)
        self.assertTrue(cr.render_markdown(carried).startswith("# Convergent Code Review"))

        resolved_output = self.temp / "suppressed-resolved"
        resolved_result = run_case(self.case, resolved_output)
        self.assertEqual(resolved_result.returncode, 0, resolved_result.stdout + resolved_result.stderr)
        resolved = load(resolved_output / "ledger.json")
        self.assertEqual(resolved["findings"][0]["lifecycle"], "resolved")
        self.assertIsNone(resolved["findings"][0]["suppression"])
        cr.validate_ledger(resolved)
        self.assertTrue(cr.render_markdown(resolved).startswith("# Convergent Code Review"))

    def test_every_object_schema_is_closed(self) -> None:
        def visit(node, path):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    self.assertIs(node.get("additionalProperties"), False, f"open object at {path}")
                for key, value in node.items():
                    visit(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, f"{path}/{index}")
        for schema_name in SCHEMAS:
            with self.subTest(schema=schema_name):
                visit(load(ROOT / "schema" / schema_name), schema_name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
