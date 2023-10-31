import unittest

from maspsx import MaspsxProcessor


def strip_comments(lines):
    res = []
    for line in lines:
        if line.startswith("#"):
            continue
        if "#" in line:
            line, *_ = line.split("#")
        res.append(line.strip())
    return res


class TestNop(unittest.TestCase):
    def test_nop_lw_div(self):
        """
        Ensure we place a nop betwen an lw/div pair that uses the same register
        """
        lines = [
            "	lw	$3,0($5)",
            "	#nop",
            "	div	$3,$3,$7",
        ]
        expected_lines = [
            "lw\t$3,0($5)",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_div_mult(self):
        """
        mult and mflo/mhfi must be separated by at least two instructions
        """
        lines = [
            "	div	$3,$3,$6",
            "",
            "	.loc	2 67",
            "	mult	$3,$5",
        ]
        expected_lines = [
            "div\t$zero,$3,$6",
            "mflo\t$3",  # expanded div
            "nop",
            "nop",
            "mult\t$3,$5",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:5])

    def test_nop_at_expansion_with_macro(self):
        """
        Ensure we can handle a macro that follows an $at expansion
        """
        lines = [
            "	lw	$19,Cameras($2)",
            "",
            "	.loc	2 41",
            " #APP",
            "	lw	$12, 0( $19 );lw	$13, 4( $19 );ctc2	$12, $0;ctc2	$13, $1;lw	$12, 8( $19 );lw	$13, 12( $19 );lw	$14, 16( $19 );ctc2	$12, $2;ctc2	$13, $3;ctc2	$14, $4",
            " #NO_APP",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(Cameras)",
            "addu\t$at,$at,$2",
            "lw\t$19,%lo(Cameras)($at)",
            ".set\tat",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:6])
