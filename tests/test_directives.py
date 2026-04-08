import unittest

from maspsx import MaspsxProcessor


class TestDirectives(unittest.TestCase):

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
