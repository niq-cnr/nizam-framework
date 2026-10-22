"""Independently adjudicated evaluation corpora (JR-16).

A corpus freezes immutable, independently labeled reference cases for the
semantic families and enforces the split discipline that prevents leakage:

- every evaluable example has an immutable id, a label rubric, an adjudicator,
  a lineage group and a data-eligibility classification;
- calibration and held-out sets never share a lineage group (variants, retries,
  descendants and related tasks stay together in one split);
- missing or ambiguous labels are excluded or evaluated as ambiguity, never
  silently forced into a category;
- deterministic governance counterexamples remain executable code regressions
  and are never delegated to a model.
"""

from __future__ import annotations

import dataclasses
from typing import Any


class CorpusError(ValueError):
    """A corpus entry or split violates the freeze/leakage discipline."""


@dataclasses.dataclass(frozen=True)
class CorpusEntry:
    entry_id: str
    family: str
    primitive: str
    lineage_group: str
    label: str | None
    adjudicator: str
    eligibility: str  # "internal" | "external" | "exclude"
    input: dict[str, Any]


def validate_entry(entry: CorpusEntry, *, rubric: set[str]) -> CorpusEntry:
    if not entry.entry_id or not entry.lineage_group or not entry.adjudicator:
        raise CorpusError(f"entry {entry.entry_id!r} is missing an immutable id, group or adjudicator")
    if entry.eligibility not in ("internal", "external", "exclude"):
        raise CorpusError(f"entry {entry.entry_id!r} has unknown eligibility {entry.eligibility!r}")
    if entry.label is not None and entry.label not in rubric:
        raise CorpusError(f"entry {entry.entry_id!r} label {entry.label!r} is not in the rubric")
    return entry


def freeze_corpus(
    entries: list[CorpusEntry],
    *,
    version: str,
    rubric: set[str],
    adjudicator: str,
) -> dict[str, Any]:
    """Validate and seal a corpus; return the frozen manifest."""
    if not version or not adjudicator:
        raise CorpusError("a corpus needs a version and an adjudicator")
    frozen = [validate_entry(entry, rubric=rubric) for entry in entries]
    ids = [entry.entry_id for entry in frozen]
    if len(set(ids)) != len(ids):
        raise CorpusError("corpus entry ids must be unique")
    return {
        "schema_version": 1,
        "version": version,
        "adjudicator": adjudicator,
        "rubric": sorted(rubric),
        "entry_count": len(frozen),
        "entries": entries,
        "frozen": True,
    }


def split_by_lineage(
    entries: list[CorpusEntry],
    *,
    holdout_group_ids: set[str],
) -> tuple[list[CorpusEntry], list[CorpusEntry]]:
    """Split into calibration and held-out sets, keeping each lineage group whole.

    A lineage group that appears in ``holdout_group_ids`` goes entirely to the
    held-out set; all others are calibration. This guarantees predictions on a
    calibration example can never leak through a shared descendant into holdout.
    """
    groups: dict[str, list[CorpusEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.lineage_group, []).append(entry)
    unknown = set(holdout_group_ids) - set(groups)
    if unknown:
        raise CorpusError(f"holdout names unknown lineage groups: {sorted(unknown)}")
    calibration: list[CorpusEntry] = []
    holdout: list[CorpusEntry] = []
    for group, group_entries in groups.items():
        target = holdout if group in holdout_group_ids else calibration
        target.extend(group_entries)
    return calibration, holdout


def assert_no_lineage_leakage(calibration: list[CorpusEntry], holdout: list[CorpusEntry]) -> None:
    cal_groups = {entry.lineage_group for entry in calibration}
    for entry in holdout:
        if entry.lineage_group in cal_groups:
            raise CorpusError(
                f"lineage group {entry.lineage_group!r} appears in both calibration and holdout"
            )
