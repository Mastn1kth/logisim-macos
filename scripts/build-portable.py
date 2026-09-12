#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "Logisim.app"
OUTPUT = ROOT / "dist" / "Logisim-2.7.1-system-java.zip"
LAUNCHER = Path("Logisim.app/Contents/MacOS/Logisim")


def zip_info(path: Path, archive_name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo.from_file(path, archive_name)
    info.create_system = 3
    permissions = 0o755 if Path(archive_name) == LAUNCHER else 0o644
    info.external_attr = (stat.S_IFREG | permissions) << 16
    return info


OUTPUT.parent.mkdir(parents=True, exist_ok=True)
temporary_output = OUTPUT.with_suffix(".zip.tmp")

with zipfile.ZipFile(
    temporary_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
) as archive:
    for source in sorted(path for path in APP.rglob("*") if path.is_file()):
        archive_name = (Path("Logisim.app") / source.relative_to(APP)).as_posix()
        archive.writestr(zip_info(source, archive_name), source.read_bytes())

os.replace(temporary_output, OUTPUT)
print(f"Created {OUTPUT}")
