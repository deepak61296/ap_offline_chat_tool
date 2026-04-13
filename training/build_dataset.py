#!/usr/bin/env python3
"""
Build a fine-tuning dataset for the ArduPilot AI backend.

The generated training data is intentionally aligned to the current backend:
- short natural reply + JSON tool block for actionable agent requests
- text-only concise answers for parameter explanations and search results
- strong emphasis on vague parameter queries and radio/RC cases
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
PARAM_DB_PATH = REPO_ROOT / "backend" / "apm.pdef.json"
OUTPUT_DIR = ROOT / "data" / "processed"
RAW_DOCS_DIR = ROOT / "data" / "raw_docs"

SYSTEM_PROMPT = (
    "You are a drone copilot. Respond briefly and output tool calls as JSON for commands. "
    "Use search_param for fuzzy parameter lookup, explain_param for 'what does X do', "
    "get_param for reading an exact parameter, and text-only responses for pure explanations."
)

RANDOM_SEED = 3407

SEARCH_TOPICS = {
    "battery": {
        "prefixes": ["BATT_", "BATT2_"],
        "queries": [
            "battery stuff",
            "battery settings",
            "battery voltage limits ardupilot",
            "battery warning params",
            "battery setup parameters",
        ],
    },
    "failsafe": {
        "prefixes": ["FS_", "BATT_FS", "RC_FS"],
        "queries": [
            "safety things",
            "failsafe settings ardupilot",
            "signal loss failsafe config",
            "battery dies failsafe",
            "safety params",
        ],
    },
    "gps": {
        "prefixes": ["GPS_"],
        "queries": [
            "gps settings",
            "gps params",
            "satellite accuracy setting",
            "gps delay issue fix",
            "gps config ardupilot",
        ],
    },
    "radio": {
        "prefixes": ["RC"],
        "queries": [
            "rc calibration min max",
            "radio endpoints config",
            "rc settings ardupilot",
            "rc speed update rate",
            "rc trim center value",
        ],
    },
    "navigation": {
        "prefixes": ["WPNAV_", "RTL_", "LOIT_", "FENCE_"],
        "queries": [
            "speed settings",
            "waypoint speed param",
            "rtl speed setting",
            "loiter speed config",
            "fence settings",
        ],
    },
    "arming": {
        "prefixes": ["ARMING_", "DISARM_"],
        "queries": [
            "arming params",
            "arming checks disable",
            "disarm delay setting",
            "arm using rudder stick",
            "arming safety checks list",
        ],
    },
}

TOOL_PATTERNS = [
    {
        "tool": "arm",
        "user_templates": ["arm the drone", "arm now", "spin up the motors"],
        "reply": "Arming the drone.",
        "params": {},
    },
    {
        "tool": "disarm",
        "user_templates": ["disarm", "cut the motors", "stop motors now"],
        "reply": "Disarming the drone.",
        "params": {},
    },
    {
        "tool": "takeoff",
        "user_templates": ["take off to {altitude} meters", "takeoff {altitude}m", "ascend to {altitude} meters"],
        "reply": "Taking off to {altitude} meters.",
        "params": {"altitude": [10, 15, 20, 25, 30]},
    },
    {
        "tool": "land",
        "user_templates": ["land", "bring it down", "land the drone now"],
        "reply": "Landing the drone.",
        "params": {},
    },
    {
        "tool": "rtl",
        "user_templates": ["return to launch", "bring it back", "rtl now"],
        "reply": "Returning to launch.",
        "params": {},
    },
    {
        "tool": "change_mode",
        "user_templates": ["change mode to {mode}", "switch to {mode}", "set flight mode to {mode}"],
        "reply": "Changing mode to {mode}.",
        "params": {"mode": ["GUIDED", "LOITER", "AUTO", "RTL", "LAND"]},
    },
    {
        "tool": "set_speed",
        "user_templates": ["set speed to {speed} m/s", "fly at {speed} m/s", "change speed to {speed}"],
        "reply": "Setting speed to {speed} m/s.",
        "params": {"speed": [3, 5, 7, 10, 12]},
    },
    {
        "tool": "move",
        "user_templates": ["move {direction} {distance} meters", "fly {direction} for {distance}m"],
        "reply": "Moving {direction} {distance} meters.",
        "params": {
            "direction": ["north", "south", "east", "west", "forward", "backward", "left", "right"],
            "distance": [5, 10, 15, 20, 30],
        },
    },
]

MISSPELLINGS = {
    "battery": ["baterry", "battrey"],
    "gps": ["gsp", "gpz"],
    "failsafe": ["failsaf", "fail safe"],
    "parameter": ["paramter", "parm"],
}


@dataclass
class Parameter:
    name: str
    description: str
    display_name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the ArduPilot fine-tuning dataset.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--train-ratio", type=float, default=0.88)
    parser.add_argument("--validation-ratio", type=float, default=0.08)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    parser.add_argument("--include-docs", action="store_true")
    parser.add_argument("--docs-dir", default=str(RAW_DOCS_DIR))
    return parser.parse_args()


def load_parameters() -> List[Parameter]:
    raw = json.loads(PARAM_DB_PATH.read_text(encoding="utf-8"))
    params: List[Parameter] = []
    for _, group in raw.items():
        if not isinstance(group, dict):
            continue
        for name, info in group.items():
            if not isinstance(info, dict):
                continue
            params.append(
                Parameter(
                    name=name,
                    description=(info.get("Description") or "").strip(),
                    display_name=(info.get("DisplayName") or "").strip(),
                )
            )
    return params


def assistant_with_json(reply: str, tool: str, params: Dict) -> str:
    payload = [{"tool": tool, "params": params}] if params else [{"tool": tool}]
    return f"{reply}\n```json\n{json.dumps(payload, ensure_ascii=True)}\n```"


def build_tool_examples(rng: random.Random) -> List[Dict]:
    rows: List[Dict] = []
    for pattern in TOOL_PATTERNS:
        for template in pattern["user_templates"]:
            for _ in range(6):
                values = {}
                for key, choices in pattern["params"].items():
                    values[key] = rng.choice(choices)
                user_text = template.format(**values)
                reply = pattern["reply"].format(**values)
                params = values.copy()
                rows.append(
                    make_row(
                        user_text,
                        assistant_with_json(reply, pattern["tool"], params),
                        task_type="agent_tool_calls",
                        category=pattern["tool"],
                        source="synthetic_tools",
                        weight=1.0,
                    )
                )
    return rows


def build_exact_param_examples(params: Sequence[Parameter], rng: random.Random) -> List[Dict]:
    rows: List[Dict] = []
    sample = rng.sample(list(params), k=min(160, len(params)))
    for param in sample:
        explain_prompts = [
            f"what does {param.name} do",
            f"explain {param.name}",
            f"what is {param.name} for",
        ]
        get_prompts = [
            f"get {param.name}",
            f"what is parameter {param.name}",
            f"read param {param.name}",
        ]
        for prompt in explain_prompts:
            rows.append(
                make_row(
                    prompt,
                    assistant_with_json(f"Let me explain {param.name}.", "explain_param", {"name": param.name}),
                    task_type="param_grounding",
                    category="exact_explain",
                    source="param_db",
                    weight=1.0,
                )
            )
        for prompt in get_prompts:
            rows.append(
                make_row(
                    prompt,
                    assistant_with_json(f"Getting parameter {param.name}.", "get_param", {"name": param.name}),
                    task_type="param_grounding",
                    category="exact_get",
                    source="param_db",
                    weight=1.0,
                )
            )
    return rows


def group_params_by_topic(params: Sequence[Parameter]) -> Dict[str, List[Parameter]]:
    grouped: Dict[str, List[Parameter]] = defaultdict(list)
    for param in params:
        for topic, config in SEARCH_TOPICS.items():
            if any(param.name.startswith(prefix) for prefix in config["prefixes"]):
                grouped[topic].append(param)
    return grouped


def build_search_examples(grouped: Dict[str, List[Parameter]], rng: random.Random) -> List[Dict]:
    rows: List[Dict] = []
    for topic, config in SEARCH_TOPICS.items():
        matches = grouped.get(topic, [])
        if not matches:
            continue
        top_params = [p.name for p in matches[:4]]
        summary = ", ".join(top_params[:3])
        for query in config["queries"]:
            rows.append(
                make_row(
                    query,
                    assistant_with_json(f"Searching parameters related to {topic}.", "search_param", {"query": topic}),
                    task_type="param_search",
                    category=topic,
                    source="topic_templates",
                    weight=2.0 if topic in {"radio", "battery", "navigation"} else 1.3,
                )
            )
            rows.append(
                make_row(
                    f"in ardupilot what controls {query}",
                    f"Relevant parameters include {summary}. Start with those and verify the exact one on the vehicle.",
                    task_type="param_explanations",
                    category=topic,
                    source="topic_templates",
                    weight=1.0,
                )
            )
        for typo in MISSPELLINGS.get(topic, []):
            rows.append(
                make_row(
                    f"{typo} settings",
                    assistant_with_json(f"Searching parameters related to {topic}.", "search_param", {"query": topic}),
                    task_type="param_search",
                    category=f"{topic}_typo",
                    source="topic_templates",
                    weight=2.0,
                )
            )
    return rows


def build_radio_hard_cases(grouped: Dict[str, List[Parameter]]) -> List[Dict]:
    names = {p.name for p in grouped.get("radio", [])}
    rows: List[Dict] = []
    hard_cases = [
        ("rc calibration min max", ["RC1_MIN", "RC1_MAX"]),
        ("radio endpoints config", ["RC1_MIN", "RC1_MAX"]),
        ("rc trim center value", ["RC1_TRIM"]),
        ("rc channel trim drift", ["RC1_TRIM"]),
        ("rc speed update rate", ["RC_SPEED"]),
        ("rc input speed lag", ["RC_SPEED"]),
        ("rc settings ardupilot", ["RC1_MIN", "RC1_MAX", "RC1_TRIM"]),
        ("radio calibration params", ["RC1_MIN", "RC1_MAX", "RC1_TRIM"]),
    ]
    for prompt, required in hard_cases:
        filtered = [name for name in required if name in names]
        if not filtered:
            continue
        text = "Relevant parameters: " + ", ".join(filtered) + "."
        rows.append(
            make_row(
                prompt,
                assistant_with_json("Searching parameters related to radio calibration.", "search_param", {"query": "radio calibration"}),
                task_type="param_search",
                category="radio_hard_case",
                source="hardcoded_failures",
                weight=3.0,
            )
        )
        rows.append(
            make_row(
                f"which rc params should i check for {prompt}",
                text,
                task_type="param_explanations",
                category="radio_hard_case",
                source="hardcoded_failures",
                weight=2.5,
            )
        )
    return rows


def build_negative_examples() -> List[Dict]:
    prompts = [
        "make drone fly like ironman",
        "increase happiness of drone",
        "wifi password for autopilot",
        "turn drone into submarine mode",
    ]
    return [
        make_row(
            prompt,
            "That request does not map to a valid ArduPilot command or parameter. Please describe the flight action or parameter you want.",
            task_type="negative_examples",
            category="no_match",
            source="hardcoded_negatives",
            weight=1.0,
        )
        for prompt in prompts
    ]


def load_docs_rows(docs_dir: Path, rng: random.Random) -> List[Dict]:
    rows: List[Dict] = []
    if not docs_dir.exists():
        return rows
    for path in sorted(docs_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        title = raw.get("title") or path.stem
        for snippet in raw.get("snippets", [])[:20]:
            snippet_text = normalize_whitespace(snippet)
            if len(snippet_text) < 80:
                continue
            prompt = rng.choice(
                [
                    f"summarize ardupilot guidance for {title}",
                    f"what should i know about {title} in ardupilot",
                    f"quick explanation of {title}",
                ]
            )
            rows.append(
                make_row(
                    prompt,
                    snippet_text[:500],
                    task_type="param_explanations",
                    category="official_docs",
                    source=f"docs:{path.name}",
                    weight=0.7,
                )
            )
    return rows


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_row(user_text: str, assistant_text: str, *, task_type: str, category: str, source: str, weight: float) -> Dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
        "task_type": task_type,
        "category": category,
        "source": source,
        "weight": weight,
    }


def write_jsonl(path: Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def split_rows(rows: List[Dict], train_ratio: float, validation_ratio: float) -> Dict[str, List[Dict]]:
    total = len(rows)
    train_end = int(total * train_ratio)
    validation_end = train_end + int(total * validation_ratio)
    return {
        "train": rows[:train_end],
        "validation": rows[train_end:validation_end],
        "heldout_eval": rows[validation_end:],
    }


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    params = load_parameters()
    grouped = group_params_by_topic(params)

    rows: List[Dict] = []
    rows.extend(build_tool_examples(rng))
    rows.extend(build_exact_param_examples(params, rng))
    rows.extend(build_search_examples(grouped, rng))
    rows.extend(build_radio_hard_cases(grouped))
    rows.extend(build_negative_examples())

    if args.include_docs:
        rows.extend(load_docs_rows(Path(args.docs_dir), rng))

    rng.shuffle(rows)
    splits = split_rows(rows, args.train_ratio, args.validation_ratio)
    output_dir = Path(args.output_dir)
    for split_name, split_rows_data in splits.items():
        write_jsonl(output_dir / f"{split_name}.jsonl", split_rows_data)

    manifest = {
        "total_rows": len(rows),
        "train_rows": len(splits["train"]),
        "validation_rows": len(splits["validation"]),
        "heldout_eval_rows": len(splits["heldout_eval"]),
        "include_docs": args.include_docs,
        "sources": sorted({row["source"] for row in rows}),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Built dataset at {output_dir}")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
