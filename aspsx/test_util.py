from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import util


def make_text_object(payload: bytes) -> bytes:
    return (
        b"LNK\x02"
        + bytes([16, 1, 0, 0, 0, 0, 5])
        + b".text"
        + bytes([6, 1, 0, 2, len(payload), 0])
        + payload
    )


class TestObjectParser(unittest.TestCase):
    def test_reads_text_words(self):
        obj = make_text_object(bytes.fromhex("21082200"))
        self.assertEqual(bytes.fromhex("21082200"), util.read_text_section(obj))
        self.assertEqual(
            ["0x00220821"], util._words_from_text(util.read_text_section(obj))
        )

    def test_reports_truncated_object(self):
        with self.assertRaisesRegex(util.ObjectFormatError, "truncated"):
            util.read_text_section(b"LNK\x02\x10")

    def test_reports_unknown_version_without_crashing(self):
        result = util.run_aspsx_result(Path("ASM/GP.S"), {"aspsx_version": "unknown"})
        self.assertFalse(result.ok)
        self.assertEqual("unsupported_version", result.status)
        self.assertIn("no runner is configured", result.diagnostic())

    def test_failure_diagnostic_has_category(self):
        result = util.RunResult(
            Path("ASM/GP.S"),
            "2.67",
            "wine",
            ["wine", "ASPSX.EXE"],
            returncode=1,
            error="assembler process exited unsuccessfully",
            failure_kind="process_error",
        )
        self.assertEqual("process_error", result.status)
        self.assertIn("status: process_error", result.diagnostic())

    @patch(
        "util.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["wine", "ASPSX.EXE"], 1, output=b"partial", stderr=b"timeout"
        ),
    )
    def test_timeout_remains_a_timeout_result(self, _run):
        result = util.run_aspsx_result(Path("ASM/GP.S"), {"aspsx_version": "2.67"})
        self.assertFalse(result.ok)
        self.assertEqual("timeout", result.status)
        self.assertIn("partial", result.stdout)

    @patch("util.subprocess.run", side_effect=PermissionError("not executable"))
    def test_runner_permission_error_is_reported(self, _run):
        result = util.run_aspsx_result(Path("ASM/GP.S"), {"aspsx_version": "2.67"})
        self.assertFalse(result.ok)
        self.assertEqual("permission_error", result.status)

    def test_invalid_flags_are_reported(self):
        result = util.run_aspsx_result(
            Path("ASM/GP.S"), {"aspsx_version": "2.67"}, extra_flags='"'
        )
        self.assertFalse(result.ok)
        self.assertEqual("command_error", result.status)


class TestAssemblyDiff(unittest.TestCase):
    def test_includes_raw_words_and_disassembly(self):
        diff = util.assembly_diff(["0x00220821"], ["0x8F820000"])
        self.assertIn("0x00220821", diff)
        self.assertIn("0x8F820000", diff)
        self.assertIn("addu", diff)
        self.assertIn("lw", diff)
