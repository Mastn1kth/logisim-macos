#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import plistlib
import stat
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "Logisim.app"
PLIST = APP / "Contents" / "Info.plist"
LAUNCHER = APP / "Contents" / "MacOS" / "Logisim"
JAR = APP / "Contents" / "Resources" / "Java" / "logisim.jar"
RUNTIME_LOCK = ROOT / "packaging" / "runtime-lock.json"
EXPECTED_JAR_SHA256 = "362a78c12ad18c203fed868872c4a01cd9c12141379d92e892bbe2c37e627bc2"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


with PLIST.open("rb") as plist_file:
    metadata = plistlib.load(plist_file)

expected_metadata = {
    "CFBundleExecutable": "Logisim",
    "CFBundleIdentifier": "com.cburch.logisim",
    "CFBundleShortVersionString": "2.7.1",
    "LSMinimumSystemVersion": "10.8.0",
}
for key, expected_value in expected_metadata.items():
    if metadata.get(key) != expected_value:
        fail(f"{key} must be {expected_value!r}, got {metadata.get(key)!r}")

launcher_text = LAUNCHER.read_text(encoding="utf-8")
if not launcher_text.startswith("#!/bin/sh\n"):
    fail("launcher must use the portable /bin/sh interpreter")
if "screen " in launcher_text or "do shell script" in launcher_text:
    fail("launcher still contains the obsolete Automator/screen implementation")
if "Contents/runtime/Contents/Home/bin/java" not in launcher_text:
    fail("launcher does not prefer the embedded Java runtime")
if os.name != "nt" and not LAUNCHER.stat().st_mode & stat.S_IXUSR:
    fail("launcher is not executable")

with zipfile.ZipFile(JAR) as archive:
    if "com/cburch/logisim/Main.class" not in archive.namelist():
        fail("Logisim main class is missing from logisim.jar")
    main_class = archive.read("com/cburch/logisim/Main.class")
    class_major_version = int.from_bytes(main_class[6:8], "big")
    if class_major_version != 49:
        fail(f"unexpected Java class version: {class_major_version}")

jar_sha256 = hashlib.sha256(JAR.read_bytes()).hexdigest()
if jar_sha256 != EXPECTED_JAR_SHA256:
    fail(f"unexpected logisim.jar SHA-256: {jar_sha256}")

runtime_lock = json.loads(RUNTIME_LOCK.read_text(encoding="utf-8"))
for architecture in ("x64", "arm64"):
    runtime = runtime_lock["runtimes"][architecture]
    if len(runtime["sha256"]) != 64:
        fail(f"invalid runtime SHA-256 for {architecture}")
    allowed_sources = (
        "https://cdn.azul.com/zulu/bin/",
        "https://github.com/adoptium/temurin17-binaries/releases/download/",
    )
    if not runtime["url"].startswith(allowed_sources):
        fail(f"unexpected runtime source for {architecture}")

print("Package metadata, launcher, and Logisim JAR are valid.")
