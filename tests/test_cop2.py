"""COP2 scheduling specifications backed by aspsx/fixtures/cop2_*.yaml."""

import importlib.util
import subprocess
import sys
from pathlib import Path
import unittest

from maspsx import MaspsxProcessor

VERSIONS = (
    "1.05",
    "1.07",
    "2.05",
    "2.08",
    "2.21",
    "2.30",
    "2.34",
    "2.56",
    "2.67",
    "2.77",
    "2.79",
    "2.81",
    "2.86",
)
EARLY = VERSIONS[:4]
BEFORE_230 = VERSIONS[:5]
CTC2_SECOND_OPERAND = ("2.30", "2.34")
LATE = VERSIONS[7:]
OPS = ("mfc2", "cfc2", "mtc2", "ctc2")


class TestCop2Characterization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "maspsx.py"
        spec = importlib.util.spec_from_file_location("maspsx_cop2_cli", path)
        cls.cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.cli)

    def instructions(self, version, lines):
        config = self.cli.config_for_aspsx_version(version)
        output = MaspsxProcessor(lines, **vars(config)).process_lines()
        # Compare processor instructions, leaving assembler directives out of
        # these narrow scheduling specifications. No host assembler is used.
        return [
            " ".join(line.split())
            for raw in output
            for part in raw.split("#", 1)[0].split(";")
            if (line := part.strip()) and not line.startswith(".")
        ]

    def test_load_to_transfer(self):
        """cop2_load_delay: both operand numbers, WAW, and unrelated control."""
        for version in VERSIONS:
            for op in OPS:
                for first, second in ((4, 8), (8, 4), (8, 8), (4, 5)):
                    if version in EARLY:
                        needs_nop = 8 in (first, second)
                    elif version == "2.21":
                        needs_nop = first == 8
                    elif op == "ctc2" and version in CTC2_SECOND_OPERAND:
                        needs_nop = second == 8
                    else:
                        needs_nop = op in ("mtc2", "ctc2") and first == 8
                    lines = ["lhu $8,370($18)", f"{op} ${first},${second}"]
                    expected = [lines[0], *(["nop"] if needs_nop else []), lines[1]]
                    with self.subTest(version=version, op=op, operands=(first, second)):
                        self.assertEqual(expected, self.instructions(version, lines))

    def test_transfer_to_gpr_consumer(self):
        """cop2_read_delay: mfc2/cfc2 consumers and overwritten destinations."""
        for version in VERSIONS:
            for op in OPS:
                for consumer, reads in (
                    ("addu $9,$8,$10", True),
                    ("addu $8,$9,$10", False),
                    ("lw $8,0($2)", False),
                ):
                    producer_delays = op == "mfc2" or (
                        op == "cfc2" and version not in BEFORE_230
                    )
                    needs_nop = producer_delays and (reads or version in BEFORE_230)
                    lines = [f"{op} $8,$4", consumer]
                    expected = [lines[0], *(["nop"] if needs_nop else []), lines[1]]
                    with self.subTest(version=version, op=op, consumer=consumer):
                        self.assertEqual(expected, self.instructions(version, lines))

    def test_noreorder_read_delay(self):
        """cop2_modes: cfc2 retains scheduling under noreorder in 2.30+."""
        for version in VERSIONS:
            for op in ("mfc2", "cfc2"):
                lines = [".set\tnoreorder", f"{op} $8,$4", "addu $9,$8,$10"]
                needs_nop = op == "cfc2" and version not in BEFORE_230
                expected = [lines[1], *(["nop"] if needs_nop else []), lines[2]]
                with self.subTest(version=version, op=op):
                    self.assertEqual(expected, self.instructions(version, lines))

    def test_transfer_to_cop2_command(self):
        """cop2_gte_delay: 2.56+ counts two slots, including under noreorder."""
        for version in VERSIONS:
            for op in OPS:
                for gap in (0, 1, 2):
                    for noreorder in (False, True):
                        body = [
                            f"{op} $8,$4",
                            *["addu $10,$11,$12"] * gap,
                            "cop2 0x0180001",
                        ]
                        inserted = (
                            max(0, 2 - gap)
                            if version in LATE and op in ("mtc2", "ctc2")
                            else 0
                        )
                        expected = [*body[:-1], *["nop"] * inserted, body[-1]]
                        lines = ([".set\tnoreorder"] if noreorder else []) + body
                        with self.subTest(
                            version=version, op=op, gap=gap, noreorder=noreorder
                        ):
                            self.assertEqual(
                                expected, self.instructions(version, lines)
                            )

    def test_read_consumers(self):
        # Inserted nops for groups 1.05–2.08 / 2.21 / 2.30–2.34 / 2.56+.
        consumers = (
            ("sw $8,0($2)", (1, 1, 1, 1)),
            ("lw $9,0($8)", (1, 1, 1, 1)),
            ("mtc2 $8,$5", (1, 1, 1, 1)),
            ("ctc2 $8,$5", (1, 1, 0, 1)),
            ("mfc2 $8,$5", (1, 1, 0, 0)),
            ("cfc2 $8,$5", (1, 1, 0, 0)),
            ("lwc2 $8,0($2)", (1, 0, 0, 0)),
            ("swc2 $8,0($2)", (1, 0, 1, 0)),
            ("lwc2 $4,0($8)", (1, 1, 1, 1)),
            ("swc2 $4,0($8)", (1, 1, 1, 1)),
            ("addu $9,$4,$10", (0, 0, 0, 0)),
        )
        for version in VERSIONS:
            group = (
                0
                if version in EARLY
                else 1 if version == "2.21" else 3 if version in LATE else 2
            )
            for op in ("mfc2", "cfc2"):
                for consumer, counts in consumers:
                    nops = counts[group] if op == "mfc2" or group >= 2 else 0
                    lines = [f"{op} $8,$4", consumer]
                    expected = [lines[0], *["nop"] * nops, consumer]
                    with self.subTest(version=version, op=op, consumer=consumer):
                        self.assertEqual(expected, self.instructions(version, lines))

    def test_load_types_and_noreorder(self):
        for version in VERSIONS:
            for load in ("lb", "lbu", "lh", "lhu", "lw", "lwl", "lwr"):
                for op in OPS:
                    lines = [".set\tnoreorder", f"{load} $8,0($18)", f"{op} $8,$4"]
                    with self.subTest(version=version, load=load, op=op):
                        self.assertEqual(lines[1:], self.instructions(version, lines))

    def test_mode_switch_uses_producer_mode(self):
        # cop2_mode_switch: switching modes does not change a preceding load.
        for version in VERSIONS:
            for before, after in (("reorder", "noreorder"), ("noreorder", "reorder")):
                for op in OPS:
                    for incoming in (False, True):
                        if incoming:
                            pair = ["lw $8,0($18)", f"{op} $8,$4"]
                            dependent = (
                                op == "mtc2"
                                or version in BEFORE_230
                                or (op == "ctc2" and version in LATE)
                            )
                            nops = int(before == "reorder" and dependent)
                        else:
                            pair = [f"{op} $8,$4", "addu $9,$8,$10"]
                            nops = int(
                                (op == "mfc2" and before == "reorder")
                                or (op == "cfc2" and version not in BEFORE_230)
                            )
                        lines = [f".set\t{before}", pair[0], f".set\t{after}", pair[1]]
                        with self.subTest(
                            version=version, before=before, op=op, incoming=incoming
                        ):
                            self.assertEqual(
                                [pair[0], *["nop"] * nops, pair[1]],
                                self.instructions(version, lines),
                            )

    def test_semicolon_macros(self):
        # Modes fixture covers both load/transfer and transfer/consumer macros.
        for version in VERSIONS:
            for body in (
                ["lw $8,0($18)", "mtc2 $8,$4"],
                ["mfc2 $8,$4", "addu $9,$8,$10"],
                ["cfc2 $8,$4", "addu $9,$8,$10"],
                ["ctc2 $8,$4", "cop2 0x0180001"],
            ):
                expected = self.instructions(version, body)
                for macro in ("; ".join(body), ";\t".join(body)):
                    with self.subTest(version=version, macro=macro):
                        self.assertEqual(
                            expected,
                            self.instructions(version, ["#APP", macro, "#NO_APP"]),
                        )

    def test_zero_register(self):
        for version in VERSIONS:
            for op in OPS:
                lines = ["lw $0,0($18)", f"{op} $0,$4"]
                with self.subTest(version=version, op=op):
                    self.assertEqual(lines, self.instructions(version, lines))

    def test_explicit_nops_satisfy_command_delay(self):
        for version in VERSIONS:
            for gap in (1, 2, 3):
                lines = ["mtc2 $8,$4", *["nop"] * gap, "cop2 0x0180001"]
                expected = [
                    lines[0],
                    *["nop"] * max(gap, 2 if version in LATE else 0),
                    lines[-1],
                ]
                with self.subTest(version=version, gap=gap):
                    self.assertEqual(expected, self.instructions(version, lines))

    def test_expanded_instructions_satisfy_command_delay(self):
        # cop2_expansion_gap: a pseudo that emits two words fills both slots.
        for version in VERSIONS:
            for gap in (
                "li $10,0x12345678",
                "la $10,0x12345678",
                "lw $10,0x10000($18)",
                "lw $10,symbol",
            ):
                lines = ["mtc2 $8,$4", gap, "cop2 0x0180001"]
                with self.subTest(version=version, gap=gap):
                    self.assertNotIn("nop", self.instructions(version, lines))

    def test_single_word_gnu_immediates(self):
        # These forms remain pseudos in 2.56+, but GNU as emits one word.
        for version in LATE:
            for value in ("-65536", "-2147483648"):
                lines = ["mtc2 $8,$4", f"li $10,{value}", "cop2 0x0180001"]
                with self.subTest(version=version, value=value):
                    self.assertEqual(
                        [*lines[:-1], "nop", lines[-1]],
                        self.instructions(version, lines),
                    )

    def test_cli_version_reaches_processor(self):
        for version in VERSIONS:
            with self.subTest(version=version):
                proc = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve().parents[1] / "maspsx.py"),
                        "--force-stdin",
                        "--aspsx-version",
                        version,
                    ],
                    input="lhu\t$8,370($18)\nctc2\t$8,$4\n",
                    text=True,
                    capture_output=True,
                    timeout=10,
                )
                self.assertEqual(0, proc.returncode, proc.stderr)
                nops = [
                    line
                    for raw in proc.stdout.splitlines()
                    if (line := raw.split("#", 1)[0].strip()) == "nop"
                ]
                self.assertEqual(0 if version in CTC2_SECOND_OPERAND else 1, len(nops))
