import unittest

from maspsx import MaspsxProcessor

from .util import strip_comments


class TestAt(unittest.TestCase):

    def test_no_at_expansion_nop(self):
        """
        The 2nd value being loaded is less than 0x8000 therefore $at is not used
        and a nop is required between the two instructions
        """
        lines = [
            "lh	$2,32767($2)",
            "lh	$2,32767($2)",
        ]
        expected_lines = [
            "lh	$2,32767($2)",
            "nop",
            "lh	$2,32767($2)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_no_at_expansion_nop_negative(self):
        """
        The 2nd value being loaded is greater than -0x7FFF therefore $at is not used
        and a nop is required between the two instructions
        """
        lines = [
            "lh	$2,-32768($2)",
            "lh	$2,-32768($2)",
        ]
        expected_lines = [
            "lh	$2,-32768($2)",
            "nop",
            "lh	$2,-32768($2)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_nop(self):
        """
        The 2nd value being loaded is greater than 0x7FFF therefore $at is used
        and a nop is required between the two instructions when ASPSX 2.21 is used
        """
        lines = [
            "lh	$2,32767($2)",
            "lh	$2,32768($2)",
        ]
        expected_lines = [
            "lh	$2,32767($2)",
            "nop",
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_nop_negative(self):
        """
        The 2nd value being loaded is less than -0x8000 therefore $at is used
        and a nop is required between the two instructions when ASPSX 2.21 is used
        """
        lines = [
            "lh	$2,-32768($2)",
            "lh	$2,-32769($2)",
        ]
        expected_lines = [
            "lh	$2,-32768($2)",
            "nop",
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_no_nop(self):
        """
        The 2nd value being loaded is greater than 0x7FFF therefore $at is used
        and a nop is not required between the two instructions when ASPSX
        higher than 2.21 is used
        """
        lines = [
            "lh	$2,32767($2)",
            "lh	$2,32768($2)",
        ]
        expected_lines = [
            "lh	$2,32767($2)",
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_no_nop_negative(self):
        """
        The 2nd value being loaded is less than -0x8000 therefore $at is used
        and a nop is not required between the two instructions when ASPSX
        higher than 2.21 is used
        """
        lines = [
            "lh	$2,-32768($2)",
            "lh	$2,-32769($2)",
        ]
        expected_lines = [
            "lh	$2,-32768($2)",
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_prefix_nop(self):
        """
        The 1st value being loaded is greater than 0x7FFF therefore $at is used.
        The final load is into $v0 and therefore a nop is required between
        the two instructions
        """
        lines = [
            "lh	$2,32768($2)",
            "lh	$2,32767($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
            "nop",
            "lh	$2,32767($2)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_at_expansion_prefix_nop_negative(self):
        """
        The 1st value being loaded is less than -0x8000 therefore $at is used.
        The final load is into $v0 and therefore a nop is required between
        the two instructions
        """
        lines = [
            "lh	$2,-32769($2)",
            "lh	$2,-32768($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
            "nop",
            "lh	$2,-32768($2)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_double_at_expansion_no_nop(self):
        """
        Both values being loaded are greater than 0x7FFF therefore $at is used.
        The final load is into $v0 and therefore no nop is required between
        the two instructions
        """
        lines = [
            "lh	$2,32768($2)",
            "lh	$2,32768($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_double_at_expansion_no_nop_negative(self):
        """
        Both values being loaded are less than -0x8000 therefore $at is used.
        The final load is into $v0 and therefore no nop is required between
        the two instructions
        """
        lines = [
            "lh	$2,-32769($2)",
            "lh	$2,-32769($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_double_at_expansion_nop(self):
        """
        Both values being loaded are greater than 0x7FFF therefore $at is used.
        The final load is into $v0 and therefore a nop is required between
        the two instructions on ASPSX 2.21
        """
        lines = [
            "lh	$2,32768($2)",
            "lh	$2,32768($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
            "nop",
            ".set\tnoat",
            "lui\t$at,%hi(32768)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(32768)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_double_at_expansion_nop_negative(self):
        """
        Both values being loaded are less than -0x8000 therefore $at is used.
        The final load is into $v0 and therefore a nop is required between
        the two instructions on ASPSX 2.21
        """
        lines = [
            "lh	$2,-32769($2)",
            "lh	$2,-32769($2)",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
            "nop",
            ".set\tnoat",
            "lui\t$at,%hi(-32769)",
            "addu\t$at,$2,$at",
            "lh\t$2,%lo(-32769)($at)",
            ".set\tat",
        ]
        mp = MaspsxProcessor(lines, nop_v0_at=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)