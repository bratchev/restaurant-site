#!/usr/bin/env python3
"""Scan known restaurant sources and write review candidates.

This is intentionally conservative. It finds likely article/page candidates and
assigns preliminary event scores. A human review step decides what becomes
public data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONFIG = ROOT / "tools" / "restaurant_sources.json"
OUTPUT = ROOT / "data-work" / "candidates.json"
PUBLIC_DATA = ROOT / "public" / "data" / "restaurants.json"

KEYWORDS = {
    "michelin_promotion": {
        "terms": ["three stars", "3 stars", "promoted", "promotion"],
        "signal": "Michelin promotion",
        "momentum": 5,
        "discovery": 1,
    },
    "new_michelin_star": {
        "terms": ["new star", "newly starred", "one star", "michelin star"],
        "signal": "New Michelin star",
        "momentum": 5,
        "discovery": 2,
    },
    "new_opening": {
        "terms": ["opens", "opened", "opening", "new restaurant", "new opening"],
        "signal": "New opening",
        "momentum": 4,
        "discovery": 4,
    },
    "popup_to_opening": {
        "terms": ["pop-up", "popup", "residency", "permanent"],
        "signal": "Pop-up to opening",
        "momentum": 3,
        "discovery": 5,
    },
    "expansion": {
        "terms": ["expands", "expansion", "larger space", "new location"],
        "signal": "Expansion",
        "momentum": 3,
        "discovery": 3,
    },
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def fetch_url(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ratchev-restaurant-scanner/0.1 (+https://ratchev.org)"
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_title(document: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", document, re.I | re.S)
    return normalize_space(match.group(1)) if match else ""


def extract_links(document: str, base_url: str) -> list[dict]:
    links = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", document, re.I | re.S):
        href = html.unescape(match.group(1))
        text = normalize_space(re.sub(r"<[^>]+>", " ", match.group(2)))
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urllib.parse.urljoin(base_url, href)
        if text:
            links.append({"title": text, "url": url})
    return links


def classify_event(text: str, source: dict) -> dict | None:
    lowered = text.lower()
    for rule in KEYWORDS.values():
        if any(term in lowered for term in rule["terms"]):
            discovery = min(rule["discovery"], int(source.get("defaultDiscovery", rule["discovery"])))
            return {
                "signal": rule["signal"],
                "momentum": rule["momentum"],
                "discovery": discovery,
                "confidence": int(source.get("confidence", 3)),
            }
    return None


def known_urls() -> set[str]:
    if not PUBLIC_DATA.exists():
      return set()
    data = load_json(PUBLIC_DATA)
    urls = {item.get("sourceUrl", "") for item in data.get("items", [])}
    for item in data.get("items", []):
        for event in item.get("events", []):
            urls.add(event.get("url", ""))
    return {url for url in urls if url}


def make_candidate(source: dict, title: str, url: str, scan_date: str) -> dict | None:
    event = classify_event(title, source)
    if event is None:
        return None

    name = title
    for separator in [" - ", " | ", ": "]:
        if separator in name:
            name = name.split(separator)[0]
            break

    return {
        "id": re.sub(r"[^a-z0-9]+", "-", f"{source['city']} {source['name']} {title}".lower()).strip("-")[:96],
        "status": "pending",
        "name": name[:90],
        "city": source["city"],
        "neighborhood": "",
        "summary": title,
        "whyItMatters": "",
        "event": {
            "type": event["signal"],
            "date": scan_date,
            "sourceName": source["name"],
            "url": url,
            "momentum": event["momentum"],
            "discovery": event["discovery"],
            "confidence": event["confidence"],
            "note": title,
        },
    }


def scan_source(source: dict, scan_date: str, seen_urls: set[str]) -> list[dict]:
    try:
        document = fetch_url(source["url"])
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"warn: could not fetch {source['name']}: {error}", file=sys.stderr)
        return []

    candidates = []
    page_title = extract_title(document)
    page_candidate = make_candidate(source, page_title, source["url"], scan_date) if page_title else None
    if page_candidate and source["url"] not in seen_urls:
        candidates.append(page_candidate)

    for link in extract_links(document, source["url"]):
        if link["url"] in seen_urls:
            continue
        candidate = make_candidate(source, link["title"], link["url"], scan_date)
        if candidate:
            candidates.append(candidate)

    unique = {}
    for candidate in candidates:
        unique[candidate["event"]["url"]] = candidate
    return list(unique.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=None, help="Lookback window for review metadata.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    config = load_json(SOURCE_CONFIG)
    weeks = args.weeks or int(config.get("defaultWeeks", 12))
    today = dt.date.today()
    scan = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "lookbackWeeks": weeks,
        "lookbackStart": (today - dt.timedelta(weeks=weeks)).isoformat(),
        "manualSources": [],
        "candidates": [],
    }

    seen_urls = known_urls()
    for source in config["sources"]:
        if source.get("scanMode") == "manual":
            scan["manualSources"].append({
                "city": source["city"],
                "name": source["name"],
                "url": source["url"],
                "reason": "Manual review source; automated fetch is skipped.",
            })
            print(f"manual: skipped {source['name']} ({source['url']})")
            continue
        scan["candidates"].extend(scan_source(source, today.isoformat(), seen_urls))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(scan['candidates'])} candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
