"""Compare Maspsx + GNU as output directly with the COP2 reference fixtures."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from case_model import discover_cases
import util

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from maspsx import MaspsxProcessor


@unittest.skipUnless(
    shutil.which("mips-linux-gnu-as"), "GNU MIPS assembler unavailable"
)
class TestMaspsxCop2Matrix(unittest.TestCase):
    def test_cop2_reference_words(self):
        spec = importlib.util.spec_from_file_location("cop2_cli", ROOT / "maspsx.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        cases = [
            case
            for case in discover_cases()
            if case.name.startswith(("cop2_", "cfc2:", "mtc2:"))
        ]
        for case in cases:
            with self.subTest(case=case.name):
                config = cli.config_for_aspsx_version(case.aspsx_version)
                output = MaspsxProcessor(
                    case.source.read_text().splitlines(), **vars(config)
                ).process_lines()
                # Production emits noreorder at .ent. These small fixtures have
                # no function wrapper; prevent GNU as from scheduling them.
                source = ".text\n.set noreorder\n" + "\n".join(output) + "\n"
                with tempfile.TemporaryDirectory(prefix="cop2-gnu-") as temp:
                    object_path = Path(temp) / "out.o"
                    proc = subprocess.run(
                        [
                            "mips-linux-gnu-as",
                            "-EL",
                            "-march=r3000",
                            "-G0",
                            "-o",
                            str(object_path),
                            "-",
                        ],
                        input=source,
                        text=True,
                        capture_output=True,
                        timeout=util.DEFAULT_TIMEOUT,
                    )
                    self.assertEqual(0, proc.returncode, proc.stderr)
                    actual = util.read_text_section(object_path.read_bytes())
                expected = b"".join(
                    int(word, 16).to_bytes(4, "little") for word in case.text
                )
                self.assertEqual(expected, actual[: len(expected)])
                # GNU as rounds .text size up to a multiple of 16 bytes.
                padding = actual[len(expected) :]
                self.assertLessEqual(len(padding), 12)
                self.assertEqual(bytes(len(padding)), padding)
