# Project notes

## macOS runtime compatibility

- Do not infer the minimum macOS version of a bundled Java runtime from
  `Info.plist`, vendor marketing, or the Java major version. Inspect every
  packaged Mach-O file's `LC_BUILD_VERSION` / `LC_VERSION_MIN_MACOSX` load
  command and use the highest OS requirement before publishing.
- A release is not fully verified until its extracted `.app` is launched on a
  matching Intel or Apple-Silicon macOS runner.
- For `lipo` validation, pass the input file before `-verify_arch`, for example
  `lipo path/to/executable -verify_arch arm64`.
