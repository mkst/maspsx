import unittest

from maspsx import MaspsxProcessor


from .util import strip_comments


class TestNop(unittest.TestCase):
    def test_nop_lw_div(self):
        """
        Ensure we place a nop betwen an lw/div pair that uses the same register
        Bug: https://github.com/mkst/maspsx/issues/31
        """
        lines = [
            "	lw	$3,0($5)",
            "	#nop",
            "	div	$3,$3,$7",
        ]
        expected_lines = [
            "lw\t$3,0($5)",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_lw_divu(self):
        """
        Ensure we place a nop betwen an lw/divu pair that uses the same register
        Bug: https://github.com/mkst/maspsx/issues/31
        """
        lines = [
            "	lw	$3,0($5)",
            "	#nop",
            "	divu	$3,$3,$7",
        ]
        expected_lines = [
            "lw\t$3,0($5)",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_div_mult(self):
        """
        mult and mflo/mhfi must be separated by at least two instructions
        Bug: https://github.com/mkst/maspsx/issues/31
        """
        lines = [
            "	div	$3,$3,$6",
            "",
            "	.loc	2 67",
            "	mult	$3,$5",
        ]
        expected_lines = [
            "div\t$zero,$3,$6",
            "mflo\t$3",  # expanded div
            "nop",
            "nop",
            "mult\t$3,$5",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:5])

    def test_simple_div_expansion_nop(self):
        """
        We need to handle loads/stores from registers used immediately after mflo/mfhi
        Bug: https://github.com/mkst/maspsx/issues/34
        """
        lines = [
            "	div	$2,$2,$3",
            "	sw	$2,112($18)",
        ]
        expected_lines = [
            "div\t$zero,$2,$3",
            "mflo\t$2",  # expanded div
            "nop",
            "sw\t$2,112($18)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_simple_div_expansion_no_nop(self):
        """
        Ensure we don't add a nop after div expansion if we dont need one
        Bug: https://github.com/mkst/maspsx/issues/34
        """
        lines = [
            "	div	$2,$2,$3",
            "",
            "	.loc	2 204",
            "	lh	$3,242($18)",
        ]
        expected_lines = [
            "div\t$zero,$2,$3",
            "mflo\t$2",  # expanded div
            "",
            ".loc\t2 204",
            "lh\t$3,242($18)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_simple_divu_expansion_no_nop(self):
        """
        Ensure we don't add a nop after divu expansion if we dont need one
        Bug: https://github.com/mkst/maspsx/issues/34
        """
        lines = [
            "	divu	$2,$2,$3",
            "",
            "	.loc	2 204",
            "	lh	$3,242($18)",
        ]
        expected_lines = [
            "divu\t$zero,$2,$3",
            "mflo\t$2",  # expanded div
            "",
            ".loc\t2 204",
            "lh\t$3,242($18)",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_nop_at_expansion_with_macro(self):
        """
        Ensure we can handle a macro that follows an $at expansion
        Bug: https://github.com/mkst/maspsx/issues/30
        """
        lines = [
            "	lw	$19,Cameras($2)",
            "",
            "	.loc	2 41",
            " #APP",
            "	lw	$12, 0( $19 );lw	$13, 4( $19 );ctc2	$12, $0;ctc2	$13, $1;lw	$12, 8( $19 );lw	$13, 12( $19 );lw	$14, 16( $19 );ctc2	$12, $2;ctc2	$13, $3;ctc2	$14, $4",
            " #NO_APP",
        ]
        expected_lines = [
            ".set\tnoat",
            "lui\t$at,%hi(Cameras)",
            "addu\t$at,$at,$2",
            "lw\t$19,%lo(Cameras)($at)",
            ".set\tat",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:6])

    def test_nop_with_macro(self):
        """
        Second example of macro requiring nop (no $at expansion)
        Bug: https://github.com/mkst/maspsx/issues/26
        """
        lines = [
            "	lw	$2,20($2)",
            "",
            "	#APP",
            "	lw	$12, 0( $2 );lw	$13, 4( $2 );ctc2	$12, $0;ctc2	$13, $1;lw	$12, 8( $2 );lw	$13, 12( $2 );lw	$14, 16( $2 );ctc2	$12, $2;ctc2	$13, $3;ctc2	$14, $4",
            "	#NO_APP",
        ]
        expected_lines = [
            "lw\t$2,20($2)",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_with_macro_with_addend_no_r_source(self):
        lines = [
            "	lw	$15,MRViewtrans_ptr",
            "	#APP",
            "	lw	$12, 0( $15 );lw	$13, 4( $15 );ctc2	$12, $0;ctc2	$13, $1;lw	$12, 8( $15 );lw	$13, 12( $15 );lw	$14, 16( $15 );ctc2	$12, $2;ctc2	$13, $3;ctc2	$14, $4",
            "	#NO_APP",
        ]
        expected_lines = [
            "lw	$15,MRViewtrans_ptr",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_with_macro_lwc2(self):
        lines = [
            "	lw	$7,48($fp)",
            "	#APP",
            "	lwc2	$0, 0( $7 );lwc2	$1, 4( $7 );lwc2	$2, 0( $2 );lwc2	$3, 4( $2 );lwc2	$4, 0( $3 );lwc2	$5, 4( $3 )",
        ]
        expected_lines = [
            "lw\t$7,48($fp)",
            "nop",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:2])

    def test_nop_lw_addu(self):
        """
        Ensure we place a nop betwen an lw/addu pair that uses the same register
        Bug: https://github.com/mkst/maspsx/issues/22
        """
        lines = [
            "	li	$19,0x1f800000		# 528482304",
            "	lw	$2,528482500		# 0x1f8000c4",
            "	#nop",
            "	addu	$3,$9,$2",
        ]
        expected_lines = [
            "li\t$19,0x1f800000",
            "lw\t$2,528482500",
            "nop",
            "addu\t$3,$9,$2",
        ]
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_nop_lw_lhu_omitted(self):
        """
        Ensure we don't add a nop between lw/lhu pair that doesnt reuse the register
        Bug: https://github.com/mkst/maspsx/issues/22
        """
        lines = [
            "	li	$19,0x1f800000		# 528482304",
            "	lw	$2,528482508",
            "",
            "	.loc	1 161",
            "LM102:",
            "	lhu	$11,16($sp)",
        ]
        expected_lines = strip_comments(lines)
        mp = MaspsxProcessor(lines)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_nop_gp_lw(self):
        """
        Ensure we place a nop between lw/sw pair that uses $gp
        Bug: https://github.com/mkst/maspsx/issues/20
        """
        lines = [
            "	.comm	UnkVar00,4",
            "	.comm	UnkVar01,4",
            "	li	$2,-1			# 0xffffffff",
            "	.set	volatile",
            "	sw	$2,UnkVar00",
            "	.set	novolatile",
            "	.set	volatile",
            "	lw	$2,UnkVar00",
            "	.set	novolatile",
            "	#nop",
            "	.set	volatile",
            "	sw	$2,UnkVar01",
        ]
        expected_lines = [
            "li\t$2,-1",
            "sw\t$2,%gp_rel(UnkVar00)($gp)",
            "lw\t$2,%gp_rel(UnkVar00)($gp)",
            "nop",  # DEBUG: next op loads from $2",
            "sw\t$2,%gp_rel(UnkVar01)($gp)",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=4, nop_gp=True)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:5])

    def test_nop_gp_lw_sw_pair(self):
        lines = [
            "	.comm	gameTrackerX,624",
            "	lw	$2,gameTrackerX+580",
            "$L15:",
            "	sw	$2,gameTrackerX+576",
        ]
        expected_lines = [
            "lw\t$2,%gp_rel(gameTrackerX+580)($gp)",
            "$L15:",
            "nop",
            "sw\t$2,%gp_rel(gameTrackerX+576)($gp)",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=1024, nop_gp=True)
        res = mp.process_lines()
        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:4])

    def test_nop_lh_sw_pair_uses_gp(self):
        """
        We need a nop betwen lh/sw pair when the sw uses $gp
        Bug: https://github.com/mkst/maspsx/issues/36
        """
        lines = [
            "	.comm	Map_water_height,2",
            "	lh	$2,2($2)",
            "	#nop",
            "	sw	$2,Map_water_height",
        ]
        expected_lines = [
            "lh\t$2,2($2)",
            "nop",
            "sw\t$2,%gp_rel(Map_water_height)($gp)",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=4, nop_gp=True)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines[:3])

    def test_nop_lh_sw_pair_no_gp(self):
        """
        We do not want a nop betwen lh/sw pair when the sw does not use $gp
        Bug: https://github.com/mkst/maspsx/issues/36
        """
        lines = [
            "	lh	$2,2($2)",
            "	#nop",
            "	sw	$2,Map_water_height",
        ]
        expected_lines = [
            "lh\t$2,2($2)",
            "sw\t$2,Map_water_height",
        ]
        mp = MaspsxProcessor(lines, sdata_limit=0)
        res = mp.process_lines()

        clean_lines = strip_comments(res)
        self.assertEqual(expected_lines, clean_lines)

    def test_nop_nor(self):
        """
        We want a nop between load/nor pair
        """
        lines = [
            "	lbu	$2,20($16)",
            "	nor	$2,$0,$2",
        ]
        expected_lines = [
            "lbu\t$2,20($16)",
            "nop",
            "nor\t$2,$0,$2",
        ]
        mp = MaspsxProcessor(lines)
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
