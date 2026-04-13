#!/usr/bin/env python3
"""
Fetch a small curated slice of official ArduPilot docs and store distilled snippets.

This script is optional. It writes JSON files under training/data/raw_docs/.
"""

from __future__ import annotations

import argparse
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import List
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
RAW_DOCS_DIR = ROOT / "data" / "raw_docs"

DOCS = [
    ("parameters-overview", "https://ardupilot.org/copter/docs/parameters.html"),
    ("radio-control", "https://ardupilot.org/copter/docs/common-radio-control-calibration.html"),
    ("failsafe", "https://ardupilot.org/copter/docs/failsafe-landing-page.html"),
    ("battery-failsafe", "https://ardupilot.org/copter/docs/failsafe-battery.html"),
    ("gps", "https://ardupilot.org/copter/docs/common-gps-for-pixhawk.html"),
    ("loiter-mode", "https://ardupilot.org/copter/docs/loiter-mode.html"),
    ("rtl-mode", "https://ardupilot.org/copter/docs/rtl-mode.html"),
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch curated official ArduPilot docs.")
    parser.add_argument("--output-dir", default=str(RAW_DOCS_DIR))
    return parser.parse_args()


def clean_html(html: str) -> List[str]:
    extractor = TextExtractor()
    extractor.feed(html)
    text = unescape(extractor.text())
    text = re.sub(r"\s+", " ", text).strip()
    chunks = re.split(r"(?<=[.!?])\s+", text)
    snippets: List[str] = []
    current = []
    current_len = 0
    for chunk in chunks:
        if not chunk:
            continue
        current.append(chunk)
        current_len += len(chunk)
        if current_len >= 350:
            snippets.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        snippets.append(" ".join(current))
    return snippets[:25]


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 ArduPilot-AI-Training/1.0"})
    with urlopen(req, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for slug, url in DOCS:
        html = fetch(url)
        snippets = clean_html(html)
        payload = {"slug": slug, "url": url, "title": slug.replace("-", " "), "snippets": snippets}
        (out_dir / f"{slug}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved {slug} ({len(snippets)} snippets)")


if __name__ == "__main__":
    main()
