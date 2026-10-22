#!/usr/bin/env python3
"""Fixed, independent compatibility vectors for the three canonical JSON formats.

The expected bytes below are literal vectors, not values recomputed by the
functions under test. They pin the distinctions that feed hashes and receipts:

* tools/start_path.py         -- ASCII-escaped, no trailing newline
* tools/workflow_assurance.py -- UTF-8 non-ASCII preserved, no trailing newline
* tools/convergent_review.py  -- UTF-8 non-ASCII preserved, trailing newline
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
VALUE = {
    "z": "café/日本語",
    "a": [1, True, None],
    "receipt": {"exit_code": 0, "stdout": {"sha256": "00" * 32}},
}

VECTORS = {
    "start_path": {
        "module": "start_path.py",
        "function": "canonical_bytes",
        "hex": (
            '7b2261223a5b312c747275652c6e756c6c5d2c2272656365697074223a7b22657869745f636f6465223a302c227374646f75'
            '74223a7b22736861323536223a22303030303030303030303030303030303030303030303030303030303030303030303030'
            '30303030303030303030303030303030303030303030303030303030227d7d2c227a223a226361665c75303065392f5c7536'
            '3565355c75363732635c7538613965227d'
        ),
        "sha256": "5b110b988bbbc786e0ddece9de81d2710450fbb1dfe510d6c8123ac2faf8d1d8",
    },
    "workflow_assurance": {
        "module": "workflow_assurance.py",
        "function": "canonical",
        "hex": (
            '7b2261223a5b312c747275652c6e756c6c5d2c2272656365697074223a7b22657869745f636f6465223a302c227374646f75'
            '74223a7b22736861323536223a22303030303030303030303030303030303030303030303030303030303030303030303030'
            '30303030303030303030303030303030303030303030303030303030227d7d2c227a223a22636166c3a92fe697a5e69cace8'
            'aa9e227d'
        ),
        "sha256": "c89db68e78121b0c4d35c4fd3a350e78a7e4a68ee8864d56aa1ff2975146a7c2",
    },
    "convergent_review": {
        "module": "convergent_review.py",
        "function": "canonical_json_bytes",
        "hex": (
            '7b2261223a5b312c747275652c6e756c6c5d2c2272656365697074223a7b22657869745f636f6465223a302c227374646f75'
            '74223a7b22736861323536223a22303030303030303030303030303030303030303030303030303030303030303030303030'
            '30303030303030303030303030303030303030303030303030303030227d7d2c227a223a22636166c3a92fe697a5e69cace8'
            'aa9e227d0a'
        ),
        "sha256": "8fdab2b9efc3dc55e2b129a18e7b4349b6f5af430f098d6da3fca3da22cd3a5a",
    },
}


def load(name: str):
    path = HERE / VECTORS[name]["module"]
    spec = importlib.util.spec_from_file_location(f"format_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    for name, vector in VECTORS.items():
        module = load(name)
        actual = getattr(module, vector["function"])(VALUE)
        expected = bytes.fromhex(vector["hex"])
        if actual != expected:
            raise AssertionError(f"{name}: canonical bytes drifted")
        if hashlib.sha256(actual).hexdigest() != vector["sha256"]:
            raise AssertionError(f"{name}: canonical digest drifted")
        if name == "start_path" and b"\\u00e9" not in actual:
            raise AssertionError("start_path must keep ASCII escaping")
        if name != "start_path" and "café".encode() not in actual:
            raise AssertionError(f"{name} must preserve non-ASCII UTF-8")
        if name != "convergent_review" and actual.endswith(b"\n"):
            raise AssertionError(f"{name} must not append a trailing newline")
        if name == "convergent_review" and not actual.endswith(b"\n"):
            raise AssertionError("convergent_review must append exactly one trailing newline")
    print("PASS canonical-format vectors: start_path / workflow_assurance / convergent_review distinct and stable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
