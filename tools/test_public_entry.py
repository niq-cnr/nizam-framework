#!/usr/bin/env python3
"""Read the shipped public entry, require the three start paths, and verify B3/B4 invariants."""

from pathlib import Path
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GUIDE = ROOT / "docs/guide" / "index.html"
NIZAM_INDEX = ROOT / "NIZAM.json"
SKILL_MD = ROOT / "tools" / "SKILL.md"
SKILL_JSON = ROOT / "tools" / "skill.json"
CIRCUIT_BREAKER_MD = ROOT / "methodology" / "03_circuit_breaker.md"
ACCEPTANCE_BARS_MD = ROOT / "standard" / "acceptance_bars.md"
METHODOLOGY_README = ROOT / "methodology" / "README.md"
SELF_GOVERNANCE_MD = ROOT / "docs" / "planning" / "SELF_GOVERNANCE.md"
VALIDATE_SH = ROOT / "tools" / "validate.sh"
BOOTSTRAP_SH = ROOT / "bootstrap.sh"
PAYLOAD_INTEGRITY_PY = ROOT / "tools" / "payload_integrity.py"


def section(text, start, end):
    """Return the slice from start through the line before end."""
    begin = text.index(start)
    finish = text.index(end, begin)
    return text[begin:finish]


def body_after_frontmatter(text: str) -> str:
    """Return markdown body after YAML frontmatter."""
    if not text.startswith("---\n"):
        return text
    end = text.index("\n---\n", 4)
    return text[end + 5 :]


def frontmatter_field(text: str, key: str) -> str:
    """Extract a scalar top-level field from YAML frontmatter."""
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.index("\n---\n", 4)
    fm = text[4:end]
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, flags=re.MULTILINE)
    if not m:
        raise ValueError(f"missing frontmatter key {key}")
    val = m.group(1).strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        val = val[1:-1]
    return val


def require(text, needle):
    if needle not in text:
        raise SystemExit("missing required text: " + needle)


def forbid(text, needle, context):
    if needle in text:
        raise SystemExit(f"forbidden text in {context}: {needle}")


def _copy_authored_payload(dest: Path, tag: str | None = None, sha: str = "606d11ee84deff0d3b7934cbfd715223d64ac79d") -> str:
    fw_ver = json.loads(NIZAM_INDEX.read_text(encoding="utf-8"))["framework"]["version"]
    resolved_tag = tag or f"v{fw_ver}"
    dest.mkdir(parents=True, exist_ok=True)
    for mod in ("standard", "templates", "schema", "tools", "methodology", "ecosystem"):
        shutil.copytree(ROOT / mod, dest / mod)
    shutil.copy2(ROOT / "NIZAM.json", dest / "NIZAM.json")
    prov = {
        "framework_version": fw_ver,
        "source_url": str(ROOT),
        "tag": resolved_tag,
        "resolved_sha": sha,
        "installed_at": "2026-10-18T15:00:00Z",
    }
    (dest / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    return resolved_tag


def _create_ref_git_repo(ref_repo: Path, tag: str) -> str:
    ref_repo.mkdir(parents=True, exist_ok=True)
    for mod in ("standard", "templates", "schema", "tools", "methodology", "ecosystem"):
        shutil.copytree(ROOT / mod, ref_repo / mod)
    shutil.copy2(ROOT / "NIZAM.json", ref_repo / "NIZAM.json")
    subprocess.run(["git", "-C", str(ref_repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(ref_repo), "config", "user.email", "test@nizam.local"], check=True)
    subprocess.run(["git", "-C", str(ref_repo), "config", "user.name", "Test Bot"], check=True)
    subprocess.run(["git", "-C", str(ref_repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(ref_repo), "commit", "-qm", "authored payload snapshot"], check=True)
    subprocess.run(["git", "-C", str(ref_repo), "tag", "-a", tag, "-m", "release tag", "HEAD"], check=True)
    res = subprocess.run(
        ["git", "-C", str(ref_repo), "rev-parse", f"refs/tags/{tag}^{{commit}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def verify_b3_and_b4() -> None:
    # V5 & C3: Skill version parity and active stopping-policy / provenance coherence
    skill_md_text = SKILL_MD.read_text(encoding="utf-8")
    skill_json_data = json.loads(SKILL_JSON.read_text(encoding="utf-8"))
    skill_md_ver = frontmatter_field(skill_md_text, "version")
    skill_json_ver = skill_json_data.get("version")
    if skill_md_ver != skill_json_ver:
        raise SystemExit(f"skill version mismatch: SKILL.md={skill_md_ver} vs skill.json={skill_json_ver}")

    cb_text = CIRCUIT_BREAKER_MD.read_text(encoding="utf-8")
    cb_desc = frontmatter_field(cb_text, "description")
    cb_body = body_after_frontmatter(cb_text)
    forbid(cb_desc, "forbidden fourth attempt", "methodology/03_circuit_breaker.md description")
    forbid(cb_body, "subordinate to this 3-attempt cap; if a blind\n  win is not achieved by attempt 3", "methodology/03_circuit_breaker.md body")
    forbid(cb_body, "begins a fourth attempt without having\nrespected this counter has violated Section 4", "methodology/03_circuit_breaker.md body")
    require(cb_body, "same unresolved defect\nsignature without a viable bounded decomposition")

    ab_body = body_after_frontmatter(ACCEPTANCE_BARS_MD.read_text(encoding="utf-8"))
    forbid(ab_body, "rather than making a forbidden fourth autonomous attempt", "standard/acceptance_bars.md body")
    require(ab_body, "same unresolved\n  gap without a viable bounded decomposition")

    planning_body = body_after_frontmatter((ROOT / "methodology" / "00_planning.md").read_text(encoding="utf-8"))
    forbid(planning_body, "if 3 attempts fail, it halts and escalates", "methodology/00_planning.md body")

    exec_body = body_after_frontmatter((ROOT / "methodology" / "01_execution.md").read_text(encoding="utf-8"))
    forbid(exec_body, "A fourth attempt on the same contract is forbidden", "methodology/01_execution.md body")

    run_state_schema_text = (ROOT / "schema" / "run_state.schema.json").read_text(encoding="utf-8")
    forbid(run_state_schema_text, "3-strike attempt counters per feature/gate", "schema/run_state.schema.json")

    skill_body = body_after_frontmatter(skill_md_text)
    forbid(skill_body, "pending\nphase016; source routing does not upgrade the installed v1.5.0 payload", "tools/SKILL.md body")
    require(skill_body, ".nizam/provenance.json")
    require(skill_body, "--mode prepare|publish|finalize")

    meth_readme_body = body_after_frontmatter(METHODOLOGY_README.read_text(encoding="utf-8"))
    forbid(meth_readme_body, "and no fourth attempt", "methodology/README.md body")

    nizam_index = json.loads(NIZAM_INDEX.read_text(encoding="utf-8"))
    cb_cap = next(c for c in nizam_index["capabilities"] if c["id"] == "nizam-circuit-breaker")
    forbid(cb_cap["summary"], "3-strike attempt limit", "NIZAM.json nizam-circuit-breaker summary")

    # V6: Authored release payload vs. repository .nizam/ self-installation documented
    readme_text = README.read_text(encoding="utf-8")
    self_gov_body = body_after_frontmatter(SELF_GOVERNANCE_MD.read_text(encoding="utf-8"))
    require(readme_text, "never the repository's own `.nizam/`")
    require(self_gov_body, "never the tagged tree's `.nizam/`")

    # V3, V4 & C2: Exercise payload_integrity.py, bootstrap.sh --verify-only, and validate.sh --payload
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    with tempfile.TemporaryDirectory(prefix="nizam-b3b4-test-") as tmp:
        tmp_path = Path(tmp)
        fw_ver = json.loads(NIZAM_INDEX.read_text(encoding="utf-8"))["framework"]["version"]
        test_tag = f"v{fw_ver}"
        ref_repo = tmp_path / "ref-repo"
        ref_sha = _create_ref_git_repo(ref_repo, test_tag)
        payload = tmp_path / ".nizam"
        _copy_authored_payload(payload, tag=test_tag, sha=ref_sha)

        # 1. Clean payload against unbound --source-root reports directory_match_unbound (never verified)
        r_clean_src = subprocess.run(
            [sys.executable, str(PAYLOAD_INTEGRITY_PY), "--payload-dir", str(payload), "--source-root", str(ROOT)],
            env=env,
            text=True,
            capture_output=True,
        )
        if (
            r_clean_src.returncode != 0
            or "content_integrity=directory_match_unbound" not in r_clean_src.stdout
            or "content_integrity=verified" in r_clean_src.stdout
        ):
            raise SystemExit(f"unbound --source-root payload_integrity.py failed:\n{r_clean_src.stdout}{r_clean_src.stderr}")

        r_vo_src = subprocess.run(
            ["bash", str(BOOTSTRAP_SH), "--verify-only", "--target", str(payload), "--tag", test_tag, "--source-root", str(ROOT)],
            env=env,
            text=True,
            capture_output=True,
        )
        if (
            r_vo_src.returncode != 0
            or "content_integrity=directory_match_unbound" not in r_vo_src.stdout
            or "content_integrity=verified" in r_vo_src.stdout
        ):
            raise SystemExit(f"unbound --source-root bootstrap.sh --verify-only failed:\n{r_vo_src.stdout}{r_vo_src.stderr}")

        # 2. Clean payload with --git-repo + --expected-sha + --require-content-integrity passes with content_integrity=verified
        r_vo_clean = subprocess.run(
            [
                "bash",
                str(BOOTSTRAP_SH),
                "--verify-only",
                "--target",
                str(payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_clean.returncode != 0 or "content_integrity=verified" not in r_vo_clean.stdout:
            raise SystemExit(f"clean commit-bound bootstrap.sh --verify-only failed:\n{r_vo_clean.stdout}{r_vo_clean.stderr}")

        # 3. Appended harmless comment to tools/start_path.py fails --verify-only (V3 case 2)
        sp_file = payload / "tools" / "start_path.py"
        orig_sp_bytes = sp_file.read_bytes()
        sp_file.write_bytes(orig_sp_bytes + b"\n# harmless comment appended\n")
        r_vo_comment = subprocess.run(
            [
                "bash",
                str(BOOTSTRAP_SH),
                "--verify-only",
                "--target",
                str(payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_comment.returncode == 0:
            raise SystemExit("bootstrap.sh --verify-only unexpectedly passed with appended comment in tools/start_path.py")
        sp_file.write_bytes(orig_sp_bytes)

        # 4. Unexpected extra file under payload fails --verify-only (V3 case 3)
        extra_file = payload / "tools" / "unexpected_extra.txt"
        extra_file.write_text("unexpected\n", encoding="utf-8")
        r_vo_extra = subprocess.run(
            [
                "bash",
                str(BOOTSTRAP_SH),
                "--verify-only",
                "--target",
                str(payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_extra.returncode == 0:
            raise SystemExit("bootstrap.sh --verify-only unexpectedly passed with unexpected extra file")
        extra_file.unlink()

        # 5. Executable mode drift fails --verify-only
        orig_mode = sp_file.stat().st_mode
        sp_file.chmod(orig_mode ^ stat.S_IXUSR)
        r_vo_mode = subprocess.run(
            [
                "bash",
                str(BOOTSTRAP_SH),
                "--verify-only",
                "--target",
                str(payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_mode.returncode == 0:
            raise SystemExit("bootstrap.sh --verify-only unexpectedly passed with executable mode drift")
        sp_file.chmod(orig_mode)

        # 6. C2 ordinary consumer & C2 tampered checker:
        # Exercise standalone bootstrap.sh in an ordinary consumer directory with no sibling tools/ directory.
        consumer_dir = tmp_path / "ordinary-consumer"
        consumer_dir.mkdir(parents=True, exist_ok=True)
        standalone_bootstrap = consumer_dir / "bootstrap.sh"
        shutil.copy2(BOOTSTRAP_SH, standalone_bootstrap)
        consumer_payload = consumer_dir / ".nizam"
        shutil.copytree(payload, consumer_payload)

        # Ordinary consumer strict verification succeeds with --git-repo and --expected-sha
        r_ord_ok = subprocess.run(
            [
                "bash",
                str(standalone_bootstrap),
                "--verify-only",
                "--target",
                str(consumer_payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            cwd=str(consumer_dir),
            env=env,
            text=True,
            capture_output=True,
        )
        if r_ord_ok.returncode != 0 or "content_integrity=verified" not in r_ord_ok.stdout:
            raise SystemExit(
                f"ordinary consumer strict verification failed:\n{r_ord_ok.stdout}{r_ord_ok.stderr}"
            )

        # Ordinary consumer required verification without --git-repo fails (no provenance/CWD shortcut)
        r_ord_no_repo = subprocess.run(
            [
                "bash",
                str(standalone_bootstrap),
                "--verify-only",
                "--target",
                str(consumer_payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--require-content-integrity",
            ],
            cwd=str(consumer_dir),
            env=env,
            text=True,
            capture_output=True,
        )
        if r_ord_no_repo.returncode == 0 or "content_integrity=verified" in r_ord_no_repo.stdout:
            raise SystemExit("ordinary consumer verification without --git-repo unexpectedly passed")

        # C2 tampered checker: replace installed payload_integrity.py with print-only exit-0 stub + extra file
        installed_checker = consumer_payload / "tools" / "payload_integrity.py"
        orig_checker_bytes = installed_checker.read_bytes()
        installed_checker.write_text("#!/usr/bin/env python3\nimport sys\nprint('STUB PASS')\nsys.exit(0)\n", encoding="utf-8")
        (consumer_payload / "tools" / "unexpected_stub_extra.txt").write_text("tampered\n", encoding="utf-8")
        r_tampered = subprocess.run(
            [
                "bash",
                str(standalone_bootstrap),
                "--verify-only",
                "--target",
                str(consumer_payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
                "--git-repo",
                str(ref_repo),
                "--require-content-integrity",
            ],
            cwd=str(consumer_dir),
            env=env,
            text=True,
            capture_output=True,
        )
        if r_tampered.returncode == 0 or "content_integrity=verified" in r_tampered.stdout or "STUB PASS" in r_tampered.stdout:
            raise SystemExit(
                f"C2 tampered checker unexpectedly passed or executed target stub:\n{r_tampered.stdout}{r_tampered.stderr}"
            )
        installed_checker.write_bytes(orig_checker_bytes)
        (consumer_payload / "tools" / "unexpected_stub_extra.txt").unlink()

        # C2 unbound directory: modify NDS.md identically in consumer_payload and unbound source_root copy;
        # running with --expected-sha and --require-content-integrity must fail and never report content_integrity=verified
        unbound_src = tmp_path / "unbound-src"
        shutil.copytree(ref_repo, unbound_src, ignore=shutil.ignore_patterns(".git"))
        nds_payload = consumer_payload / "standard" / "NDS.md"
        nds_src = unbound_src / "standard" / "NDS.md"
        orig_nds = nds_payload.read_bytes()
        nds_payload.write_bytes(orig_nds + b"\n<!-- identical unbound modification -->\n")
        nds_src.write_bytes(orig_nds + b"\n<!-- identical unbound modification -->\n")
        r_unbound_req = subprocess.run(
            [
                "bash",
                str(standalone_bootstrap),
                "--verify-only",
                "--target",
                str(consumer_payload),
                "--tag",
                test_tag,
                "--source-root",
                str(unbound_src),
                "--expected-sha",
                ref_sha,
                "--require-content-integrity",
            ],
            cwd=str(consumer_dir),
            env=env,
            text=True,
            capture_output=True,
        )
        if r_unbound_req.returncode == 0 or "content_integrity=verified" in r_unbound_req.stdout:
            raise SystemExit(
                f"C2 unbound directory with --expected-sha and --require-content-integrity unexpectedly succeeded:\n"
                f"{r_unbound_req.stdout}{r_unbound_req.stderr}"
            )
        nds_payload.write_bytes(orig_nds)

        # C2 downgrade bug: --source-root=--audit-invalid-reference with --require-content-integrity and --expected-sha
        r_downgrade = subprocess.run(
            [
                "bash",
                str(standalone_bootstrap),
                "--verify-only",
                "--target",
                str(consumer_payload),
                "--tag",
                test_tag,
                "--source-root=--audit-invalid-reference",
                "--expected-sha",
                ref_sha,
                "--require-content-integrity",
            ],
            cwd=str(consumer_dir),
            env=env,
            text=True,
            capture_output=True,
        )
        if r_downgrade.returncode == 0 or "PASS" in r_downgrade.stdout:
            raise SystemExit(
                f"C2 downgrade bug (--source-root=--audit-invalid-reference) unexpectedly passed:\n"
                f"{r_downgrade.stdout}{r_downgrade.stderr}"
            )

        # 7. Structural-only mode discloses content_integrity=not_checked and rejects --expected-sha
        r_vo_struct = subprocess.run(
            ["bash", str(BOOTSTRAP_SH), "--verify-only", "--structural-only", "--target", str(payload), "--tag", test_tag],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_struct.returncode != 0 or "structural_only; content_integrity=not_checked" not in r_vo_struct.stdout:
            raise SystemExit(f"structural-only verify-only unexpected result:\n{r_vo_struct.stdout}{r_vo_struct.stderr}")

        r_vo_struct_sha = subprocess.run(
            [
                "bash",
                str(BOOTSTRAP_SH),
                "--verify-only",
                "--structural-only",
                "--target",
                str(payload),
                "--tag",
                test_tag,
                "--expected-sha",
                ref_sha,
            ],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_vo_struct_sha.returncode == 0:
            raise SystemExit("verify-only --structural-only with --expected-sha unexpectedly passed")

        # 8. validate.sh --payload reports non-conflated summary (V4)
        r_val_payload = subprocess.run(
            ["bash", str(payload / "tools" / "validate.sh"), "--payload"],
            env=env,
            text=True,
            capture_output=True,
        )
        expected_summary = (
            "SUMMARY (payload mode): 10 exercised passed, 0 failed, "
            "2 not-applicable (C11, C16), 1 skipped (C6), 3 out-of-scope (C12, C14, C15); "
            "content_integrity=not_checked, operational_acceptance=not_assessed"
        )
        if r_val_payload.returncode != 0 or expected_summary not in r_val_payload.stdout:
            raise SystemExit(f"validate.sh --payload summary mismatch:\n{r_val_payload.stdout}{r_val_payload.stderr}")

        # 9. C13 rejects version mismatch between tools/skill.json and tools/SKILL.md (V5)
        sj_path = payload / "tools" / "skill.json"
        sj_data = json.loads(sj_path.read_text(encoding="utf-8"))
        sj_data["version"] = "0.0.99"
        sj_path.write_text(json.dumps(sj_data, indent=2) + "\n", encoding="utf-8")
        r_val_mismatch = subprocess.run(
            ["bash", str(payload / "tools" / "validate.sh"), "--payload"],
            env=env,
            text=True,
            capture_output=True,
        )
        if r_val_mismatch.returncode == 0 or "does not match entry_point tools/SKILL.md frontmatter version" not in r_val_mismatch.stdout:
            raise SystemExit(
                f"validate.sh --payload did not reject skill.json/SKILL.md version mismatch:\n"
                f"{r_val_mismatch.stdout}{r_val_mismatch.stderr}"
            )


def main():
    readme = README.read_text(encoding="utf-8")
    guide = GUIDE.read_text(encoding="utf-8")
    fw_version = json.loads(NIZAM_INDEX.read_text(encoding="utf-8"))["framework"]["version"]
    paths = section(readme, "## Start paths", "## Quickstart")
    guide_paths = section(guide, 'id="start-paths"', 'id="execution-loop"')
    install = section(readme, "## Quickstart", "## Local governance")

    for text in (paths, guide_paths):
        require(text, "New feature")
        require(text, "Bug fix")
        require(text, "Small unambiguous change")
        require(text, "Implementation may begin only after the contract is approved")
        require(text, "independent post-implementation check")
        require(text, "recorded verification result")
        require(text, "assessed cause")
        require(text, "scoped fix")
        require(text, "does not require the full feature-gate stack")
        require(text, "Implementation may begin once the intent is recorded")
        require(text, "tools/start_path.py begin bugfix")
        require(text, "tools/start_path.py done bugfix")
        require(text, "tools/start_path.py begin small-change")
        require(text, "tools/start_path.py done small-change")
        for banned in ("surpass", "superior", "world class", "matches Superpowers",
                       "matches BMAD", "matches Spec Kit"):
            if banned in text:
                raise SystemExit("comparison claim in public entry: " + banned)

    require(install, f"--tag v{fw_version}")
    require(install, "never a floating branch (`main`, `master`, `HEAD` are all refused)")
    require(install, "`tools/validate.sh`")
    require(paths, "Spec Kit")
    require(paths, "Superpowers")
    require(paths, "BMAD Method")

    # Ensure docs/guide/index.html has no stale v0.1.0 pins or pre-015/016 claims
    for stale_guide in (
        "v0.1.0",
        "Framework-side only so far",
        "schemas, adapters and a controller belong to later features",
    ):
        if stale_guide in guide:
            raise SystemExit(f"stale token in docs/guide/index.html: {stale_guide}")
    require(guide, f"--tag v{fw_version}")
    require(guide, "NIZAM_MUTATION_ADAPTER")
    require(guide, "tools/start_path.py classify")
    require(guide, "tools/start_path.py publish")

    # Ensure shipped payload docs have no residual universal 3-strike or phase016 placeholder claims in their bodies
    def _strip_frontmatter(md_text: str) -> str:
        if md_text.startswith("---\n"):
            parts = md_text.split("\n---\n", 1)
            if len(parts) == 2:
                return parts[1]
        return md_text

    preflight_body = _strip_frontmatter((ROOT / "ecosystem" / "01_clean_state_preflight.md").read_text(encoding="utf-8"))
    if "3-strike attempt limit" in preflight_body:
        raise SystemExit("stale '3-strike attempt limit' in ecosystem/01_clean_state_preflight.md")
    for rel_doc in (
        "methodology/10_live_runtime_sessions.md",
        "methodology/11_sbcl_runtime_binding.md",
        "schema/README.md",
    ):
        doc_body = _strip_frontmatter((ROOT / rel_doc).read_text(encoding="utf-8"))
        if "phase016" in doc_body:
            raise SystemExit(f"stale 'phase016' reference in {rel_doc}")

    verify_b3_and_b4()
    print("public-entry: feature, bug-fix, and small-change paths present")
    print("public-entry: install pin, payload integrity, payload summary, and policy/metadata coherence verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())


