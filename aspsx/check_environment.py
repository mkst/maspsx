#!/usr/bin/env python3
"""Check Python packages, host runners, and ASPSX binaries."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import argparse
import shutil

from util import ASPSX_RUNNER_LOOKUP


ROOT = Path(__file__).parent


def _package_status(package: str) -> tuple[bool, str]:
    try:
        return True, version(package)
    except PackageNotFoundError:
        return False, "not installed"


def check() -> list[tuple[bool, str]]:
    results = []
    for package in ("PyYAML", "rabbitizer", "spimdisasm"):
        ok, detail = _package_status(package)
        results.append((ok, f"Python package {package} ({detail})"))

    runners = sorted(set(ASPSX_RUNNER_LOOKUP.values()))
    for runner in runners:
        executable = "dosemu" if runner == "dosemu2" else runner
        found = shutil.which(executable)
        results.append((found is not None, f"host runner {executable}"))

    for aspsx_version in ASPSX_RUNNER_LOOKUP:
        binary = ROOT / "binaries" / aspsx_version / "ASPSX.EXE"
        results.append((binary.is_file(), f"ASPSX binary {aspsx_version}"))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="return failure when any dependency is missing")
    args = parser.parse_args(argv)
    results = check()
    for ok, label in results:
        print(f"{'OK' if ok else 'MISSING':7} {label}")
    missing = sum(not ok for ok, _ in results)
    print(f"\n{len(results)} checks: {len(results) - missing} available, {missing} missing")
    return 1 if args.strict and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
