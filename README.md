# Logisim for macOS and Windows

**English | [Русский](README.ru.md)**

[![Build status](https://github.com/Mastn1kth/logisim-macos/actions/workflows/build.yml/badge.svg)](https://github.com/Mastn1kth/logisim-macos/actions/workflows/build.yml)
[![Latest release](https://img.shields.io/github/v/release/Mastn1kth/logisim-macos?display_name=tag)](https://github.com/Mastn1kth/logisim-macos/releases/latest)
[![GPL-3.0 license](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://github.com/logisim-evolution/logisim-evolution/blob/v5.0.0/LICENSE.md)

I put this repository together for classes and digital-logic lab work. The goal
is simple: download Logisim and start working without installing Java or sorting
through platform-specific runtime requirements.

The application is based on the official **Logisim-evolution 5.0.0** release.
The macOS app uses the shorter display name **Logisim**, and Russian localization
is included. I do not claim the simulator as my own work: this repository adds
packaging, repeatable verification, and convenient downloads.

## Download

Ready-to-use packages are available on the
**[Releases page](https://github.com/Mastn1kth/logisim-macos/releases/latest)**.

| Computer | Download | Separate Java install |
| --- | --- | --- |
| Mac with M1, M2, M3, M4, or M5 | `Logisim-5.0.0-macOS-Apple-Silicon.zip` | No |
| Older Intel Mac | `Logisim-5.0.0-macOS-Intel.zip` | No |
| Typical Intel/AMD Windows PC | `logisim-evolution-5.0.0-amd64.msi` | No |
| Portable Intel/AMD Windows build | `logisim-evolution-5.0.0-windows-amd64.zip` | No |
| Windows on ARM | `logisim-evolution-5.0.0-aarch64.msi` | No |
| Portable Windows on ARM build | `logisim-evolution-5.0.0-windows-aarch64.zip` | No |

Most Windows users want **`amd64.msi`**. Despite the name, AMD64 is the regular
64-bit architecture used by both Intel and AMD processors.

## What is included

- Logisim-evolution 5.0.0;
- a bundled Java runtime, so Java does not need to be installed separately;
- the Russian interface and built-in language selector;
- gates, memories, registers, TTL devices, and timing diagrams;
- FPGA and VHDL tools plus the extended Evolution component libraries;
- support for the `.circ` files commonly used in digital-logic courses.

The language selector is available under **Logisim → Preferences →
International → Language**. Opening Preferences selects the localization tab by
default.

## Installing on macOS

1. Check the processor under Apple menu → **About This Mac**.
2. Download the Apple Silicon or Intel ZIP.
3. Extract it and move `Logisim.app` to **Applications**.
4. On first launch, Control-click the app, choose **Open**, and confirm.

The downloadable apps are ad-hoc signed and verified with `codesign`, but they
are not notarized with a paid Apple Developer certificate. If macOS still blocks
the first launch, use **System Settings → Privacy & Security → Open Anyway**.

## Installing on Windows

For a regular installation, download and run `amd64.msi`. If software cannot be
installed on a lab computer, use the portable Windows ZIP, extract it to its own
folder, and run Logisim-evolution from there.

The Windows binaries are not modified. They are the official upstream
Logisim-evolution packages, verified against the SHA-256 digests published with
the release.

## Compatibility with coursework

Logisim-evolution opens many projects created by the original Logisim 2.7.1,
but upstream does not guarantee perfect backward compatibility. Keep the
original lab file untouched and save an Evolution copy under a new name. Avoid
Evolution-only components if the instructor will open the result in 2.7.1.

Build scripts for the original Logisim 2.7.1 remain available in this repository
for courses that explicitly require the legacy version.

## How the packages are verified

GitHub Actions builds and launches the app on real Intel and Apple Silicon macOS
runners. The workflow also checks:

- the extracted application and reported Logisim version;
- ad-hoc code signatures;
- ZIP and JAR integrity;
- executable permissions;
- the architecture and minimum macOS version of every bundled Mach-O file;
- pinned sizes and SHA-256 checksums for downloaded runtimes and resources.

The pinned sources are recorded in `packaging/evolution-lock.json`. Rebuild the
macOS archives with:

```sh
python scripts/build-modern-logisim.py --arch all
```

Download and verify the official Windows packages with:

```sh
python scripts/download-windows-packages.py
```

## Project status and attribution

This is an independent packaging project, not the official Logisim-evolution
website. The simulator is maintained by the
[Logisim-evolution developers](https://github.com/logisim-evolution/logisim-evolution)
and distributed under GPL-3.0.

Packaging and this repository are maintained by
[@Mastn1kth](https://github.com/Mastn1kth). Thanks to Carl Burch for the original
Logisim and to every Logisim-evolution contributor who continues to improve it.

If a package fails, please
**[open an issue](https://github.com/Mastn1kth/logisim-macos/issues/new)** and
include the computer model, operating-system version, and exact error message.
