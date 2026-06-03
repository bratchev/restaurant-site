#!/usr/bin/env python3
"""Merge approved restaurant candidates into public/data/restaurants.json."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APPROVED = ROOT / "data-work" / "approved-candidates.json"
PUBLIC_DATA = ROOT / "public" / "data" / "restaurants.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def average_score(events: list[dict], key: str, fallback: int = 3) -> int:
    values = [int(event.get(key, fallback)) for event in events if event.get(key) is not None]
    if not values:
        return fallback
    return round(sum(values) / len(values))


def candidate_to_item(candidate: dict) -> dict:
    event = candidate["event"]
    events = [event]
    scores = {
        "momentum": average_score(events, "momentum"),
        "discovery": average_score(events, "discovery"),
        "confidence": average_score(events, "confidence"),
    }

    return {
        "name": candidate["name"],
        "city": candidate["city"],
        "neighborhood": candidate.get("neighborhood", ""),
        "signal": event["type"],
        "signalStrength": scores["momentum"],
        "signalDate": event["date"],
        "summary": candidate.get("summary", ""),
        "whyItMatters": candidate.get("whyItMatters", ""),
        "sourceName": event["sourceName"],
        "sourceUrl": event["url"],
        "scores": scores,
        "events": events,
    }


def merge_item(existing: dict, incoming: dict) -> dict:
    existing_events = existing.get("events", [])
    event_urls = {event.get("url") for event in existing_events}
    for event in incoming.get("events", []):
        if event.get("url") not in event_urls:
            existing_events.append(event)

    existing["events"] = existing_events
    existing["scores"] = {
        "momentum": average_score(existing_events, "momentum", existing.get("signalStrength", 3)),
        "discovery": average_score(existing_events, "discovery"),
        "confidence": average_score(existing_events, "confidence"),
    }
    existing["signalStrength"] = existing["scores"]["momentum"]

    if incoming.get("signalDate", "") > existing.get("signalDate", ""):
        for key in ["signal", "signalDate", "summary", "whyItMatters", "sourceName", "sourceUrl"]:
            existing[key] = incoming.get(key, existing.get(key, ""))

    return existing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved", type=Path, default=DEFAULT_APPROVED)
    parser.add_argument("--data", type=Path, default=PUBLIC_DATA)
    args = parser.parse_args()

    approved = load_json(args.approved)
    public = load_json(args.data)
    items = public.setdefault("items", [])

    by_key = {slug(f"{item.get('city', '')}-{item.get('name', '')}"): item for item in items}
    merged_count = 0
    added_count = 0

    for candidate in approved.get("candidates", []):
        if candidate.get("status") not in (None, "approved"):
            continue
        incoming = candidate_to_item(candidate)
        key = slug(f"{incoming['city']}-{incoming['name']}")
        if key in by_key:
            merge_item(by_key[key], incoming)
            merged_count += 1
        else:
            items.append(incoming)
            by_key[key] = incoming
            added_count += 1

        if incoming["city"] not in public.setdefault("cities", []):
            public["cities"].append(incoming["city"])

    public["cities"] = sorted(public.get("cities", []))
    public["items"] = sorted(
        items,
        key=lambda item: (
            -int(item.get("scores", {}).get("momentum", item.get("signalStrength", 0))),
            item.get("city", ""),
            item.get("name", ""),
        ),
    )
    public["updated"] = dt.date.today().isoformat()

    write_json(args.data, public)
    print(f"Added {added_count}, merged {merged_count}, wrote {args.data}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
