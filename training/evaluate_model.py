#!/usr/bin/env python3
"""
Run the existing golden backend tests and copy the JSON reports into training/reports/.

This does not modify the tests. It wraps them so training experiments can be tracked
from inside the training directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
REPORTS_DIR = ROOT / "reports"

COMMAND_TMP_REPORT = Path("/tmp/command_test_results.json")
PARAM_TMP_REPORT = Path("/tmp/param_test_results.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the live backend with the golden datasets.")
    parser.add_argument("--label", default="manual")
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def run_test(script: Path, python_bin: str) -> int:
    result = subprocess.run(
        [python_bin, str(script)],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode


def load_json(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Expected report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    args = parse_args()
    label_dir = REPORTS_DIR / args.label
    label_dir.mkdir(parents=True, exist_ok=True)

    command_code = run_test(REPO_ROOT / "tests" / "test_command_dataset.py", args.python)
    param_code = run_test(REPO_ROOT / "tests" / "test_param_dataset.py", args.python)

    command_report = load_json(COMMAND_TMP_REPORT)
    param_report = load_json(PARAM_TMP_REPORT)

    shutil.copy2(COMMAND_TMP_REPORT, label_dir / "command_results.json")
    shutil.copy2(PARAM_TMP_REPORT, label_dir / "param_results.json")

    summary = {
        "label": args.label,
        "command_exit_code": command_code,
        "param_exit_code": param_code,
        "command_accuracy": command_report["pass"] / max(command_report["total"], 1),
        "param_perfect_accuracy": param_report["pass"] / max(param_report["total"], 1),
        "param_acceptable_accuracy": (param_report["pass"] + param_report["partial"]) / max(param_report["total"], 1),
    }
    (label_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
