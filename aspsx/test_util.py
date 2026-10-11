from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import util


class TestRelocatedFields(unittest.TestCase):
    def test_clears_relocated_bits(self):
        text = bytes.fromhex(
            "0400828f"  # lw $v0, 0x4($gp), R_MIPS_GPREL16
            "1080023c"  # lui $v0, 0x8010, R_MIPS_HI16
            "0400000c"  # jal 0x10, R_MIPS_26
            "21082200"  # addu $at, $at, $v0
            "78563412"  # .word 0x12345678, R_MIPS_32
        )
        relocations = [(0, 7), (4, 5), (8, 4), (16, 2)]
        self.assertEqual(
            ["0x8F820000", "0x3C020000", "0x0C000000", "0x00220821", "0x00000000"],
            util._words_from_text(util.clear_relocated_fields(text, relocations)),
        )

    def test_reports_unsupported_relocation_type(self):
        with self.assertRaisesRegex(util.ObjectFormatError, "unsupported relocation"):
            util.clear_relocated_fields(bytes(4), [(0, 10)])


class TestRunner(unittest.TestCase):
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
