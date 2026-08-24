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
