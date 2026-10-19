from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import case_model
import util


class TestRunnerCommand(unittest.TestCase):
    def test_16_bit_versions_use_daze(self):
        command = util._build_command(
            "daze",
            Path("ASPSX.EXE"),
            Path("/tmp/workspace"),
            "input.s",
            "output.obj",
            "",
            "",
        )
        self.assertEqual(["daze", "ASPSX.EXE", "-o", "output.obj", "input.s"], command)

    def test_32_bit_versions_use_wibo(self):
        command = util._build_command(
            "wibo",
            Path("/tools/ASPSX.EXE"),
            Path("/tmp/workspace"),
            "input.s",
            "output.obj",
            "",
            "",
        )
        self.assertEqual(
            ["wibo", "/tools/ASPSX.EXE", "-o", "output.obj", "input.s"],
            command,
        )


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
            "wibo",
            ["wibo", "ASPSX.EXE"],
            returncode=1,
            error="assembler process exited unsuccessfully",
            failure_kind="process_error",
        )
        self.assertEqual("process_error", result.status)
        self.assertIn("status: process_error", result.diagnostic())

    @patch(
        "util.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            ["wibo", "ASPSX.EXE"], 1, output=b"partial", stderr=b"timeout"
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


class TestOutputDiff(unittest.TestCase):
    def result(self, sections):
        return util.RunResult(
            Path("ASM/GP.S"),
            "2.67",
            "wibo",
            [],
            instructions=["0x00000000"],
            sections=sections,
        )

    def test_matching_output_has_no_report(self):
        result = self.result({".sbss": {"a": 0x0, "tail": 0x4}})
        self.assertEqual(
            "",
            util.output_diff(
                ["0x00000000"], {".sbss": {"a": 0x0, "tail": 0x4}}, result
            ),
        )

    def test_only_listed_sections_are_checked(self):
        result = self.result({".sbss": {"a": 0x0}})
        self.assertEqual("", util.output_diff(None, {}, result))

    def test_only_listed_symbols_are_checked(self):
        result = self.result({".sbss": {"pad": 0x0, "x": 0x4}})
        self.assertEqual("", util.output_diff(None, {".sbss": {"x": 0x4}}, result))

    def test_reports_moved_and_missing_symbols(self):
        result = self.result({".sbss": {"a": 0x0, "b": 0x8, "c": 0xC}})
        report = util.output_diff(
            None, {".sbss": {"a": 0x0, "b": 0x4, "tail": 0x8}}, result
        )
        self.assertIn(".sbss mismatch", report)
        self.assertRegex(report, r"\nb\s+0x4\s+0x8")
        self.assertRegex(report, r"\ntail\s+0x8\s+<missing>")
        self.assertNotRegex(report, r"\n[ac]\s")

    def test_common_symbols_are_checked_by_section(self):
        result = self.result({".sbss": {"l": 0x0}, ".bss": {"c": None}})
        self.assertEqual("", util.output_diff(None, {".bss": {"c": None}}, result))
        report = util.output_diff(None, {".sbss": {"c": None}}, result)
        self.assertRegex(report, r"\nc\s+<comm>\s+<missing>")
        report = util.output_diff(None, {".sbss": {"l": None}}, result)
        self.assertRegex(report, r"\nl\s+<comm>\s+0x0")


class TestFixtureModel(unittest.TestCase):
    def load(self, cases: str) -> dict:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "case.yaml"
            path.write_text("source: ASM/GP.S\ncases:\n" + cases)
            return case_model._load_fixture(path)

    def test_accepts_text_and_data_sections(self):
        fixture = self.load(
            '  "2.67":\n'
            "    .text:\n"
            '      - "0x00000000"\n'
            "    .sbss:\n"
            "      a: 0x0\n"
            "      tail: 0x4\n"
            "      c: null\n"
        )
        self.assertEqual(
            {"a": 0, "tail": 4, "c": None}, fixture["cases"]["2.67"][".sbss"]
        )

    def test_rejects_unknown_section(self):
        with self.assertRaisesRegex(ValueError, "unknown section '.foo'"):
            self.load('  "2.67":\n    .foo:\n      a: 0x0\n')

    def test_rejects_non_integer_offset(self):
        with self.assertRaisesRegex(ValueError, "non-empty map of symbol names"):
            self.load('  "2.67":\n    .sbss:\n      a: zero\n')

    def test_rejects_empty_section(self):
        with self.assertRaisesRegex(ValueError, "non-empty map of symbol names"):
            self.load('  "2.67":\n    .sbss: {}\n')

    def test_rejects_bare_word_list(self):
        with self.assertRaisesRegex(ValueError, "non-empty map of sections"):
            self.load('  "2.67":\n    - "0x00000000"\n')
