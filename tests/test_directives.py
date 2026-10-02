import unittest

from maspsx import MaspsxProcessor, PassthroughProcessor


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
