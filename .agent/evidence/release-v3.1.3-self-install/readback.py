#!/usr/bin/env python3
"""Read the actual installed Framework index, skill, entrypoint and provenance."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
primary = Path(sys.argv[1]).resolve(strict=True)
payload = primary / ".nizam"
index_bytes = (payload / "NIZAM.json").read_bytes()
index = json.loads(index_bytes)
skill_relative = next(cap["authoritative_source"] for cap in index["capabilities"] if cap["id"] == "nizam-tools-skill")
skill = (payload / skill_relative).resolve(strict=True)
if not skill.is_relative_to(payload.resolve(strict=True)):
    raise ValueError("installed skill resolves outside payload")
skill_bytes = skill.read_bytes()
skill_bytes.decode("utf-8")
entrypoint_bytes = (payload / "tools/start_path.py").read_bytes()
def git(*args):
    return subprocess.check_output(["git", "-C", str(primary), *args], text=True).strip()
print(json.dumps({"destination": str(primary), "repository": git("remote", "get-url", "origin"),
    "head": git("rev-parse", "HEAD"), "provenance": json.loads((payload / "provenance.json").read_text()),
    "NIZAM_sha256": hashlib.sha256(index_bytes).hexdigest(), "SKILL_sha256": hashlib.sha256(skill_bytes).hexdigest(),
    "entrypoint_sha256": hashlib.sha256(entrypoint_bytes).hexdigest(),
    "loaded_index_framework_version": index["framework"]["version"], "resolved_skill": str(skill),
    "qualification": "Actual installed file reads and entrypoint smoke; no fresh LLM session or PRIMARY typed commissioning claimed"}, sort_keys=True))
