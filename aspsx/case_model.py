"""Shared case model loaded from the human-editable YAML fixtures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from util import DATA_SECTIONS, SymbolOffsets

ROOT = Path(__file__).parent
FIXTURE_DIR = ROOT / "fixtures"

TEXT_SECTION = ".text"


@dataclass(frozen=True)
class AssemblerCase:
    name: str
    source: Path
    aspsx_version: str
    text: Optional[list[str]]
    sections: dict[str, SymbolOffsets] = field(default_factory=dict)
    data_limit: str = ""
    extra_flags: str = ""


def _validate_expected(path: Path, aspsx_version, expected) -> None:
    prefix = f"invalid fixture file {path}: expected output for {aspsx_version}"
    if not isinstance(expected, dict) or not expected:
        raise ValueError(f"{prefix} must be a non-empty map of sections")
    for section, contents in expected.items():
        if section == TEXT_SECTION:
            if not isinstance(contents, list) or not all(
                isinstance(word, str) for word in contents
            ):
                raise ValueError(f"{prefix}: {section} must be a list of strings")
        elif section in DATA_SECTIONS:
            if (
                not isinstance(contents, dict)
                or not contents
                or not all(
                    isinstance(name, str)
                    and (
                        offset is None
                        or (isinstance(offset, int) and not isinstance(offset, bool))
                    )
                    for name, offset in contents.items()
                )
            ):
                raise ValueError(
                    f"{prefix}: {section} must be a non-empty map of symbol names "
                    "to offsets, or to null for `.comm` symbols"
                )
        else:
            raise ValueError(f"{prefix}: unknown section {section!r}")


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
        _validate_expected(path, aspsx_version, expected)
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
                    expected.get(TEXT_SECTION),
                    {
                        section: contents
                        for section, contents in expected.items()
                        if section != TEXT_SECTION
                    },
                    options.get("data_limit", ""),
                    options.get("extra_flags", ""),
                )
            )
    return cases
