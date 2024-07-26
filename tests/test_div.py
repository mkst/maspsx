import unittest

from maspsx import MaspsxProcessor

from .util import strip_comments


class TestDivExpansion(unittest.TestCase):
    def test_div_nop(self):
        """
        Ensure we expand an li instruction during div/mflo handling
        when user has set expand_li=True
        Bug report: https://github.com/mkst/maspsx/issues/46
        """

        lines = [
            "	div	$16,$16,$2",
            "",
            "	.loc	2 173",
            "LM163:",
            "	li	$4,0x00001000		# 4096",
            "	div	$4,$4,$2",
        ]
        expected_lines = [
            # EXPAND_ZERO_DIV START
            "div\t$zero,$16,$2",
            "mflo\t$16",
            # EXPAND_ZERO_DIV END
            "li\t$4,0x00001000",
            "nop",  # DEBUG: mflo/mfhi with mult/div and li expands to 1 op
            # DEBUG: div needs expanding
            "",
            ".loc\t2 173",
            "LM163:",
            # li	$4,0x00001000		# 4096  # DEBUG: skipped
            # EXPAND_ZERO_DIV START
            "div\t$zero,$4,$2",
            "mflo\t$4",
            # EXPAND_ZERO_DIV END
        ]

        mp = MaspsxProcessor(lines, expand_li=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_div_no_nop(self):
        lines = [
            "	div	$16,$16,$2",
            "",
            "	.loc	2 173",
            "LM163:",
            "	li	$4,0x0010001		# 65537",
            "	div	$4,$4,$2",
        ]
        expected_lines = [
            # EXPAND_ZERO_DIV START
            "div\t$zero,$16,$2",
            "mflo\t$16",
            # EXPAND_ZERO_DIV END
            "li\t$4,0x0010001",
            # nop  # DEBUG: mflo/mfhi with mult/div and li expands to 2 ops
            # DEBUG: div needs expanding
            "",
            ".loc\t2 173",
            "LM163:",
            # li	$4,0x00001000		# 4096  # DEBUG: skipped
            # EXPAND_ZERO_DIV START
            "div\t$zero,$4,$2",
            "mflo\t$4",
            # EXPAND_ZERO_DIV END
        ]

        mp = MaspsxProcessor(lines, expand_li=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_div_expand_li_nop(self):
        """
        Ensure we expand an li instruction during div/mflo handling
        when user has set expand_li=True
        Bug report: https://github.com/mkst/maspsx/issues/46
        """

        lines = [
            "	div	$16,$16,$2",
            "",
            "	.loc	2 173",
            "LM163:",
            "	li	$4,0x00001000		# 4096",
            "	div	$4,$4,$2",
        ]
        expected_lines = [
            # EXPAND_ZERO_DIV START
            "div	$zero,$16,$2",
            "mflo	$16",
            # EXPAND_ZERO_DIV END
            "ori	$4,$zero,4096",
            "nop",  # DEBUG: mflo/mfhi with mult/div and li expands to 1 op
            # DEBUG: div needs expanding
            "",
            ".loc	2 173",
            "LM163:",
            # li	$4,0x00001000		# 4096  # DEBUG: skipped
            # EXPAND_ZERO_DIV START
            "div	$zero,$4,$2",
            "mflo	$4",
            # EXPAND_ZERO_DIV END
        ]

        mp = MaspsxProcessor(lines, expand_li=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_div_expand_li_no_nop(self):
        lines = [
            "	div	$16,$16,$2",
            "",
            "	.loc	2 173",
            "LM163:",
            "	li	$4,0x0010001		# 65537",
            "	div	$4,$4,$2",
        ]
        expected_lines = [
            # EXPAND_ZERO_DIV START
            "div	$zero,$16,$2",
            "mflo	$16",
            # EXPAND_ZERO_DIV END
            "lui\t$4,(65537 >> 16) & 0xFFFF",
            "ori	$4,$4,65537 & 0xFFFF",
            # nop  # DEBUG: mflo/mfhi with mult/div and li expands to 2 ops
            # DEBUG: div needs expanding
            "",
            ".loc	2 173",
            "LM163:",
            # li	$4,0x00001000		# 4096  # DEBUG: skipped
            # EXPAND_ZERO_DIV START
            "div	$zero,$4,$2",
            "mflo	$4",
            # EXPAND_ZERO_DIV END
        ]

        mp = MaspsxProcessor(lines, expand_li=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_div_expand_at_nop(self):
        """
        Only ASPSX 2.21 should insert a nop here, the sh uses $at.
        Bug report: https://github.com/mkst/maspsx/issues/76
        """
        lines = [
            "divu	$2,$2,$3",
            "sh	$2,gUpdateRate",
        ]
        expected_lines = [
            ".set\tnoat",
            "divu\t$zero,$2,$3",
            "bnez\t$3,.L_NOT_DIV_BY_ZERO_0",
            "nop",
            "break\t0x7",
            ".L_NOT_DIV_BY_ZERO_0:",
            "mflo\t$2",
            ".set\tat",
            "nop",
            "sh\t$2,gUpdateRate",
        ]

        mp = MaspsxProcessor(lines, expand_div=True, nop_v0_at=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_div_expand_at_no_nop(self):
        """
        Only ASPSX 2.21 should insert a nop here, the sh uses $at.
        Bug report: https://github.com/mkst/maspsx/issues/76
        """
        lines = [
            "divu	$2,$2,$3",
            "sh	$2,gUpdateRate",
        ]
        expected_lines = [
            ".set\tnoat",
            "divu\t$zero,$2,$3",
            "bnez\t$3,.L_NOT_DIV_BY_ZERO_0",
            "nop",
            "break\t0x7",
            ".L_NOT_DIV_BY_ZERO_0:",
            "mflo\t$2",
            ".set\tat",
            "sh\t$2,gUpdateRate",
        ]

        mp = MaspsxProcessor(lines, expand_div=True, nop_v0_at=False)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)
