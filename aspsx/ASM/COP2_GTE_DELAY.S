# [01] gte/plain/mfc2/addu $10,$11,$12/gap0
	mfc2	$8,$4
	cop2	0x0180001
	nop
	nop

# [02] gte/plain/mfc2/nop/gap1
	mfc2	$8,$4
	nop
	cop2	0x0180001
	nop
	nop

# [03] gte/plain/mfc2/addu $10,$11,$12/gap1
	mfc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [04] gte/plain/mfc2/nop/gap2
	mfc2	$8,$4
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [05] gte/plain/mfc2/addu $10,$11,$12/gap2
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [06] gte/plain/mfc2/nop/gap3
	mfc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [07] gte/plain/mfc2/addu $10,$11,$12/gap3
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [08] gte/plain/cfc2/addu $10,$11,$12/gap0
	cfc2	$8,$4
	cop2	0x0180001
	nop
	nop

# [09] gte/plain/cfc2/nop/gap1
	cfc2	$8,$4
	nop
	cop2	0x0180001
	nop
	nop

# [10] gte/plain/cfc2/addu $10,$11,$12/gap1
	cfc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [11] gte/plain/cfc2/nop/gap2
	cfc2	$8,$4
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [12] gte/plain/cfc2/addu $10,$11,$12/gap2
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [13] gte/plain/cfc2/nop/gap3
	cfc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [14] gte/plain/cfc2/addu $10,$11,$12/gap3
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [15] gte/plain/mtc2/addu $10,$11,$12/gap0
	mtc2	$8,$4
	cop2	0x0180001
	nop
	nop

# [16] gte/plain/mtc2/nop/gap1
	mtc2	$8,$4
	nop
	cop2	0x0180001
	nop
	nop

# [17] gte/plain/mtc2/addu $10,$11,$12/gap1
	mtc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [18] gte/plain/mtc2/nop/gap2
	mtc2	$8,$4
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [19] gte/plain/mtc2/addu $10,$11,$12/gap2
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [20] gte/plain/mtc2/nop/gap3
	mtc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [21] gte/plain/mtc2/addu $10,$11,$12/gap3
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [22] gte/plain/ctc2/addu $10,$11,$12/gap0
	ctc2	$8,$4
	cop2	0x0180001
	nop
	nop

# [23] gte/plain/ctc2/nop/gap1
	ctc2	$8,$4
	nop
	cop2	0x0180001
	nop
	nop

# [24] gte/plain/ctc2/addu $10,$11,$12/gap1
	ctc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [25] gte/plain/ctc2/nop/gap2
	ctc2	$8,$4
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [26] gte/plain/ctc2/addu $10,$11,$12/gap2
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [27] gte/plain/ctc2/nop/gap3
	ctc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	nop
	nop

# [28] gte/plain/ctc2/addu $10,$11,$12/gap3
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	nop
	nop

# [29] gte/noreorder/mfc2/addu $10,$11,$12/gap0
	.set	noreorder
	mfc2	$8,$4
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [30] gte/noreorder/mfc2/nop/gap1
	.set	noreorder
	mfc2	$8,$4
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [31] gte/noreorder/mfc2/addu $10,$11,$12/gap1
	.set	noreorder
	mfc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [32] gte/noreorder/mfc2/nop/gap2
	.set	noreorder
	mfc2	$8,$4
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [33] gte/noreorder/mfc2/addu $10,$11,$12/gap2
	.set	noreorder
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [34] gte/noreorder/mfc2/nop/gap3
	.set	noreorder
	mfc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [35] gte/noreorder/mfc2/addu $10,$11,$12/gap3
	.set	noreorder
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [36] gte/noreorder/cfc2/addu $10,$11,$12/gap0
	.set	noreorder
	cfc2	$8,$4
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [37] gte/noreorder/cfc2/nop/gap1
	.set	noreorder
	cfc2	$8,$4
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [38] gte/noreorder/cfc2/addu $10,$11,$12/gap1
	.set	noreorder
	cfc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [39] gte/noreorder/cfc2/nop/gap2
	.set	noreorder
	cfc2	$8,$4
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [40] gte/noreorder/cfc2/addu $10,$11,$12/gap2
	.set	noreorder
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [41] gte/noreorder/cfc2/nop/gap3
	.set	noreorder
	cfc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [42] gte/noreorder/cfc2/addu $10,$11,$12/gap3
	.set	noreorder
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [43] gte/noreorder/mtc2/addu $10,$11,$12/gap0
	.set	noreorder
	mtc2	$8,$4
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [44] gte/noreorder/mtc2/nop/gap1
	.set	noreorder
	mtc2	$8,$4
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [45] gte/noreorder/mtc2/addu $10,$11,$12/gap1
	.set	noreorder
	mtc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [46] gte/noreorder/mtc2/nop/gap2
	.set	noreorder
	mtc2	$8,$4
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [47] gte/noreorder/mtc2/addu $10,$11,$12/gap2
	.set	noreorder
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [48] gte/noreorder/mtc2/nop/gap3
	.set	noreorder
	mtc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [49] gte/noreorder/mtc2/addu $10,$11,$12/gap3
	.set	noreorder
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [50] gte/noreorder/ctc2/addu $10,$11,$12/gap0
	.set	noreorder
	ctc2	$8,$4
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [51] gte/noreorder/ctc2/nop/gap1
	.set	noreorder
	ctc2	$8,$4
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [52] gte/noreorder/ctc2/addu $10,$11,$12/gap1
	.set	noreorder
	ctc2	$8,$4
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [53] gte/noreorder/ctc2/nop/gap2
	.set	noreorder
	ctc2	$8,$4
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [54] gte/noreorder/ctc2/addu $10,$11,$12/gap2
	.set	noreorder
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [55] gte/noreorder/ctc2/nop/gap3
	.set	noreorder
	ctc2	$8,$4
	nop
	nop
	nop
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [56] gte/noreorder/ctc2/addu $10,$11,$12/gap3
	.set	noreorder
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$10,$11,$12
	cop2	0x0180001
	.set	reorder
	nop
	nop

# [57] gte/semicolon/mfc2/addu $10,$11,$12/gap0
	 #APP
	mfc2	$8,$4; cop2	0x0180001
	 #NO_APP
	nop
	nop

# [58] gte/semicolon/cfc2/addu $10,$11,$12/gap0
	 #APP
	cfc2	$8,$4; cop2	0x0180001
	 #NO_APP
	nop
	nop

# [59] gte/semicolon/mtc2/addu $10,$11,$12/gap0
	 #APP
	mtc2	$8,$4; cop2	0x0180001
	 #NO_APP
	nop
	nop

# [60] gte/semicolon/ctc2/addu $10,$11,$12/gap0
	 #APP
	ctc2	$8,$4; cop2	0x0180001
	 #NO_APP
	nop
	nop

# [61] copnext/plain/mfc2/cop2 0
	mfc2	$8,$4
	cop2	0
	nop
	nop

# [62] copnext/plain/mfc2/mfc2 $8,$4
	mfc2	$8,$4
	mfc2	$8,$4
	nop
	nop

# [63] copnext/plain/mfc2/cfc2 $8,$4
	mfc2	$8,$4
	cfc2	$8,$4
	nop
	nop

# [64] copnext/plain/cfc2/cop2 0
	cfc2	$8,$4
	cop2	0
	nop
	nop

# [65] copnext/plain/cfc2/mfc2 $8,$4
	cfc2	$8,$4
	mfc2	$8,$4
	nop
	nop

# [66] copnext/plain/cfc2/cfc2 $8,$4
	cfc2	$8,$4
	cfc2	$8,$4
	nop
	nop

# [67] copnext/plain/mtc2/cop2 0
	mtc2	$8,$4
	cop2	0
	nop
	nop

# [68] copnext/plain/mtc2/mfc2 $8,$4
	mtc2	$8,$4
	mfc2	$8,$4
	nop
	nop

# [69] copnext/plain/mtc2/cfc2 $8,$4
	mtc2	$8,$4
	cfc2	$8,$4
	nop
	nop

# [70] copnext/plain/ctc2/cop2 0
	ctc2	$8,$4
	cop2	0
	nop
	nop

# [71] copnext/plain/ctc2/mfc2 $8,$4
	ctc2	$8,$4
	mfc2	$8,$4
	nop
	nop

# [72] copnext/plain/ctc2/cfc2 $8,$4
	ctc2	$8,$4
	cfc2	$8,$4
	nop
	nop

