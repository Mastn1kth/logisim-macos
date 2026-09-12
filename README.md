# Logisim 2.7.1 for macOS

This repository packages the original Logisim 2.7.1 application for a wide range
of Macs. The Logisim Java application itself is unchanged.

## Current Logisim for lab work

The repository can also package the current Logisim-evolution 5.0.0 application
under the shorter macOS display name `Logisim`. These packages include a Java 21
runtime and retain the upstream Russian localization and language selector:

| Package | Mac | macOS | Separate Java install |
| --- | --- | --- | --- |
| `Logisim-5.0.0-macOS-Intel.zip` | Intel | 11 or newer | No |
| `Logisim-5.0.0-macOS-Apple-Silicon.zip` | M1 or newer | 11 or newer | No |

Build both reproducible ZIP archives from pinned, checksummed upstream files:

```sh
python scripts/build-modern-logisim.py --arch all
```

Only the application name and packaging are customized. The simulator remains
Logisim-evolution 5.0.0 internally, and its GPL license and source provenance are
included in each archive.

## Which download should I use?

| Package | Mac | macOS | Separate Java install |
| --- | --- | --- | --- |
| `Logisim-2.7.1-system-java` | Intel or Apple Silicon | 10.8 or newer | Yes |
| `Logisim-2.7.1-bundled-jre-x64` | Intel | 11 or newer | No |
| `Logisim-2.7.1-bundled-jre-arm64` | Apple Silicon (M1 or newer) | 11 or newer | No |
| `Logisim-2.7.1-macos-x64` | Intel | 11 or newer | No |
| `Logisim-2.7.1-macos-arm64` | Apple Silicon (M1 or newer) | 11 or newer | No |

The system-Java package is the compatibility build. Java 17 is recommended on
modern Macs; Java 8 is useful on older Intel systems. Java 6 and 7 can run this
old Logisim bytecode on legacy systems, but those Java versions are obsolete
and unsupported.

The standalone packages contain their own Java runtime. They are larger, but do
not depend on Homebrew or a system-wide Java installation.

The `bundled-jre` ZIPs can be assembled on any operating system from pinned and
checksummed OpenJDK runtimes. The Intel build uses Azul Zulu Java 8 for Catalina
compatibility; the Apple-Silicon build uses Eclipse Temurin Java 17:

```sh
python scripts/build-embedded-runtime.py --arch all
```

## Install

1. Download the package matching the table above.
2. Open the DMG or unpack the ZIP, then drag `Logisim.app` to `Applications`.
3. The builds are not Apple-notarized. On first launch, Control-click the app,
   choose **Open**, then confirm **Open**. On newer macOS releases, use
   **System Settings → Privacy & Security → Open Anyway** if that button is not
   offered in Finder.

For the system-Java package, install a compatible JDK/JRE first. On modern
Intel and Apple-Silicon Macs, an Eclipse Temurin 17 build is available from
<https://adoptium.net/temurin/releases/>.

## Build locally on a Mac

Create the widest-compatibility package:

```sh
./scripts/build-system-java-app.sh
```

Create a standalone package for the current Mac architecture (requires JDK 17
with `jpackage`):

```sh
./scripts/build-bundled-app.sh
```

Both scripts write artifacts to `dist/`. GitHub Actions builds the Intel,
Apple-Silicon, and system-Java artifacts automatically.

The system-Java ZIP can also be created on Windows or Linux without changing
its macOS executable permissions:

```sh
python scripts/build-portable.py
```

## Compatibility notes

- Apple Silicon first shipped with macOS 11, so there is no arm64 package for
  macOS 10.x.
- The `10.8+` package is architecture-neutral, but it needs a Java runtime that
  supports the installed macOS and CPU.
- Current standalone packages require macOS 11 or newer on both architectures.
  Catalina and older can use the system-Java compatibility package. Bundling an
  old, unpatched Java runtime just to lower this limit is intentionally avoided.
- CI smoke-tests each generated application on its build runner. Claims about
  older macOS releases still need testing on real legacy hardware or VMs.
- The original repository used an Intel-only Automator stub and the `screen`
  utility. This package uses a small POSIX launcher instead, avoiding Rosetta
  and unnecessary Automator privacy prompts.

## Credits

Logisim was developed by Carl Burch. This repository only supplies macOS
packaging. Original project: <http://www.cburch.com/logisim/>.
