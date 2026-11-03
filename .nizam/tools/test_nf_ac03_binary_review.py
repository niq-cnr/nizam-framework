#!/usr/bin/env python3
"""NF-AC03 acceptance suite: typed binary coverage with honest limits in convergent review.

Covers Finding F09 and requirement NF-R03:
- Versioned review packet schema ("1.0.0" text-only, "1.1.0" typed text + opaque_binary + absent)
- Ordinary and full_audit binary inventory with exact path, Git mode, blob OID, byte length, SHA-256
- Declared vs validated media type sniffing (PNG, JPEG, GIF, WEBP, PDF, WASM, ZIP, ELF/Mach-O, ICO, octet-stream)
- Complete delta coverage: additions, deletions, modifications, mode changes, and renames
- Provenance, limits (no truncation, max_bytes enforced), inspection_scope (integrity_only vs trusted_processor_derived)
- Rejection of changed bytes, mode, path, stale head, conflicting media types, oversized blobs,
  symlink traversal/binary substitution, unknown schema versions, and line-excerpt evidence on opaque binaries
- Invalidation of external binary/UI approvals when binary bytes, mode, path, media type, or head change
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import jsonschema

TOOLS_DIR = Path(__file__).resolve().parent
ROOT_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import convergent_review as cr  # noqa: E402


SAMPLE_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
SAMPLE_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
SAMPLE_WASM = b"\x00asm\x01\x00\x00\x00"
SAMPLE_PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"


def _git_raw(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class NfAc03BinaryReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(
            tempfile.mkdtemp(
                prefix="nizam-nf-ac03-",
                dir="/private/tmp" if Path("/private/tmp").is_dir() else None,
            )
        ).resolve()
        self.schema = json.loads((ROOT_DIR / "schema/review_packet.schema.json").read_text(encoding="utf-8"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _init_repo(self, name: str = "repo") -> Path:
        repo = self.temp_dir / name
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "--object-format=sha1", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.email", "nf-ac03@example.test"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "user.name", "NF AC03"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "commit.gpgsign", "false"], check=True)
        subprocess.run(["git", "-C", str(repo), "config", "core.filemode", "true"], check=True)
        return repo

    def test_valid_binary_inventory_deltas_and_schema_validation_in_ordinary_and_full_audit(self) -> None:
        """Build 1.1.0 packets with additions, deletions, modifications, mode changes, and renames across text and binary."""
        repo = self._init_repo()
        (repo / "assets").mkdir(parents=True, exist_ok=True)
        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "assets/old_icon.png").write_bytes(SAMPLE_PNG)
        (repo / "assets/ obsolete.wasm").write_bytes(SAMPLE_WASM)
        (repo / "assets/banner.jpg").write_bytes(SAMPLE_JPEG)
        (repo / "src/app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = _git_raw(repo, "rev-parse", "HEAD")

        # 1. Rename assets/old_icon.png -> assets/new_icon.png (same bytes)
        (repo / "assets/old_icon.png").unlink()
        (repo / "assets/new_icon.png").write_bytes(SAMPLE_PNG)
        # 2. Delete assets/ obsolete.wasm
        (repo / "assets/ obsolete.wasm").unlink()
        # 3. Mode change on assets/banner.jpg (100644 -> 100755)
        (repo / "assets/banner.jpg").chmod(0o755)
        # 4. Add assets/manual.pdf
        (repo / "assets/manual.pdf").write_bytes(SAMPLE_PDF)
        # 5. Modify src/app.py
        (repo / "src/app.py").write_text("def run():\n    return 2\n", encoding="utf-8")

        subprocess.run(["git", "-C", str(repo), "add", "--all"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        head = _git_raw(repo, "rev-parse", "HEAD")

        # 1.0.0 mode must refuse binary blobs explicitly
        with self.assertRaisesRegex(cr.ReviewError, "refuses non-UTF-8/binary blobs in 1.0.0 mode"):
            cr.build_packet_from_git(
                repo, "host/org/repo", "ac03-v1-reject", "ordinary", base, head, packet_version="1.0.0"
            )

        # Auto and 1.1.0 modes emit valid 1.1.0 packets for both ordinary and full_audit
        for mode in ("ordinary", "full_audit"):
            packet = cr.build_packet_from_git(
                repo, "host/org/repo", f"ac03-{mode}", mode, base, head, packet_version="auto"
            )
            self.assertEqual(packet["schema_version"], "1.1.0")
            jsonschema.Draft202012Validator(self.schema).validate(packet)
            cr.validate_packet(packet)

            delta_by_path = {d["path"]: d for d in packet["delta"]}
            self.assertEqual(delta_by_path["assets/old_icon.png"]["change_kind"], "deleted")
            self.assertEqual(delta_by_path["assets/new_icon.png"]["change_kind"], "renamed")
            self.assertEqual(delta_by_path["assets/new_icon.png"]["renamed_from"], "assets/old_icon.png")
            self.assertEqual(delta_by_path["assets/ obsolete.wasm"]["change_kind"], "deleted")
            self.assertEqual(delta_by_path["assets/banner.jpg"]["change_kind"], "mode_changed")
            self.assertEqual(delta_by_path["assets/banner.jpg"]["old_mode"], "100644")
            self.assertEqual(delta_by_path["assets/banner.jpg"]["new_mode"], "100755")
            self.assertEqual(delta_by_path["assets/manual.pdf"]["change_kind"], "added")
            self.assertEqual(delta_by_path["assets/manual.pdf"]["new_validated_media_type"], "application/pdf")
            self.assertEqual(delta_by_path["src/app.py"]["change_kind"], "modified")
            self.assertEqual(delta_by_path["src/app.py"]["new_record_kind"], "text")

            rf_by_path = {f["path"]: f for f in packet["review_files"]}
            self.assertEqual(rf_by_path["assets/old_icon.png"]["record_kind"], "absent")
            self.assertEqual(rf_by_path["assets/old_icon.png"]["inspection_scope"], "absent")
            self.assertEqual(rf_by_path["assets/new_icon.png"]["record_kind"], "opaque_binary")
            self.assertEqual(rf_by_path["assets/new_icon.png"]["validated_media_type"], "image/png")
            self.assertEqual(rf_by_path["assets/new_icon.png"]["inspection_scope"], "integrity_only")
            self.assertFalse(rf_by_path["assets/new_icon.png"]["limits"]["semantic_inspection_performed"])
            self.assertIsNone(rf_by_path["assets/new_icon.png"]["content"])
            self.assertEqual(rf_by_path["src/app.py"]["record_kind"], "text")
            self.assertEqual(rf_by_path["src/app.py"]["inspection_scope"], "text_semantic")
            self.assertTrue(rf_by_path["src/app.py"]["limits"]["semantic_inspection_performed"])

    def test_changed_bytes_mode_path_stale_head_and_conflicting_media_types_rejected(self) -> None:
        """Reject tampered binary digests/modes/paths, stale bindings, and conflicting media types."""
        repo = self._init_repo("tamper-repo")
        (repo / "logo.png").write_bytes(SAMPLE_PNG)
        subprocess.run(["git", "-C", str(repo), "add", "logo.png"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = _git_raw(repo, "rev-parse", "HEAD")

        (repo / "logo.png").write_bytes(SAMPLE_PNG + b"\x00\x01")
        subprocess.run(["git", "-C", str(repo), "add", "logo.png"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        head = _git_raw(repo, "rev-parse", "HEAD")

        packet = cr.build_packet_from_git(repo, "host/org/repo", "ac03-tamper", "full_audit", base, head)

        # 1. Tamper binary content_digest
        bad_digest = copy.deepcopy(packet)
        bad_digest["review_files"][0]["content_digest"] = "1" * 64
        with self.assertRaisesRegex(cr.ReviewError, "new_digest: does not match"):
            cr.validate_packet(bad_digest)

        # 2. Tamper binary mode
        bad_mode = copy.deepcopy(packet)
        bad_mode["review_files"][0]["mode"] = "100755"
        with self.assertRaisesRegex(cr.ReviewError, r"new_\* metadata does not match"):
            cr.validate_packet(bad_mode)

        # 3. Tamper provenance commit_sha (stale binding)
        bad_prov = copy.deepcopy(packet)
        bad_prov["review_files"][0]["provenance"]["commit_sha"] = base
        with self.assertRaisesRegex(cr.ReviewError, "provenance.commit_sha: must equal packet.head_sha"):
            cr.validate_packet(bad_prov)

        # 4. Drop binary from full_audit review_files to fake full-tree text review
        dropped = copy.deepcopy(packet)
        dropped["review_files"] = []
        with self.assertRaisesRegex(cr.ReviewError, "current content is missing"):
            cr.validate_packet(dropped)

        # 5. Conflicting media type: JPEG bytes in a .png file
        bad_media_repo = self._init_repo("bad-media")
        (bad_media_repo / "spoof.png").write_bytes(SAMPLE_JPEG)
        subprocess.run(["git", "-C", str(bad_media_repo), "add", "spoof.png"], check=True)
        subprocess.run(["git", "-C", str(bad_media_repo), "commit", "-qm", "spoof"], check=True)
        spoof_head = _git_raw(bad_media_repo, "rev-parse", "HEAD")
        with self.assertRaisesRegex(cr.ReviewError, "conflicting media type declaration: declared image/png but validated image/jpeg"):
            cr.build_packet_from_git(
                bad_media_repo, "host/org/repo", "ac03-spoof", "full_audit", spoof_head, spoof_head
            )

        # 6. Conflicting media type: ASCII text in a .png file
        text_in_png_repo = self._init_repo("text-in-png")
        (text_in_png_repo / "fake.png").write_text("plain ascii text\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(text_in_png_repo), "add", "fake.png"], check=True)
        subprocess.run(["git", "-C", str(text_in_png_repo), "commit", "-qm", "fake"], check=True)
        fake_head = _git_raw(text_in_png_repo, "rev-parse", "HEAD")
        with self.assertRaisesRegex(cr.ReviewError, "declared binary media type image/png conflicts with validated"):
            cr.build_packet_from_git(
                text_in_png_repo, "host/org/repo", "ac03-fake", "full_audit", fake_head, fake_head, packet_version="1.1.0"
            )

    def test_oversized_blobs_symlink_traversal_and_version_compatibility(self) -> None:
        """Reject oversized binary blobs, unsafe symlink targets, binary symlinks, and unknown packet versions."""
        repo = self._init_repo("limits-repo")
        (repo / "blob.bin").write_bytes(b"\x00\x01\x02\x03" * 64)
        subprocess.run(["git", "-C", str(repo), "add", "blob.bin"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        head = _git_raw(repo, "rev-parse", "HEAD")

        # Oversized binary rejected when max_binary_bytes < len(blob)
        with self.assertRaisesRegex(cr.ReviewError, "exceeds max_bytes 32"):
            cr.build_packet_from_git(
                repo, "host/org/repo", "ac03-oversize", "full_audit", head, head, max_binary_bytes=32
            )

        # Truncated flag set to True in packet rejected
        valid_pkt = cr.build_packet_from_git(repo, "host/org/repo", "ac03-ok", "full_audit", head, head)
        trunc_pkt = copy.deepcopy(valid_pkt)
        trunc_pkt["review_files"][0]["limits"]["truncated"] = True
        with self.assertRaisesRegex(cr.ReviewError, "truncated: must be false"):
            cr.validate_packet(trunc_pkt)

        # Unknown schema version rejected
        unknown_ver = copy.deepcopy(valid_pkt)
        unknown_ver["schema_version"] = "2.0.0"
        with self.assertRaisesRegex(cr.ReviewError, "unsupported version"):
            cr.validate_packet(unknown_ver)

        # Symlink pointing outside repository (`../escape`) rejected
        sym_repo = self._init_repo("sym-repo")
        (sym_repo / "escape_link").symlink_to("../outside/secret.txt")
        subprocess.run(["git", "-C", str(sym_repo), "add", "escape_link"], check=True)
        subprocess.run(["git", "-C", str(sym_repo), "commit", "-qm", "sym"], check=True)
        sym_head = _git_raw(sym_repo, "rev-parse", "HEAD")
        with self.assertRaisesRegex(cr.ReviewError, "symlink target"):
            cr.build_packet_from_git(sym_repo, "host/org/repo", "ac03-sym", "full_audit", sym_head, sym_head)

        # Symlink mode 120000 classified as opaque_binary in packet rejected
        forged_sym = copy.deepcopy(valid_pkt)
        forged_sym["review_files"][0]["mode"] = "120000"
        with self.assertRaisesRegex(cr.ReviewError, "symlink mode 120000 cannot be classified as opaque_binary"):
            cr.validate_packet(forged_sym)

    def test_inspection_scope_processor_identity_and_binary_approval_invalidation(self) -> None:
        """Enforce integrity_only vs trusted_processor_derived rules and invalidate binary approvals on any drift."""
        repo = self._init_repo("scope-repo")
        (repo / "ui.png").write_bytes(SAMPLE_PNG)
        (repo / "view.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "ui.png", "view.py"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
        base = _git_raw(repo, "rev-parse", "HEAD")

        (repo / "ui.png").write_bytes(SAMPLE_PNG + b"\x99")
        (repo / "view.py").write_text("x = 2\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "ui.png", "view.py"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "head"], check=True)
        head = _git_raw(repo, "rev-parse", "HEAD")

        # 1. Default integrity_only packet
        pkt = cr.build_packet_from_git(repo, "host/org/repo", "ac03-scope", "ordinary", base, head)
        pkt_raw = cr.canonical_json_bytes(pkt)
        pkt_digest = cr.sha256(pkt_raw)

        # Claiming semantic_inspection_performed=True on integrity_only is rejected
        bad_claim = copy.deepcopy(pkt)
        ui_entry = next(f for f in bad_claim["review_files"] if f["path"] == "ui.png")
        ui_entry["limits"]["semantic_inspection_performed"] = True
        with self.assertRaisesRegex(cr.ReviewError, "integrity_only opaque_binary record cannot claim"):
            cr.validate_packet(bad_claim)

        # Claiming trusted_processor_derived without processor_identity is rejected
        bad_proc = copy.deepcopy(pkt)
        ui_entry2 = next(f for f in bad_proc["review_files"] if f["path"] == "ui.png")
        ui_entry2["inspection_scope"] = "trusted_processor_derived"
        ui_entry2["limits"]["semantic_inspection_performed"] = True
        with self.assertRaisesRegex(cr.ReviewError, "trusted_processor_derived opaque_binary record requires"):
            cr.validate_packet(bad_proc)

        # Valid trusted_processor_derived with processor_identity passes
        proc_id = {
            "processor_id": "nizam-png-inspector",
            "version": "1.0.0",
            "config_digest": "a" * 64,
            "output_digest": "b" * 64,
        }
        pkt_proc = cr.build_packet_from_git(
            repo, "host/org/repo", "ac03-proc", "ordinary", base, head,
            processor_identities={"ui.png": proc_id},
        )
        jsonschema.Draft202012Validator(self.schema).validate(pkt_proc)
        cr.validate_packet(pkt_proc)
        ui_proc = next(f for f in pkt_proc["review_files"] if f["path"] == "ui.png")
        self.assertEqual(ui_proc["inspection_scope"], "trusted_processor_derived")
        self.assertEqual(ui_proc["processor_identity"], proc_id)

        # Line-excerpt evidence on opaque_binary is rejected, while 0-0 empty excerpt is accepted
        ui_rf = next(f for f in pkt["review_files"] if f["path"] == "ui.png")
        with self.assertRaisesRegex(cr.ReviewError, "cannot support line-excerpt semantic evidence"):
            cr.validate_current_evidence(
                {
                    "path": "ui.png",
                    "start_line": 1,
                    "end_line": 1,
                    "excerpt": "fake line",
                    "content_digest": ui_rf["content_digest"],
                },
                pkt,
                "evidence[0]",
            )
        cr.validate_current_evidence(
            {
                "path": "ui.png",
                "start_line": 0,
                "end_line": 0,
                "excerpt": "",
                "content_digest": ui_rf["content_digest"],
            },
            pkt,
            "evidence[0]",
        )

        # Converge 3 trials on 1.1.0 packet
        trials = []
        for tnum in (1, 2, 3):
            trials.append({
                "schema_version": "1.0.0",
                "review_id": "ac03-scope",
                "trial_number": tnum,
                "packet_digest": pkt_digest,
                "head_sha": head,
                "observations": [
                    {
                        "action": "active",
                        "finding": {
                            "severity": "minor",
                            "category": "integrity",
                            "path": "ui.png",
                            "symbol": "ui.png",
                            "rule": "binary-asset-updated",
                            "title": "Binary UI asset changed",
                            "description": "Binary UI asset bytes changed without semantic text diff.",
                        },
                        "evidence": [
                            {
                                "path": "ui.png",
                                "start_line": 0,
                                "end_line": 0,
                                "excerpt": "",
                                "content_digest": ui_rf["content_digest"],
                            }
                        ],
                    }
                ],
            })
        trial_digests = {t["trial_number"]: cr.sha256(cr.canonical_json_bytes(t)) for t in trials}
        ledger = cr.converge_documents(pkt, pkt_digest, trials, trial_digests, None, None, [])
        self.assertEqual(ledger["verdict"], "approve")
        self.assertEqual(ledger["counts"]["new"], 1)

        # External binary/UI approval validation and invalidation on byte, mode, path, or head change
        approval = {
            "schema_version": "1.1.0",
            "repository": "host/org/repo",
            "review_id": "ac03-scope",
            "head_sha": head,
            "approved_by": "operator@example.test",
            "approved_at": "2026-10-27T12:00:00Z",
            "scope": "ui_visual_baseline",
            "artifacts": [
                {
                    "path": "ui.png",
                    "mode": ui_rf["mode"],
                    "object_id": ui_rf["object_id"],
                    "byte_length": ui_rf["byte_length"],
                    "content_digest": ui_rf["content_digest"],
                    "validated_media_type": ui_rf["validated_media_type"],
                }
            ],
        }
        cr.validate_binary_approval(approval, pkt)

        # Mutate binary bytes in approval -> invalidated!
        stale_bytes = copy.deepcopy(approval)
        stale_bytes["artifacts"][0]["content_digest"] = "f" * 64
        with self.assertRaisesRegex(cr.ReviewError, "binary bytes changed for ui.png; prior approval is invalidated"):
            cr.validate_binary_approval(stale_bytes, pkt)

        # Mutate binary mode in approval -> invalidated!
        stale_mode = copy.deepcopy(approval)
        stale_mode["artifacts"][0]["mode"] = "100755"
        with self.assertRaisesRegex(cr.ReviewError, "binary Git mode changed for ui.png; prior approval is invalidated"):
            cr.validate_binary_approval(stale_mode, pkt)

        # Mutate binary path in approval -> invalidated!
        stale_path = copy.deepcopy(approval)
        stale_path["artifacts"][0]["path"] = "other.png"
        with self.assertRaisesRegex(cr.ReviewError, "absent or changed path in packet"):
            cr.validate_binary_approval(stale_path, pkt)

        # Mutate head_sha in approval -> invalidated!
        stale_head = copy.deepcopy(approval)
        stale_head["head_sha"] = base
        with self.assertRaisesRegex(cr.ReviewError, "stale approval bound to"):
            cr.validate_binary_approval(stale_head, pkt)


if __name__ == "__main__":
    unittest.main()
