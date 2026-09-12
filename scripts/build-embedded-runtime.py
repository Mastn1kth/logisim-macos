#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import plistlib
import stat
import struct
import tarfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "Logisim.app"
DIST = ROOT / "dist"
CACHE = DIST / "cache"
LOCK_PATH = ROOT / "packaging" / "runtime-lock.json"
BUFFER_SIZE = 1024 * 1024
CPU_TYPES = {"x64": 0x01000007, "arm64": 0x0100000C}
LC_VERSION_MIN_MACOSX = 0x24
LC_BUILD_VERSION = 0x32


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def download_runtime(config: dict[str, object]) -> Path:
    url = str(config["url"])
    expected_hash = str(config["sha256"])
    expected_size = int(config["size"])
    archive_path = CACHE / PurePosixPath(url).name

    if archive_path.exists():
        if archive_path.stat().st_size == expected_size and file_sha256(archive_path) == expected_hash:
            print(f"Using verified cache: {archive_path.name}")
            return archive_path
        archive_path.unlink()

    CACHE.mkdir(parents=True, exist_ok=True)
    temporary_path = archive_path.with_suffix(archive_path.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "logisim-macos-builder/2.7.1"})
    digest = hashlib.sha256()
    received = 0
    print(f"Downloading {url}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary_path.open("wb") as output:
            while chunk := response.read(BUFFER_SIZE):
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise

    if received != expected_size:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"runtime size mismatch: expected {expected_size}, received {received}")
    if digest.hexdigest() != expected_hash:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError("runtime SHA-256 mismatch")

    os.replace(temporary_path, archive_path)
    return archive_path


def zip_info(name: str, mode: int, mtime: float, file_type: int = stat.S_IFREG) -> zipfile.ZipInfo:
    earliest_zip_time = datetime.datetime(1980, 1, 1)
    modified = max(datetime.datetime.fromtimestamp(mtime), earliest_zip_time)
    info = zipfile.ZipInfo(name, modified.timetuple()[:6])
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (file_type | mode) << 16
    return info


def add_application(archive: zipfile.ZipFile, minimum_macos: str) -> None:
    for source in sorted(path for path in APP.rglob("*") if path.is_file()):
        relative = source.relative_to(APP)
        if relative.parts and relative.parts[0] == "runtime":
            continue
        archive_name = (PurePosixPath("Logisim.app") / PurePosixPath(relative.as_posix())).as_posix()
        data = source.read_bytes()
        if relative.as_posix() == "Contents/Info.plist":
            metadata = plistlib.loads(data)
            metadata["LSMinimumSystemVersion"] = minimum_macos
            data = plistlib.dumps(metadata, sort_keys=False)
        mode = 0o755 if relative.as_posix() == "Contents/MacOS/Logisim" else 0o644
        archive.writestr(zip_info(archive_name, mode, source.stat().st_mtime), data)


def runtime_root_and_java(runtime: tarfile.TarFile) -> tuple[PurePosixPath, tarfile.TarInfo]:
    matches = []
    for member in runtime.getmembers():
        path = PurePosixPath(member.name)
        if path.parts[-4:] == ("Contents", "Home", "bin", "java"):
            matches.append((PurePosixPath(*path.parts[:-4]), member))
    if len(matches) != 1:
        raise RuntimeError(f"expected one macOS Java executable, found {len(matches)}")
    return matches[0]


def validate_java_architecture(runtime: tarfile.TarFile, java_member: tarfile.TarInfo, arch: str) -> None:
    java_stream = runtime.extractfile(java_member)
    if java_stream is None:
        raise RuntimeError("could not read the Java executable")
    header = java_stream.read(8)
    if header[:4] != b"\xcf\xfa\xed\xfe":
        raise RuntimeError("Java executable is not a 64-bit little-endian Mach-O file")
    cpu_type = int.from_bytes(header[4:8], "little")
    if cpu_type != CPU_TYPES[arch]:
        raise RuntimeError(f"runtime architecture mismatch for {arch}: CPU type {cpu_type:#x}")


def add_runtime(archive: zipfile.ZipFile, runtime_path: Path, arch: str) -> int:
    symlink_count = 0
    with tarfile.open(runtime_path, "r:gz") as runtime:
        root, java_member = runtime_root_and_java(runtime)
        validate_java_architecture(runtime, java_member, arch)

        for member in runtime.getmembers():
            member_path = PurePosixPath(member.name)
            try:
                relative = member_path.relative_to(root)
            except ValueError:
                continue
            if not relative.parts or member.isdir():
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe runtime path: {member.name}")

            archive_name = (
                PurePosixPath("Logisim.app/Contents/runtime") / relative
            ).as_posix()
            if member.issym():
                link_target = PurePosixPath(member.linkname)
                if link_target.is_absolute():
                    raise RuntimeError(f"absolute runtime symlink: {member.name}")
                archive.writestr(
                    zip_info(archive_name, 0o777, member.mtime, stat.S_IFLNK),
                    member.linkname.encode("utf-8"),
                )
                symlink_count += 1
            elif member.isfile() or member.islnk():
                source = runtime.extractfile(member)
                if source is None:
                    raise RuntimeError(f"could not read runtime member: {member.name}")
                archive.writestr(zip_info(archive_name, member.mode, member.mtime), source.read())
    return symlink_count


def encoded_macos_version(version: int) -> tuple[int, int, int]:
    return version >> 16, (version >> 8) & 0xFF, version & 0xFF


def macho_metadata(source: zipfile.ZipExtFile) -> tuple[int, tuple[int, int, int] | None] | None:
    header = source.read(32)
    if header[:4] != b"\xcf\xfa\xed\xfe":
        return None
    _, cpu_type, _, _, command_count, command_size, _, _ = struct.unpack("<8I", header)
    commands = source.read(command_size)
    offset = 0
    minimum = None
    for _ in range(command_count):
        command, size = struct.unpack_from("<2I", commands, offset)
        if size < 8 or offset + size > len(commands):
            raise RuntimeError("invalid Mach-O load command")
        if command == LC_VERSION_MIN_MACOSX:
            minimum = encoded_macos_version(struct.unpack_from("<I", commands, offset + 8)[0])
        elif command == LC_BUILD_VERSION:
            platform, version = struct.unpack_from("<2I", commands, offset + 8)
            if platform == 1:
                minimum = encoded_macos_version(version)
        offset += size
    return cpu_type, minimum


def validate_output(output: Path, arch: str, configured_minimum: str) -> None:
    configured_version = tuple(int(part) for part in configured_minimum.split("."))
    maximum_native_minimum = (0, 0, 0)
    maximum_minimum_entries: list[str] = []
    macho_count = 0
    with zipfile.ZipFile(output) as archive:
        bad_entry = archive.testzip()
        if bad_entry is not None:
            raise RuntimeError(f"corrupt output archive entry: {bad_entry}")
        java_entry = archive.getinfo("Logisim.app/Contents/runtime/Contents/Home/bin/java")
        if ((java_entry.external_attr >> 16) & 0o777) & 0o111 == 0:
            raise RuntimeError("embedded Java executable lost its execute permission")
        for entry in archive.infolist():
            if not entry.filename.startswith("Logisim.app/Contents/runtime/"):
                continue
            with archive.open(entry) as source:
                metadata = macho_metadata(source)
            if metadata is None:
                continue
            cpu_type, minimum = metadata
            macho_count += 1
            if cpu_type != CPU_TYPES[arch]:
                raise RuntimeError(f"wrong Mach-O architecture in {entry.filename}")
            if minimum is not None:
                if minimum > maximum_native_minimum:
                    maximum_native_minimum = minimum
                    maximum_minimum_entries = [entry.filename]
                elif minimum == maximum_native_minimum:
                    maximum_minimum_entries.append(entry.filename)
    if macho_count == 0:
        raise RuntimeError("no Mach-O files found in embedded runtime")
    if maximum_native_minimum > configured_version:
        raise RuntimeError(
            f"native runtime needs macOS {maximum_native_minimum}, "
            f"but package declares {configured_version}; "
            f"highest requirement found in {maximum_minimum_entries[:5]}"
        )
    print(
        f"Verified {macho_count} {arch} Mach-O files; "
        f"highest native minimum is {'.'.join(map(str, maximum_native_minimum))}"
    )


def build(arch: str, lock: dict[str, object]) -> Path:
    runtime_config = lock["runtimes"][arch]
    runtime_path = download_runtime(runtime_config)
    output = DIST / f"Logisim-2.7.1-bundled-jre-{arch}.zip"
    temporary_output = output.with_suffix(".zip.tmp")
    provenance = {
        "runtime_architecture": arch,
        "runtime_java_version": runtime_config["java_version"],
        "runtime_license": lock["license"],
        "runtime_sha256": runtime_config["sha256"],
        "runtime_url": runtime_config["url"],
        "runtime_vendor": runtime_config["vendor"],
    }

    with zipfile.ZipFile(
        temporary_output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        add_application(archive, str(runtime_config["macos_minimum"]))
        symlink_count = add_runtime(archive, runtime_path, arch)
        provenance_name = "Logisim.app/Contents/runtime-source.json"
        archive.writestr(
            zip_info(provenance_name, 0o644, LOCK_PATH.stat().st_mtime),
            (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )

    os.replace(temporary_output, output)
    validate_output(output, arch, str(runtime_config["macos_minimum"]))
    print(f"Created {output} ({output.stat().st_size} bytes, {symlink_count} symlinks)")
    print(f"SHA-256: {file_sha256(output)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Logisim macOS ZIPs with an embedded JRE")
    parser.add_argument("--arch", choices=("x64", "arm64", "all"), default="all")
    args = parser.parse_args()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    architectures = tuple(lock["runtimes"]) if args.arch == "all" else (args.arch,)
    for arch in architectures:
        build(arch, lock)


if __name__ == "__main__":
    main()
