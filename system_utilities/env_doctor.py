#!/usr/bin/env python3
# filepath: env_doctor.py

import argparse
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    command: str
    found: bool
    version: Optional[str]
    detail: Optional[str] = None
    suggestion: Optional[str] = None


def run_command(command: List[str]) -> Optional[str]:
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return output.strip()


def detect_version(command: str, version_args: List[List[str]]) -> Optional[str]:
    if not shutil.which(command):
        return None
    for args in version_args:
        output = run_command([command] + args)
        if output:
            first_line = output.splitlines()[0]
            return first_line
    return "version unavailable"


def detect_primary(commands: List[str]) -> Optional[str]:
    for cmd in commands:
        if shutil.which(cmd):
            return cmd
    return None


def build_checks(is_macos: bool) -> List[CheckResult]:
    checks = []

    def add(name, command, version_args, suggestion=None, detail=None):
        version = detect_version(command, version_args)
        checks.append(
            CheckResult(
                name=name,
                command=command,
                found=version is not None,
                version=version,
                suggestion=suggestion,
                detail=detail,
            )
        )

    add(
        "python3",
        "python3",
        [["--version"]],
        suggestion="Install Python 3 via brew, apt, or pyenv.",
    )
    add(
        "git",
        "git",
        [["--version"]],
        suggestion="Install Git via brew or your system package manager.",
    )

    readelf_cmd = detect_primary(["readelf", "llvm-readelf"])
    if readelf_cmd:
        add("readelf", readelf_cmd, [["--version"]])
    else:
        checks.append(
            CheckResult(
                name="readelf",
                command="readelf/llvm-readelf",
                found=False,
                version=None,
                suggestion="Install binutils or LLVM tools to provide readelf.",
            )
        )

    objdump_cmd = detect_primary(["objdump", "llvm-objdump"])
    if objdump_cmd:
        add("objdump", objdump_cmd, [["--version"]])
    else:
        checks.append(
            CheckResult(
                name="objdump",
                command="objdump/llvm-objdump",
                found=False,
                version=None,
                suggestion="Install binutils or LLVM tools to provide objdump.",
            )
        )

    md5_cmd = detect_primary(["md5", "md5sum", "openssl"])
    if md5_cmd:
        if md5_cmd == "openssl":
            add(
                "md5",
                md5_cmd,
                [["version"]],
                detail="Use: openssl dgst -md5 <file>",
            )
        else:
            add("md5", md5_cmd, [["--version"], ["-v"]])
    else:
        checks.append(
            CheckResult(
                name="md5",
                command="md5/md5sum/openssl",
                found=False,
                version=None,
                suggestion="Install coreutils or openssl to provide md5 tooling.",
            )
        )

    add(
        "docker",
        "docker",
        [["--version"]],
        suggestion="Install Docker Desktop or docker engine.",
    )

    if is_macos:
        add(
            "brew", "brew", [["--version"]], suggestion="Install Homebrew from brew.sh."
        )
    else:
        add(
            "brew",
            "brew",
            [["--version"]],
            suggestion="Optional: install Homebrew on Linux if needed.",
        )

    return checks


def render_report(checks: List[CheckResult], is_macos: bool):
    platform_name = "macOS" if is_macos else platform.system()
    print("Environment Doctor")
    print(f"Platform: {platform_name} ({platform.machine()})")

    ok = [c for c in checks if c.found]
    missing = [c for c in checks if not c.found]

    print("\nAvailable:")
    if ok:
        for item in ok:
            detail = f" ({item.detail})" if item.detail else ""
            print(f"- {item.name}: {item.version}{detail}")
    else:
        print("- none")

    print("\nMissing:")
    if missing:
        for item in missing:
            suggestion = f" Suggestion: {item.suggestion}" if item.suggestion else ""
            print(f"- {item.name} ({item.command}) not found.{suggestion}")
    else:
        print("- none")


def main():
    parser = argparse.ArgumentParser(
        description="Check common toolchain availability and versions."
    )
    parser.parse_args()
    is_macos = platform.system().lower() == "darwin"
    checks = build_checks(is_macos)
    render_report(checks, is_macos)


if __name__ == "__main__":
    main()
