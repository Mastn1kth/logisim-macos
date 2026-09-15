#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "windows"
LOCK = ROOT / "packaging" / "evolution-lock.json"
BUFFER_SIZE = 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def download(config: dict[str, object]) -> Path:
    destination = DIST / str(config["filename"])
    expected_size = int(config["size"])
    expected_hash = str(config["sha256"])
    if destination.exists():
        if destination.stat().st_size == expected_size and sha256(destination) == expected_hash:
            print(f"Verified cache: {destination.name}")
            return destination
        destination.unlink()

    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(
        str(config["url"]), headers={"User-Agent": "logisim-macos-builder/5.0.0"}
    )
    digest = hashlib.sha256()
    received = 0
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            while chunk := response.read(BUFFER_SIZE):
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    if received != expected_size or digest.hexdigest() != expected_hash:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"upstream verification failed: {destination.name}")
    os.replace(temporary, destination)
    print(f"Downloaded and verified: {destination.name}")
    return destination


def main() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    packages = tuple(lock["windows_packages"].values())
    DIST.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(packages)) as executor:
        files = tuple(executor.map(download, packages))
    for file in sorted(files):
        print(f"{sha256(file)}  {file.name}")


if __name__ == "__main__":
    main()
