import unittest

from maspsx import (
    strip_comments,
    line_loads_from_reg,
    uses_at,
    is_label,
)


class TestMaspsxFunctions(unittest.TestCase):
    def test_strip_comments(self):
        line = "li\t$v0,100 # comment here"
        expected = "li\t$v0,100"
        stripped = strip_comments(line)
        self.assertEqual(expected, stripped)

    def test_line_loads_from_reg_jal(self):
        line = "jal	$31,$2"
        self.assertTrue(line_loads_from_reg(line, "$2"))
        self.assertFalse(line_loads_from_reg(line, "$31"))

    def test_line_loads_from_reg_j(self):
        line = "j	$31"
        self.assertTrue(line_loads_from_reg(line, "$31"))
        self.assertFalse(line_loads_from_reg(line, "$3"))

    def test_line_loads_from_reg_beq(self):
        line = "beq   $v1, $v0, .L801B79E8"
        self.assertTrue(line_loads_from_reg(line, "$v0"))
        self.assertTrue(line_loads_from_reg(line, "$v1"))

    def test_line_loads_from_reg_mult(self):
        line = "mult  $v1, $a0"
        self.assertTrue(line_loads_from_reg(line, "$a0"))
        self.assertTrue(line_loads_from_reg(line, "$v1"))

    def test_line_loads_from_reg_addu(self):
        line = "addu  $s1, $a0, $zero"
        self.assertTrue(line_loads_from_reg(line, "$a0"))
        self.assertFalse(line_loads_from_reg(line, "$s1"))

    def test_line_uses_at(self):
        line = "sb   $2, g_InputSaveName($3)"
        self.assertTrue(uses_at(line))

    def test_is_label(self):
        labels = [
            "$L38:",
            "$Lb0:",
            "$Le3:",
            # "LM132:",  # NOTE: this is a line marker not true label
        ]
        for label in labels:
            with self.subTest():
                self.assertTrue(is_label(label))
