# [01] mtc2 / li	$10,1
	mtc2	$8,$4
	li	$10,1
	cop2	0x0180001
	nop
	nop

# [02] mtc2 / li	$10,-65536
	mtc2	$8,$4
	li	$10,-65536
	cop2	0x0180001
	nop
	nop

# [03] mtc2 / li	$10,-2147483648
	mtc2	$8,$4
	li	$10,-2147483648
	cop2	0x0180001
	nop
	nop

# [04] mtc2 / li	$10,0x10000
	mtc2	$8,$4
	li	$10,0x10000
	cop2	0x0180001
	nop
	nop

# [05] mtc2 / li	$10,0x12345678
	mtc2	$8,$4
	li	$10,0x12345678
	cop2	0x0180001
	nop
	nop

# [06] mtc2 / la	$10,0x10000
	mtc2	$8,$4
	la	$10,0x10000
	cop2	0x0180001
	nop
	nop

# [07] mtc2 / la	$10,0x12345678
	mtc2	$8,$4
	la	$10,0x12345678
	cop2	0x0180001
	nop
	nop

# [08] mtc2 / lw	$10,0x10000($18)
	mtc2	$8,$4
	lw	$10,0x10000($18)
	cop2	0x0180001
	nop
	nop

# [09] mtc2 / lw	$10,symbol
	mtc2	$8,$4
	lw	$10,symbol
	cop2	0x0180001
	nop
	nop

# [10] ctc2 / li	$10,1
	ctc2	$8,$4
	li	$10,1
	cop2	0x0180001
	nop
	nop

# [11] ctc2 / li	$10,-65536
	ctc2	$8,$4
	li	$10,-65536
	cop2	0x0180001
	nop
	nop

# [12] ctc2 / li	$10,-2147483648
	ctc2	$8,$4
	li	$10,-2147483648
	cop2	0x0180001
	nop
	nop

# [13] ctc2 / li	$10,0x10000
	ctc2	$8,$4
	li	$10,0x10000
	cop2	0x0180001
	nop
	nop

# [14] ctc2 / li	$10,0x12345678
	ctc2	$8,$4
	li	$10,0x12345678
	cop2	0x0180001
	nop
	nop

# [15] ctc2 / la	$10,0x10000
	ctc2	$8,$4
	la	$10,0x10000
	cop2	0x0180001
	nop
	nop

# [16] ctc2 / la	$10,0x12345678
	ctc2	$8,$4
	la	$10,0x12345678
	cop2	0x0180001
	nop
	nop

# [17] ctc2 / lw	$10,0x10000($18)
	ctc2	$8,$4
	lw	$10,0x10000($18)
	cop2	0x0180001
	nop
	nop

# [18] ctc2 / lw	$10,symbol
	ctc2	$8,$4
	lw	$10,symbol
	cop2	0x0180001
	nop
	nop

