import unittest

from maspsx import MaspsxProcessor

from .util import strip_comments


class TestLcomm(unittest.TestCase):
    def test_lcomm_is_global_by_default(self):
        lines = [
            "	.lcomm	staticVar,8",
            "	.comm	globalVar,8",
        ]
        expected_lines = [
            ".section .bss",
            ".align 2",
            ".globl staticVar",
            "staticVar:",
            ".space 8",
            ".align 2",
            ".globl globalVar",
            "globalVar:",
            ".space 8",
        ]

        mp = MaspsxProcessor(lines, sdata_limit=0)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_local_lcomm_only_affects_lcomm(self):
        lines = [
            "	.lcomm	staticVar,8",
            "	.comm	globalVar,8",
        ]
        expected_lines = [
            ".section .bss",
            ".align 2",
            "staticVar:",
            ".space 8",
            ".align 2",
            ".globl globalVar",
            "globalVar:",
            ".space 8",
        ]

        mp = MaspsxProcessor(lines, sdata_limit=0, local_lcomm=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_local_lcomm_does_not_change_sbss(self):
        lines = [
            "	.lcomm	staticVar,4",
        ]

        mp = MaspsxProcessor(lines, sdata_limit=8)
        expected_lines = strip_comments(mp.process_lines())

        mp = MaspsxProcessor(lines, sdata_limit=8, local_lcomm=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_local_lcomm_has_no_effect_without_lcomm(self):
        lines = [
            "	.comm	globalVar,8",
            "	.data",
            "	.globl	initialised",
            "initialised:",
            "	.word	5",
            "	.text",
            "foo:",
            "	lw	$2,globalVar",
        ]

        mp = MaspsxProcessor(lines, sdata_limit=0)
        expected_lines = strip_comments(mp.process_lines())

        mp = MaspsxProcessor(lines, sdata_limit=0, local_lcomm=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_comm_for_lcomm_takes_precedence_over_local_lcomm(self):
        lines = [
            "	.lcomm	staticVar,8",
            "	.comm	globalVar,8",
        ]
        expected_lines = [
            ".section .bss",
            ".comm staticVar,8,4",
            ".comm globalVar,8,8",
        ]

        mp = MaspsxProcessor(
            lines,
            sdata_limit=0,
            use_comm_section=True,
            use_comm_for_lcomm=True,
            local_lcomm=True,
        )
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)
