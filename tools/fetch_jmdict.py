#!/usr/bin/env python3
"""Download and verify the fixed JMdict packages used by JLPT Wisteria."""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import sys
import urllib.error
import urllib.request

RELEASE = "3.6.2+20260727141257"
BASE = "https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20260727141257"
FILES = {
    "common": (
        f"jmdict-eng-common-{RELEASE}.json.tgz",
        "a7f9e1f6fd14ff361fa86fbeafa2261ee215c6ffff7e4b2625df26b7fba47173",
    ),
    "examples": (
        f"jmdict-examples-eng-{RELEASE}.json.tgz",
        "508d41af24121624d69b2cf35aa9e5dc214a3272c529f688518c1025bf870f11",
    ),
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
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["common", "examples", "both"])
    parser.add_argument("--output", default="data")
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    selected = FILES if args.kind == "both" else {args.kind: FILES[args.kind]}

    for kind, (filename, expected) in selected.items():
        destination = output / filename
        url = f"{BASE}/{filename}"

        if destination.exists() and sha256(destination) == expected:
            print(f"[{kind}] already verified: {destination} ({destination.stat().st_size:,} bytes)")
            continue

        destination.unlink(missing_ok=True)
        print(f"[{kind}] downloading {url}")
        try:
            download(url, destination)
        except (OSError, urllib.error.URLError) as error:
            destination.unlink(missing_ok=True)
            print(f"Download failed: {error}", file=sys.stderr)
            return 1

        actual = sha256(destination)
        if actual != expected:
            destination.unlink(missing_ok=True)
            print(f"SHA-256 mismatch: {actual}", file=sys.stderr)
            return 2
        print(f"[{kind}] OK: {destination} ({destination.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
