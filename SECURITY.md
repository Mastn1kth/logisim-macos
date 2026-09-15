# Security policy

## Download integrity

All third-party binaries used by the build are pinned by HTTPS URL, byte size,
and SHA-256 digest. The build stops when any of these values do not match.

## Reporting a vulnerability

For a packaging issue in this repository, open a GitHub security advisory for
`Mastn1kth/logisim-macos` instead of publishing exploit details in a public
issue. Vulnerabilities in the simulator itself or its official packages should
be reported directly to the
[Logisim-evolution project](https://github.com/logisim-evolution/logisim-evolution/security).

The packages are ad-hoc signed for structural integrity, not notarized by Apple.
Users should download releases only from this repository and may compare the
published SHA-256 checksums before installation.
