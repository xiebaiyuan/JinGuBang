# Environment Doctor

Check common tooling availability and versions in one place.

## Features

- Detects tool presence and versions
- Highlights missing dependencies with suggestions
- Works on macOS and Linux

## Usage

```bash
python3 system_utilities/env_doctor.py
```

## Checks

- `python3`
- `git`
- `readelf` / `llvm-readelf`
- `objdump` / `llvm-objdump`
- `md5` / `md5sum` / `openssl`
- `docker`
- `brew` (optional)

## Example Output

```
Environment Doctor
Platform: macOS (arm64)

Available:
- python3: Python 3.11.6
- git: git version 2.42.0
- md5: OpenSSL 3.0.9 30 May 2023 (Use: openssl dgst -md5 <file>)

Missing:
- readelf (readelf/llvm-readelf) not found. Suggestion: Install binutils or LLVM tools to provide readelf.
```
