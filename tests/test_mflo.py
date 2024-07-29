import unittest

from maspsx import MaspsxProcessor


from .util import strip_comments


class TestMflo(unittest.TestCase):

    def test_mflo_disabled(self):
        lines = [
            "mult	$4,$2",
            "mflo	$4",
            "#nop",
            "#nop",
            "mult	$4,$5",
        ]
        expected_lines = [
            "mult	$4,$2",
            "mflo	$4",
            "mult	$4,$5",
        ]

        mp = MaspsxProcessor(lines, nop_mflo_mfhi=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_mflo_li(self):
        """
        li with large value will turn into two instructions (lui+ori)
        which means no nop is required
        """
        lines = [
            "	mflo	$3",
            "	li	$5,-2004318071			# 0x88888889",
            "	mult	$3,$5        ",
        ]
        expected_lines = [
            "mflo\t$3",
            "li\t$5,-2004318071",
            "mult\t$3,$5",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_mflo_li_hex(self):
        """
        li with large value will turn into two instructions (lui+ori)
        which means no nop is required
        """
        lines = [
            "	mflo	$3",
            "	li	$5,0x2aaaaaab		# 715827883",
            "	mult	$3,$5        ",
        ]
        expected_lines = [
            "mflo\t$3",
            "li\t$5,0x2aaaaaab",
            "mult\t$3,$5",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_mflo_bgez_no_set_noreorder(self):
        """
        Standard behaviour is to take the next instruction and insert a nop *after* it
        """
        lines = [
            "	mflo	$2",
            "	#nop",
            "	#nop",
            "	bgez	$2,$L14",
            "	mult	$17,$3",
        ]
        expected_lines = [
            "mflo\t$2",
            "bgez\t$2,$L14",
            "nop",
            "mult\t$17,$3",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_mflo_bgez_set_reorder(self):
        """
        Due to .set noreorder the nop should go BEFORE the bgez
        """
        lines = [
            "	mflo	$2",
            "	#nop",
            "	#nop",
            "	.set	noreorder",
            "	.set	nomacro",
            "	bgez	$2,$L14",
            "	mult	$17,$3",
        ]
        expected_lines = [
            "mflo\t$2",
            "nop",
            ".set\tnoreorder",
            "bgez\t$2,$L14",
            "mult\t$17,$3",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)
