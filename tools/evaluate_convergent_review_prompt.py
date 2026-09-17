#!/usr/bin/env python3
"""Evaluate a trusted review prompt with three isolated runner invocations.

Runner contract (trusted executable):
  RUNNER --prompt PATH --packet PATH --trial-number N --output PATH [--prior-ledger PATH]

Sandbox-adapter contract (trusted executable):
  ADAPTER --root TRIAL_ROOT --runner RUNNER -- RUNNER_ARGUMENTS...

The adapter MUST enforce an isolated filesystem write/read boundary, network namespace,
PID namespace, and process session. The runner owns model/provider integration. This
harness owns exact prompt rendering, trial validation, deterministic convergence, and
a content-addressed receipt. Reviewed code is never executed by this program.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import convergent_review as cr

PLACEHOLDERS = ("{{PACKET_PATH}}", "{{TRIAL_NUMBER}}", "{{TRIAL_OUTPUT_PATH}}", "{{PRIOR_LEDGER_INSTRUCTION}}")


def render_prompt(template: str, packet: Path, trial: int, output: Path, prior: Path | None) -> str:
    missing = [token for token in PLACEHOLDERS if template.count(token) != 1]
    if missing:
        raise cr.ReviewError(f"prompt template must contain each placeholder exactly once: {', '.join(missing)}")
    prior_instruction = str(prior) if prior is not None else "none; there are no prior findings"
    return (
        template.replace("{{PACKET_PATH}}", str(packet))
        .replace("{{TRIAL_NUMBER}}", str(trial))
        .replace("{{TRIAL_OUTPUT_PATH}}", str(output))
        .replace("{{PRIOR_LEDGER_INSTRUCTION}}", prior_instruction)
    )


def evaluate(args: argparse.Namespace) -> int:
    packet_path = Path(args.packet).resolve(strict=True)
    prompt_path = Path(args.prompt_template).resolve(strict=True)
    runner = Path(args.runner).resolve(strict=True)
    isolation_adapter = Path(args.isolation_adapter).resolve(strict=True)
    prior_path = Path(args.prior_ledger).resolve(strict=True) if args.prior_ledger else None
    output = Path(args.output_dir)
    if output.exists() or output.is_symlink():
        raise cr.ReviewError(f"output directory must not already exist: {output}")
    if not runner.is_file() or runner.is_symlink() or not os.access(runner, os.X_OK):
        raise cr.ReviewError("runner must be a trusted, executable, non-symlink file")
    if not isolation_adapter.is_file() or isolation_adapter.is_symlink() or not os.access(isolation_adapter, os.X_OK):
        raise cr.ReviewError("isolation adapter must be a trusted, executable, non-symlink file")

    packet, packet_raw = cr.read_raw_json(packet_path, "packet")
    cr.require_canonical_json(packet, packet_raw, "packet")
    cr.validate_packet(packet)
    prior_raw = None
    if prior_path is not None:
        prior, prior_raw = cr.read_raw_json(prior_path, "prior ledger")
        cr.require_canonical_json(prior, prior_raw, "prior ledger")
        cr.validate_ledger(prior, "prior ledger")
        if prior["review_id"] != packet["review_id"] or prior["repository"] != packet["repository"]:
            raise cr.ReviewError("prior ledger identity does not match packet")
        if prior["head_sha"] != packet["base_sha"]:
            raise cr.ReviewError("prior ledger head does not equal packet base")
    packet_digest = cr.sha256(packet_raw)
    template_raw = cr._read_regular_nofollow(prompt_path, "prompt template")
    runner_raw = cr._read_regular_nofollow(runner, "runner")
    adapter_raw = cr._read_regular_nofollow(isolation_adapter, "isolation adapter")
    try:
        template = template_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise cr.ReviewError(f"prompt template is not UTF-8: {exc}") from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=str(output.parent)))
    evaluation_root = staging / "evaluation"
    evaluation_root.mkdir()
    verified_root = staging / ".verified-trials"
    verified_root.mkdir()
    trials: list[Path] = []
    receipts: list[dict[str, object]] = []
    try:
        for trial_number in (1, 2, 3):
            trial_root = evaluation_root / f"trial-{trial_number}"
            trial_root.mkdir()
            trial_packet = trial_root / "packet.json"
            cr._write_relative_regular_nofollow(trial_root, "packet.json", packet_raw, f"trial {trial_number} packet")
            trial_prior = None
            if prior_raw is not None:
                trial_prior = trial_root / "prior-ledger.json"
                cr._write_relative_regular_nofollow(
                    trial_root, "prior-ledger.json", prior_raw, f"trial {trial_number} prior ledger",
                )
            trial_output = trial_root / "trial.json"
            rendered = render_prompt(template, trial_packet, trial_number, trial_output, trial_prior)
            rendered_raw = rendered.encode("utf-8")
            prompt_file = trial_root / "prompt.md"
            cr._write_relative_regular_nofollow(trial_root, "prompt.md", rendered_raw, f"trial {trial_number} prompt")
            env = {
                "HOME": str(trial_root / "home"),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            }
            Path(env["HOME"]).mkdir()
            runner_command = [
                str(runner), "--prompt", str(prompt_file), "--packet", str(trial_packet),
                "--trial-number", str(trial_number), "--output", str(trial_output),
            ]
            if trial_prior is not None:
                runner_command.extend(["--prior-ledger", str(trial_prior)])
            isolated_command = [
                str(isolation_adapter), "--root", str(trial_root), "--runner", str(runner),
                "--", *runner_command,
            ]
            completed = subprocess.run(
                isolated_command,
                cwd=trial_root,
                env=env,
                text=True,
                capture_output=True,
                timeout=args.timeout_seconds,
                check=False,
                start_new_session=True,
            )
            cr._write_relative_regular_nofollow(
                trial_root, "runner.stdout", completed.stdout.encode("utf-8"), f"trial {trial_number} stdout",
            )
            cr._write_relative_regular_nofollow(
                trial_root, "runner.stderr", completed.stderr.encode("utf-8"), f"trial {trial_number} stderr",
            )
            if completed.returncode != 0:
                raise cr.ReviewError(f"trial {trial_number}: runner exited {completed.returncode}")
            if cr._read_relative_regular_nofollow(trial_root, "packet.json", f"trial {trial_number} packet") != packet_raw:
                raise cr.ReviewError(f"trial {trial_number}: runner substituted packet.json")
            if cr._read_relative_regular_nofollow(trial_root, "prompt.md", f"trial {trial_number} prompt") != rendered_raw:
                raise cr.ReviewError(f"trial {trial_number}: runner substituted prompt.md")
            if prior_raw is not None and cr._read_relative_regular_nofollow(
                trial_root, "prior-ledger.json", f"trial {trial_number} prior ledger",
            ) != prior_raw:
                raise cr.ReviewError(f"trial {trial_number}: runner substituted prior-ledger.json")
            trial_raw = cr._read_relative_regular_nofollow(trial_root, "trial.json", f"trial {trial_number}")
            trial = cr.parse_json_bytes(trial_raw, f"trial {trial_number}")
            cr.require_canonical_json(trial, trial_raw, f"trial {trial_number}")
            cr.validate_trial(trial, packet, packet_digest, f"trial {trial_number}")
            if trial["trial_number"] != trial_number:
                raise cr.ReviewError(f"trial {trial_number}: output trial_number mismatch")
            verified_trial = verified_root / f"trial-{trial_number}.json"
            cr._write_relative_regular_nofollow(
                verified_root, verified_trial.name, trial_raw, f"verified trial {trial_number}",
            )
            trials.append(verified_trial)
            receipts.append({
                "trial_number": trial_number,
                "prompt_digest": cr.sha256(rendered_raw),
                "trial_digest": cr.sha256(trial_raw),
                "isolated_packet_digest": packet_digest,
                "runner_exit": completed.returncode,
                "isolation_adapter_digest": cr.sha256(adapter_raw),
            })

        converge_args = argparse.Namespace(
            packet=str(packet_path),
            trial=[str(path) for path in trials],
            prior_ledger=str(prior_path) if prior_path else None,
            suppression=[],
            output_dir=str(staging / "review"),
        )
        cr.cmd_converge(converge_args)
        receipt = {
            "schema_version": cr.SCHEMA_VERSION,
            "packet_digest": packet_digest,
            "prompt_template_digest": cr.sha256(template_raw),
            "runner_digest": cr.sha256(runner_raw),
            "trials": receipts,
            "review_replay_digest": cr.sha256((staging / "review/replay.json").read_bytes()),
        }
        cr._write_relative_regular_nofollow(
            staging, "prompt-evaluation.json", cr.canonical_json_bytes(receipt), "prompt evaluation receipt",
        )
        shutil.rmtree(verified_root)
        cr._fsync_tree(staging)
        publication = cr._rename_noreplace(staging, output)
        if not publication.durable:
            print(
                f"evaluate_convergent_review_prompt: warning: output published at {output}, but "
                f"parent-directory durability failed: {publication.durability_error}",
                file=sys.stderr,
            )
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--prompt-template", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument(
        "--isolation-adapter",
        default=str(Path(__file__).with_name("linux_trial_sandbox.sh")),
        help="trusted executable implementing the mandatory per-trial sandbox contract",
    )
    parser.add_argument("--prior-ledger")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        if not 1 <= args.timeout_seconds <= 3600:
            raise cr.ReviewError("timeout-seconds must be between 1 and 3600")
        return evaluate(args)
    except (cr.ReviewError, OSError, UnicodeDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"evaluate_convergent_review_prompt: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
