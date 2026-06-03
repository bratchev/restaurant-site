#!/usr/bin/env python3
"""Append a manually found restaurant candidate to approved-candidates.json."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data-work" / "approved-candidates.json"

EVENT_DEFAULTS = {
    "New opening": {"momentum": 4, "discovery": 4, "confidence": 4},
    "New Michelin star": {"momentum": 5, "discovery": 2, "confidence": 5},
    "Michelin promotion": {"momentum": 5, "discovery": 1, "confidence": 5},
    "Bib Gourmand": {"momentum": 4, "discovery": 3, "confidence": 5},
    "Green Star": {"momentum": 4, "discovery": 3, "confidence": 5},
    "Pop-up to opening": {"momentum": 3, "discovery": 5, "confidence": 3},
    "Expansion": {"momentum": 3, "discovery": 3, "confidence": 3},
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def load_or_empty(path: Path) -> dict:
    if not path.exists():
        return {
            "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "candidates": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--why", required=True)
    parser.add_argument("--event-type", default="New opening", choices=sorted(EVENT_DEFAULTS))
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--neighborhood", default="")
    parser.add_argument("--source-name", default="Falstaff")
    parser.add_argument("--momentum", type=int)
    parser.add_argument("--discovery", type=int)
    parser.add_argument("--confidence", type=int)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    defaults = EVENT_DEFAULTS[args.event_type]
    candidate = {
        "id": slug(f"{args.city}-{args.source_name}-{args.name}-{args.event_type}"),
        "status": "approved",
        "name": args.name,
        "city": args.city,
        "neighborhood": args.neighborhood,
        "summary": args.summary,
        "whyItMatters": args.why,
        "event": {
            "type": args.event_type,
            "date": args.date,
            "sourceName": args.source_name,
            "url": args.url,
            "momentum": args.momentum or defaults["momentum"],
            "discovery": args.discovery or defaults["discovery"],
            "confidence": args.confidence or defaults["confidence"],
            "note": args.summary,
        },
    }

    data = load_or_empty(args.output)
    existing_ids = {item.get("id") for item in data.get("candidates", [])}
    if candidate["id"] in existing_ids:
        raise SystemExit(f"Candidate already exists: {candidate['id']}")

    data.setdefault("candidates", []).append(candidate)
    write_json(args.output, data)
    print(f"Added approved candidate: {candidate['name']} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
