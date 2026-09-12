#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
DIST = ROOT / "dist"
CACHE = DIST / "cache"
LOCK_PATH = ROOT / "packaging" / "evolution-lock.json"
BUFFER_SIZE = 1024 * 1024
CPU_TYPES = {"x64": 0x01000007, "arm64": 0x0100000C}
LC_VERSION_MIN_MACOSX = 0x24
LC_BUILD_VERSION = 0x32
ZIP_TIMESTAMP = (2026, 9, 12, 5, 36, 54)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def cached_download(config: dict[str, object], filename: str | None = None) -> Path:
    url = str(config["url"])
    expected_size = int(config["size"])
    expected_hash = str(config["sha256"])
    destination = CACHE / (filename or PurePosixPath(url).name)
    CACHE.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        if destination.stat().st_size == expected_size and sha256(destination) == expected_hash:
            print(f"Using verified cache: {destination.name}")
            return destination
        destination.unlink()

    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "logisim-macos-builder/5.0.0"})
    digest = hashlib.sha256()
    received = 0
    print(f"Downloading {url}")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            while chunk := response.read(BUFFER_SIZE):
                output.write(chunk)
                digest.update(chunk)
                received += len(chunk)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    if received != expected_size:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"download size mismatch for {url}: {received} != {expected_size}")
    if digest.hexdigest() != expected_hash:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"download SHA-256 mismatch for {url}")
    os.replace(temporary, destination)
    return destination


def zip_info(name: str, mode: int, file_type: int = stat.S_IFREG) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (file_type | mode) << 16
    return info


def plist_bytes(version: str, minimum_macos: str) -> bytes:
    metadata = {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": "Logisim",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeExtensions": ["circ"],
                "CFBundleTypeIconFile": "LogisimDoc.icns",
                "CFBundleTypeName": "Logisim circuit",
                "CFBundleTypeRole": "Editor",
                "LSHandlerRank": "Owner",
            }
        ],
        "CFBundleExecutable": "Logisim",
        "CFBundleIconFile": "Logisim.icns",
        "CFBundleIdentifier": "org.logisim-evolution.Logisim",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": "Logisim",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "LSMinimumSystemVersion": minimum_macos,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": (
            "Copyright ©2001–2026 Logisim-evolution developers; custom macOS packaging"
        ),
    }
    return plistlib.dumps(metadata, sort_keys=False)


def launcher_bytes(version: str) -> bytes:
    return f'''#!/bin/sh

APP_ROOT=$(CDPATH= cd "$(dirname "$0")/../.." && pwd)
JAVA="$APP_ROOT/Contents/runtime/Contents/Home/bin/java"
JAR="$APP_ROOT/Contents/Resources/Java/logisim-evolution-{version}-all.jar"
ICON="$APP_ROOT/Contents/Resources/Logisim.icns"

if [ ! -x "$JAVA" ]; then
    osascript -e 'display alert "Logisim" message "Встроенная Java повреждена. Переустановите приложение." as critical' 2>/dev/null || true
    exit 1
fi

exec "$JAVA" \\
    --enable-native-access=ALL-UNNAMED \\
    -Dapple.laf.useScreenMenuBar=true \\
    -Dapple.awt.application.name=Logisim \\
    -Dcom.apple.mrj.application.apple.menu.about.name=Logisim \\
    -Xdock:name=Logisim \\
    "-Xdock:icon=$ICON" \\
    -jar "$JAR" "$@"
'''.encode("utf-8")


def runtime_root_and_java(runtime: tarfile.TarFile) -> tuple[PurePosixPath, tarfile.TarInfo]:
    matches = []
    for member in runtime.getmembers():
        path = PurePosixPath(member.name)
        if path.parts[-4:] == ("Contents", "Home", "bin", "java"):
            matches.append((PurePosixPath(*path.parts[:-4]), member))
    if len(matches) != 1:
        raise RuntimeError(f"expected one macOS Java executable, found {len(matches)}")
    return matches[0]


def add_runtime(archive: zipfile.ZipFile, runtime_path: Path, arch: str) -> int:
    symlinks = 0
    with tarfile.open(runtime_path, "r:gz") as runtime:
        root, java_member = runtime_root_and_java(runtime)
        java_stream = runtime.extractfile(java_member)
        if java_stream is None:
            raise RuntimeError("could not read the Java executable")
        header = java_stream.read(8)
        if header[:4] != b"\xcf\xfa\xed\xfe":
            raise RuntimeError("Java executable is not a little-endian 64-bit Mach-O file")
        if int.from_bytes(header[4:8], "little") != CPU_TYPES[arch]:
            raise RuntimeError(f"runtime architecture does not match {arch}")

        for member in runtime.getmembers():
            path = PurePosixPath(member.name)
            try:
                relative = path.relative_to(root)
            except ValueError:
                continue
            if not relative.parts or member.isdir():
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe path in runtime archive: {member.name}")
            target = (PurePosixPath("Logisim.app/Contents/runtime") / relative).as_posix()
            if member.issym():
                link_target = PurePosixPath(member.linkname)
                if link_target.is_absolute() or ".." in link_target.parts:
                    raise RuntimeError(f"unsafe runtime symlink: {member.name}")
                archive.writestr(
                    zip_info(target, 0o777, stat.S_IFLNK), member.linkname.encode("utf-8")
                )
                symlinks += 1
            elif member.isfile() or member.islnk():
                source = runtime.extractfile(member)
                if source is None:
                    raise RuntimeError(f"could not read runtime member: {member.name}")
                archive.writestr(zip_info(target, member.mode), source.read())
    return symlinks


def decoded_version(version: int) -> tuple[int, int, int]:
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
            minimum = decoded_version(struct.unpack_from("<I", commands, offset + 8)[0])
        elif command == LC_BUILD_VERSION:
            platform, version = struct.unpack_from("<2I", commands, offset + 8)
            if platform == 1:
                minimum = decoded_version(version)
        offset += size
    return cpu_type, minimum


def validate(output: Path, arch: str, version: str, minimum_macos: str, jar_hash: str) -> None:
    configured_minimum = tuple(int(part) for part in minimum_macos.split("."))
    maximum_minimum = (0, 0, 0)
    macho_count = 0
    with zipfile.ZipFile(output) as archive:
        bad_entry = archive.testzip()
        if bad_entry:
            raise RuntimeError(f"corrupt ZIP entry: {bad_entry}")
        prefix = "Logisim.app/Contents/"
        plist = plistlib.loads(archive.read(prefix + "Info.plist"))
        if plist.get("CFBundleDisplayName") != "Logisim":
            raise RuntimeError("application display name is not Logisim")
        if plist.get("CFBundleShortVersionString") != version:
            raise RuntimeError("application version does not match the lock file")
        launcher = archive.getinfo(prefix + "MacOS/Logisim")
        java = archive.getinfo(prefix + "runtime/Contents/Home/bin/java")
        for item in (launcher, java):
            if ((item.external_attr >> 16) & 0o111) == 0:
                raise RuntimeError(f"executable permission is missing: {item.filename}")
        jar_name = prefix + f"Resources/Java/logisim-evolution-{version}-all.jar"
        if hashlib.sha256(archive.read(jar_name)).hexdigest() != jar_hash:
            raise RuntimeError("packaged Logisim JAR checksum mismatch")
        with zipfile.ZipFile(Path(CACHE / f"logisim-evolution-{version}-all.jar")) as jar:
            if "resources/logisim/strings/gui/gui_ru.properties" not in jar.namelist():
                raise RuntimeError("Russian GUI localization is missing from the upstream JAR")

        for entry in archive.infolist():
            if not entry.filename.startswith(prefix + "runtime/"):
                continue
            with archive.open(entry) as source:
                metadata = macho_metadata(source)
            if metadata is None:
                continue
            cpu_type, native_minimum = metadata
            macho_count += 1
            if cpu_type != CPU_TYPES[arch]:
                raise RuntimeError(f"wrong architecture in {entry.filename}")
            if native_minimum and native_minimum > maximum_minimum:
                maximum_minimum = native_minimum
    if macho_count == 0:
        raise RuntimeError("no Mach-O binaries found in the embedded runtime")
    if maximum_minimum > configured_minimum:
        raise RuntimeError(
            f"runtime needs macOS {maximum_minimum}, package declares {configured_minimum}"
        )
    print(
        f"Verified {macho_count} {arch} Mach-O files; highest native minimum is "
        f"{'.'.join(map(str, maximum_minimum))}"
    )


def build(arch: str, lock: dict[str, object]) -> Path:
    product = lock["product"]
    version = str(product["version"])
    jar_config = lock["jar"]
    runtime_config = lock["runtimes"][arch]
    assets = lock["assets"]
    jar = cached_download(jar_config, f"logisim-evolution-{version}-all.jar")
    runtime = cached_download(runtime_config)
    app_icon = cached_download(assets["app_icon"], f"Logisim-{version}.icns")
    document_icon = cached_download(assets["document_icon"], f"LogisimDoc-{version}.icns")
    license_file = cached_download(assets["license"], f"Logisim-evolution-LICENSE-{version}.md")
    minimum_macos = str(runtime_config["macos_minimum"])
    display_arch = str(runtime_config["display_name"])
    output = DIST / f"Logisim-{version}-macOS-{display_arch}.zip"
    temporary = output.with_suffix(".zip.tmp")
    temporary.unlink(missing_ok=True)

    provenance = {
        "application": "Logisim-evolution",
        "application_version": version,
        "custom_display_name": "Logisim",
        "release_url": product["release_url"],
        "runtime_architecture": arch,
        "runtime_java_version": runtime_config["java_version"],
        "runtime_license": lock["runtime_license"],
        "runtime_sha256": runtime_config["sha256"],
        "runtime_url": runtime_config["url"],
        "runtime_vendor": runtime_config["vendor"],
    }
    prefix = PurePosixPath("Logisim.app/Contents")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(zip_info((prefix / "Info.plist").as_posix(), 0o644), plist_bytes(version, minimum_macos))
        archive.writestr(zip_info((prefix / "MacOS/Logisim").as_posix(), 0o755), launcher_bytes(version))
        archive.writestr(zip_info((prefix / "Resources/Logisim.icns").as_posix(), 0o644), app_icon.read_bytes())
        archive.writestr(zip_info((prefix / "Resources/LogisimDoc.icns").as_posix(), 0o644), document_icon.read_bytes())
        archive.writestr(
            zip_info((prefix / f"Resources/Java/logisim-evolution-{version}-all.jar").as_posix(), 0o644),
            jar.read_bytes(),
        )
        archive.writestr(zip_info((prefix / "Resources/LICENSE.md").as_posix(), 0o644), license_file.read_bytes())
        archive.writestr(
            zip_info((prefix / "Resources/build-source.json").as_posix(), 0o644),
            (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        symlink_count = add_runtime(archive, runtime, arch)

    os.replace(temporary, output)
    validate(output, arch, version, minimum_macos, str(jar_config["sha256"]))
    print(f"Created {output} ({output.stat().st_size} bytes, {symlink_count} symlinks)")
    print(f"SHA-256: {sha256(output)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package current Logisim-evolution as Logisim.app with an embedded Java 21 runtime"
    )
    parser.add_argument("--arch", choices=("x64", "arm64", "all"), default="all")
    args = parser.parse_args()
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    architectures = tuple(lock["runtimes"]) if args.arch == "all" else (args.arch,)
    for arch in architectures:
        build(arch, lock)


if __name__ == "__main__":
    main()
