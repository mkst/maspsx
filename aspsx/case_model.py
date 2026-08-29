"""Shared case model loaded from the human-editable YAML fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).parent
FIXTURE_DIR = ROOT / "fixtures"


@dataclass(frozen=True)
class AssemblerCase:
    name: str
    source: Path
    aspsx_version: str
    expected: list[str]
    data_limit: str = ""
    extra_flags: str = ""


def _load_fixture(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        fixture = yaml.safe_load(stream)
    if (
        not isinstance(fixture, dict)
        or "source" not in fixture
        or "cases" not in fixture
    ):
        raise ValueError(f"invalid fixture file {path}: expected source and cases")
    if not isinstance(fixture["source"], str) or not fixture["source"]:
        raise ValueError(
            f"invalid fixture file {path}: source must be a non-empty string"
        )
    if not isinstance(fixture["cases"], dict) or not fixture["cases"]:
        raise ValueError(f"invalid fixture file {path}: cases must be a non-empty map")
    options = fixture.get("options", {})
    if not isinstance(options, dict):
        raise ValueError(f"invalid fixture file {path}: options must be a map")
    for option in ("data_limit", "extra_flags"):
        if option in options and not isinstance(options[option], str):
            raise ValueError(f"invalid fixture file {path}: {option} must be a string")
    for aspsx_version, expected in fixture["cases"].items():
        if not isinstance(aspsx_version, (str, int, float)):
            raise ValueError(f"invalid fixture file {path}: version must be scalar")
        if not isinstance(expected, list) or not all(
            isinstance(word, str) for word in expected
        ):
            raise ValueError(
                f"invalid fixture file {path}: expected output for {aspsx_version} "
                "must be a list of strings"
            )
    return fixture


def discover_cases() -> list[AssemblerCase]:
    cases = []
    for path in sorted(FIXTURE_DIR.glob("*.yaml")):
        fixture = _load_fixture(path)
        source = ROOT / fixture["source"]
        options = fixture.get("options", {})
        for aspsx_version, expected in fixture["cases"].items():
            cases.append(
                AssemblerCase(
                    f"{path.stem}:{aspsx_version}",
                    source,
                    str(aspsx_version),
                    expected,
                    options.get("data_limit", ""),
                    options.get("extra_flags", ""),
                )
            )
    return cases
