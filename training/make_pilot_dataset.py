#!/usr/bin/env python3
"""
Build a small pilot dataset focused on vague parameter search weaknesses.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "data" / "processed"
OUT_DIR = SRC_DIR / "pilot"
RANDOM_SEED = 3407

PRIORITY_CATEGORIES = {
    "radio_hard_case",
    "radio",
    "battery",
    "failsafe",
    "gps",
    "navigation",
    "vague",
    "battery_typo",
    "gps_typo",
}
PRIORITY_TASK_TYPES = {"param_search", "param_explanations"}


def load_rows(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def keep_row(row: dict) -> bool:
    return row.get("category") in PRIORITY_CATEGORIES or row.get("task_type") in PRIORITY_TASK_TYPES


def write_rows(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def main() -> None:
    random.seed(RANDOM_SEED)

    train_rows = [row for row in load_rows(SRC_DIR / "train.jsonl") if keep_row(row)]
    val_rows = [row for row in load_rows(SRC_DIR / "validation.jsonl") if keep_row(row)]

    random.shuffle(train_rows)
    random.shuffle(val_rows)

    train_rows = train_rows[:320]
    val_rows = val_rows[:40]

    write_rows(OUT_DIR / "train.jsonl", train_rows)
    write_rows(OUT_DIR / "validation.jsonl", val_rows)

    print(f"pilot train={len(train_rows)} val={len(val_rows)} -> {OUT_DIR}")


if __name__ == "__main__":
    main()
