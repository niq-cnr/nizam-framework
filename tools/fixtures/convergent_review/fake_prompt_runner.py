#!/usr/bin/env python3
"""Hermetic observation runner used only by the prompt-evaluation tests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", required=True)
parser.add_argument("--packet", required=True)
parser.add_argument("--trial-number", required=True, type=int)
parser.add_argument("--output", required=True)
args = parser.parse_args()

prompt = Path(args.prompt).read_text(encoding="utf-8")
packet_raw = Path(args.packet).read_bytes()
packet = json.loads(packet_raw)
assert f'"trial_number": {args.trial_number}' in prompt
assert str(Path(args.output)) in prompt
trial = {
    "schema_version": "1.0.0",
    "review_id": packet["review_id"],
    "trial_number": args.trial_number,
    "packet_digest": hashlib.sha256(packet_raw).hexdigest(),
    "head_sha": packet["head_sha"],
    "observations": [],
}
Path(args.output).write_text(json.dumps(trial, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
