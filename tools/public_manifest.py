#!/usr/bin/env python3
"""Create or verify a preservation manifest for the static public site."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ROOT = ROOT / "public"
DEFAULT_MANIFEST = ROOT / "docs" / "public-preservation-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def extension(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return suffix[1:] if suffix else "[none]"


def iter_public_files() -> list[Path]:
    return sorted(path for path in PUBLIC_ROOT.rglob("*") if path.is_file())


def build_manifest() -> dict:
    files = []
    by_extension: Counter[str] = Counter()
    total_bytes = 0

    for path in iter_public_files():
        rel = relative(path)
        size = path.stat().st_size
        total_bytes += size
        by_extension[extension(rel)] += 1
        files.append(
            {
                "path": rel,
                "size": size,
                "sha256": sha256(path),
            }
        )

    return {
        "schema": 1,
        "root": "public",
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "summary": {
            "files": len(files),
            "bytes": total_bytes,
            "byExtension": dict(sorted(by_extension.items())),
            "preservationCritical": [
                "public/ourphotos/",
                "public/applets/",
                "public/index_files/",
            ],
        },
        "files": files,
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_manifest(manifest_path: Path) -> int:
    expected = load_json(manifest_path)
    actual = build_manifest()

    expected_files = {item["path"]: item for item in expected.get("files", [])}
    actual_files = {item["path"]: item for item in actual.get("files", [])}

    missing = sorted(set(expected_files) - set(actual_files))
    extra = sorted(set(actual_files) - set(expected_files))
    changed = []

    for path in sorted(set(expected_files) & set(actual_files)):
        old = expected_files[path]
        new = actual_files[path]
        if old["size"] != new["size"] or old["sha256"] != new["sha256"]:
            changed.append(path)

    print(f"Manifest: {manifest_path}")
    print(f"Expected files: {len(expected_files)}")
    print(f"Actual files: {len(actual_files)}")
    print(f"Missing: {len(missing)}")
    print(f"Changed: {len(changed)}")
    print(f"Extra: {len(extra)}")

    for label, paths in [("missing", missing), ("changed", changed), ("extra", extra)]:
        if paths:
            print(f"\nFirst {label} paths:")
            for path in paths[:25]:
                print(f"  {path}")
            if len(paths) > 25:
                print(f"  ... {len(paths) - 25} more")

    return 1 if missing or changed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["write", "check"],
        help="Write a new manifest or check current public files against one.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    if args.command == "write":
        manifest = build_manifest()
        write_json(args.manifest, manifest)
        print(
            f"Wrote {manifest['summary']['files']} files "
            f"({manifest['summary']['bytes']} bytes) to {args.manifest}"
        )
        return 0

    return check_manifest(args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
