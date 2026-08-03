#!/usr/bin/env python3
"""Download, verify, and inventory the fixed JMdict packages used by JLPT Wisteria."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import shutil
import sys
import urllib.error
import urllib.request

RELEASE = "3.6.2+20260727141257"
BASE = "https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20260727141257"
FILES = {
    "common": {
        "filename": f"jmdict-eng-common-{RELEASE}.json.tgz",
        "sha256": "a7f9e1f6fd14ff361fa86fbeafa2261ee215c6ffff7e4b2625df26b7fba47173",
        "label": "JMdict English common",
        "examples": False,
    },
    "examples": {
        "filename": f"jmdict-examples-eng-{RELEASE}.json.tgz",
        "sha256": "508d41af24121624d69b2cf35aa9e5dc214a3272c529f688518c1025bf870f11",
        "label": "JMdict English with examples",
        "examples": True,
    },
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: pathlib.Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JLPT-Wisteria/4.1 (+https://github.com/open-spaced-repetition/ts-fsrs)",
            "Accept": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def verify_or_download(kind: str, spec: dict[str, object], output: pathlib.Path) -> dict[str, object]:
    filename = str(spec["filename"])
    expected = str(spec["sha256"])
    destination = output / filename
    url = f"{BASE}/{filename}"

    if destination.exists():
        actual = sha256(destination)
        if actual == expected:
            print(f"[{kind}] already verified: {destination} ({destination.stat().st_size:,} bytes)")
        else:
            print(f"[{kind}] removing invalid cached file: {destination} ({actual})")
            destination.unlink()

    if not destination.exists():
        print(f"[{kind}] downloading {url}")
        try:
            download(url, destination)
        except (OSError, urllib.error.URLError) as error:
            destination.unlink(missing_ok=True)
            raise RuntimeError(f"Download failed for {kind}: {error}") from error

    actual = sha256(destination)
    if actual != expected:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"SHA-256 mismatch for {kind}: {actual}")
    size = destination.stat().st_size
    if size <= 0:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded file is empty: {destination}")
    print(f"[{kind}] OK: {destination} ({size:,} bytes)")
    return {
        "label": spec["label"],
        "file": filename,
        "sha256": expected,
        "bytes": size,
        "examples": bool(spec["examples"]),
        "releaseUrl": url,
    }


def write_manifest(output: pathlib.Path) -> pathlib.Path:
    packages: dict[str, dict[str, object]] = {}
    for kind, spec in FILES.items():
        destination = output / str(spec["filename"])
        if not destination.is_file():
            continue
        actual = sha256(destination)
        expected = str(spec["sha256"])
        if actual != expected:
            raise RuntimeError(f"Cannot inventory unverified package {destination}: {actual}")
        packages[kind] = {
            "label": spec["label"],
            "file": spec["filename"],
            "sha256": expected,
            "bytes": destination.stat().st_size,
            "examples": bool(spec["examples"]),
            "releaseUrl": f"{BASE}/{spec['filename']}",
        }
    manifest = {
        "schema": 1,
        "release": RELEASE,
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "packages": packages,
    }
    path = output / "jmdict-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest written: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["common", "examples", "both"])
    parser.add_argument("--output", default="data")
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    selected = FILES if args.kind == "both" else {args.kind: FILES[args.kind]}

    try:
        for kind, spec in selected.items():
            verify_or_download(kind, spec, output)
        write_manifest(output)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
