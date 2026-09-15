# Contributing

Thanks for taking the time to improve the packages.

## Reporting a problem

Open an issue and include:

- the exact package filename;
- the computer model and CPU architecture;
- the operating-system version;
- the complete error message or terminal output;
- whether the same circuit opens in the official Logisim-evolution package.

Simulator bugs should be reported to the
[upstream project](https://github.com/logisim-evolution/logisim-evolution/issues).
This repository tracks packaging, installation, signing, and compatibility
problems specific to these downloads.

## Sending a change

Keep changes focused and document why they are needed. Before opening a pull
request, run:

```sh
python scripts/verify.py
python scripts/build-modern-logisim.py --arch all
```

macOS-specific changes must also pass the Intel and Apple Silicon jobs in GitHub
Actions. Never replace a pinned download without updating and independently
checking its size and SHA-256 digest.
