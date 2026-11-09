import unittest

from maspsx import LcommAlignment, MaspsxProcessor


class TestLcommAlignment(unittest.TestCase):

    def test_max_lcomm_alignment_caps_power_of_two(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000002,2",
            "\t.lcomm\tD_80000004,5",
            "\t.lcomm\tD_80000008,9",
            "\t.lcomm\tD_80000020,32",
        ]
        mp = MaspsxProcessor(
            lines,
            sdata_limit=32,
            lcomm_alignment=LcommAlignment.POWER_OF_TWO,
            max_lcomm_alignment=8,
        )
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .sbss",
                "D_80000000:",
                "\t.space 1",
                "\t.align 1",
                "D_80000002:",
                "\t.space 2",
                "\t.align 3",
                "D_80000004:",
                "\t.space 5",
                "\t.align 3",
                "D_80000008:",
                "\t.space 9",
                "\t.align 3",
                "D_80000020:",
                "\t.space 32",
            ],
            res,
        )

    def test_max_lcomm_alignment_with_comm_for_lcomm(self):
        lines = [
            "\t.lcomm\tD_80000000,9",
            "\t.lcomm\tD_80000010,32",
        ]
        mp = MaspsxProcessor(
            lines,
            use_comm_section=True,
            use_comm_for_lcomm=True,
            lcomm_alignment=LcommAlignment.POWER_OF_TWO,
            max_lcomm_alignment=8,
        )
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,9,8",
                "\t.comm D_80000010,32,8",
            ],
            res,
        )

    def test_max_lcomm_alignment_does_not_affect_comm_symbols(self):
        lines = [
            "\t.comm\tD_80000000,32",
            "\t.lcomm\tD_80000020,32",
        ]
        mp = MaspsxProcessor(
            lines,
            use_comm_section=True,
            lcomm_alignment=LcommAlignment.POWER_OF_TWO,
            max_lcomm_alignment=8,
        )
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,32,16",
                "\t.align 3",
                "\t.globl D_80000020",
                "D_80000020:",
                "\t.space 32",
            ],
            res,
        )
