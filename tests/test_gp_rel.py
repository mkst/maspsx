import unittest

from maspsx import MaspsxProcessor

from .util import strip_comments


class TestGpRel(unittest.TestCase):
    def test_gp_rel_load_with_offset(self):
        lines = [
            "	.comm	savedInfoTracker,16",
            "	lw	$4,savedInfoTracker+4",
            "	lw	$2,savedInfoTracker+8",
        ]
        expected_lines = [
            "lw\t$4,%gp_rel(savedInfoTracker+4)($gp)",
            "lw\t$2,%gp_rel(savedInfoTracker+8)($gp)",
        ]

        mp = MaspsxProcessor(
            lines,
            sdata_limit=65536,
        )
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_gp_rel_store_with_offset(self):
        lines = [
            "	.comm	savedInfoTracker,16",
            "	sw	$4,savedInfoTracker+4",
            "	sw	$2,savedInfoTracker+8",
        ]
        expected_lines = [
            "sw\t$4,%gp_rel(savedInfoTracker+4)($gp)",
            "sw\t$2,%gp_rel(savedInfoTracker+8)($gp)",
        ]

        mp = MaspsxProcessor(
            lines,
            sdata_limit=65536,
        )
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_gp_rel_load_address_with_offset(self):
        lines = [
            "	.lcomm	Raziel,1464",
            "	la	$5,Raziel+1380",
        ]
        expected_lines = [
            "la\t$5,%gp_rel(Raziel+1380)($gp)",
        ]

        mp = MaspsxProcessor(
            lines,
            sdata_limit=65536,
            la_gprel=True,
        )
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:1])
