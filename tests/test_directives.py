import unittest

from maspsx import LcommAlignment, MaspsxProcessor, PassthroughProcessor


class TestDirectives(unittest.TestCase):

    def test_passthrough_processor_only_removes_coff_directives(self):
        lines = [
            '  .file 1 "test.c"',
            "\t.def\tfoo",
            "\t.begin\tfoo",
            "foo:",
            "\tmove\t$2, $3  # preserve",
            "\t.bend\tfoo",
            "",
        ]

        processor = PassthroughProcessor(lines)

        self.assertEqual(
            [
                '.file 1 "test.c"',
                "foo:",
                "move\t$2, $3  # preserve",
                "",
            ],
            processor.process_lines(),
        )

    def test_file_directive(self):
        line = '.file\t1 "/tmp/code.c"'
        mp = MaspsxProcessor([])
        res = mp.process_line(line)
        self.assertEqual([line], res)
        self.assertEqual(mp.file_num, 2)

    def test_file_directive_with_space(self):
        line = '.file\t1 "E:/ROOT/My Project/VehCalc_InterpSpeed.c"'
        mp = MaspsxProcessor([])
        res = mp.process_line(line)
        self.assertEqual([line], res)
        self.assertEqual(mp.file_num, 2)

    def test_comm_default_alignment(self):
        lines = [
            "\t.comm\tD_80000000,1",
            "\t.comm\tD_80000004,8",
            "\t.comm\tD_8000000C,32",
        ]
        mp = MaspsxProcessor(lines, use_comm_section=True)
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,1,1",
                "\t.comm D_80000004,8,8",
                "\t.comm D_8000000C,32,16",
            ],
            res,
        )

    def test_comm_max_alignment(self):
        lines = [
            "\t.comm\tD_80000000,1",
            "\t.comm\tD_80000004,3",
            "\t.comm\tD_80000008,8",
        ]
        mp = MaspsxProcessor(lines, use_comm_section=True, max_comm_alignment=4)
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,1,1",
                "\t.comm D_80000004,3,4",
                "\t.comm D_80000008,8,4",
            ],
            res,
        )

    def test_lcomm_alignment_none(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000001,2",
            "\t.lcomm\tD_80000003,5",
        ]
        mp = MaspsxProcessor(lines, lcomm_alignment=LcommAlignment.NONE)
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.globl D_80000000",
                "D_80000000:",
                "\t.space 1",
                "\t.globl D_80000001",
                "D_80000001:",
                "\t.space 2",
                "\t.globl D_80000003",
                "D_80000003:",
                "\t.space 5",
            ],
            res,
        )

    def test_lcomm_alignment_word(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000004,2",
            "\t.lcomm\tD_80000008,5",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=8, lcomm_alignment=LcommAlignment.WORD)
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .sbss",
                "\t.align 2",
                "D_80000000:",
                "\t.space 4",
                "\t.align 2",
                "D_80000004:",
                "\t.space 4",
                "\t.align 2",
                "D_80000008:",
                "\t.space 8",
            ],
            res,
        )

    def test_lcomm_alignment_power_of_two(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000002,2",
            "\t.lcomm\tD_80000004,3",
            "\t.lcomm\tD_80000008,5",
            "\t.lcomm\tD_80000010,9",
            "\t.lcomm\tD_80000020,32",
        ]
        mp = MaspsxProcessor(
            lines, sdata_limit=32, lcomm_alignment=LcommAlignment.POWER_OF_TWO
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
                "\t.align 2",
                "D_80000004:",
                "\t.space 3",
                "\t.align 3",
                "D_80000008:",
                "\t.space 5",
                "\t.align 4",
                "D_80000010:",
                "\t.space 9",
                "\t.align 4",
                "D_80000020:",
                "\t.space 32",
            ],
            res,
        )

    def test_lcomm_alignment_with_comm_for_lcomm(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000004,5",
        ]
        mp = MaspsxProcessor(
            lines,
            use_comm_section=True,
            use_comm_for_lcomm=True,
            lcomm_alignment=LcommAlignment.WORD,
        )
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,1,4",
                "\t.comm D_80000004,5,4",
            ],
            res,
        )

    def test_lcomm_max_alignment_with_comm_for_lcomm(self):
        lines = [
            "\t.lcomm\tD_80000000,1",
            "\t.lcomm\tD_80000002,2",
            "\t.lcomm\tD_80000004,9",
        ]
        mp = MaspsxProcessor(
            lines,
            use_comm_section=True,
            use_comm_for_lcomm=True,
            max_comm_alignment=2,
            lcomm_alignment=LcommAlignment.POWER_OF_TWO,
        )
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .bss",
                "\t.comm D_80000000,1,1",
                "\t.comm D_80000002,2,2",
                "\t.comm D_80000004,9,2",
            ],
            res,
        )

    def test_comm_ignores_sdata_limit(self):
        lines = [
            "\t.comm\tD_80000000,4",
            "\t.lcomm\tD_80000004,4",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=8, comm_uses_sdata_limit=False)
        res = mp.process_lines()

        self.assertEqual(
            [
                ".section .sbss",
                "\t.align 2",
                "D_80000004:",
                "\t.space 4",
                ".section .bss",
                "\t.align 2",
                "\t.globl D_80000000",
                "D_80000000:",
                "\t.space 4",
            ],
            res,
        )
