# [01] after/plain/mfc2/addu $9,$8,$10
	mfc2	$8,$4
	addu	$9,$8,$10
	nop
	nop

# [02] after/plain/mfc2/addu $8,$9,$10
	mfc2	$8,$4
	addu	$8,$9,$10
	nop
	nop

# [03] after/plain/mfc2/sw $8,0($2)
	mfc2	$8,$4
	sw	$8,0($2)
	nop
	nop

# [04] after/plain/mfc2/lw $9,0($8)
	mfc2	$8,$4
	lw	$9,0($8)
	nop
	nop

# [05] after/plain/mfc2/lw $8,0($2)
	mfc2	$8,$4
	lw	$8,0($2)
	nop
	nop

# [06] after/plain/mfc2/mtc2 $8,$5
	mfc2	$8,$4
	mtc2	$8,$5
	nop
	nop

# [07] after/plain/mfc2/ctc2 $8,$5
	mfc2	$8,$4
	ctc2	$8,$5
	nop
	nop

# [08] after/plain/mfc2/mfc2 $8,$5
	mfc2	$8,$4
	mfc2	$8,$5
	nop
	nop

# [09] after/plain/mfc2/cfc2 $8,$5
	mfc2	$8,$4
	cfc2	$8,$5
	nop
	nop

# [10] after/plain/mfc2/addu $9,$4,$10
	mfc2	$8,$4
	addu	$9,$4,$10
	nop
	nop

# [11] after/plain/mfc2/addu $9,$10,$11
	mfc2	$8,$4
	addu	$9,$10,$11
	nop
	nop

# [12] after/plain/mfc2/read-gap1
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [13] after/plain/mfc2/read-gap2
	mfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [14] after/plain/cfc2/addu $9,$8,$10
	cfc2	$8,$4
	addu	$9,$8,$10
	nop
	nop

# [15] after/plain/cfc2/addu $8,$9,$10
	cfc2	$8,$4
	addu	$8,$9,$10
	nop
	nop

# [16] after/plain/cfc2/sw $8,0($2)
	cfc2	$8,$4
	sw	$8,0($2)
	nop
	nop

# [17] after/plain/cfc2/lw $9,0($8)
	cfc2	$8,$4
	lw	$9,0($8)
	nop
	nop

# [18] after/plain/cfc2/lw $8,0($2)
	cfc2	$8,$4
	lw	$8,0($2)
	nop
	nop

# [19] after/plain/cfc2/mtc2 $8,$5
	cfc2	$8,$4
	mtc2	$8,$5
	nop
	nop

# [20] after/plain/cfc2/ctc2 $8,$5
	cfc2	$8,$4
	ctc2	$8,$5
	nop
	nop

# [21] after/plain/cfc2/mfc2 $8,$5
	cfc2	$8,$4
	mfc2	$8,$5
	nop
	nop

# [22] after/plain/cfc2/cfc2 $8,$5
	cfc2	$8,$4
	cfc2	$8,$5
	nop
	nop

# [23] after/plain/cfc2/addu $9,$4,$10
	cfc2	$8,$4
	addu	$9,$4,$10
	nop
	nop

# [24] after/plain/cfc2/addu $9,$10,$11
	cfc2	$8,$4
	addu	$9,$10,$11
	nop
	nop

# [25] after/plain/cfc2/read-gap1
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [26] after/plain/cfc2/read-gap2
	cfc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [27] after/plain/mtc2/addu $9,$8,$10
	mtc2	$8,$4
	addu	$9,$8,$10
	nop
	nop

# [28] after/plain/mtc2/addu $8,$9,$10
	mtc2	$8,$4
	addu	$8,$9,$10
	nop
	nop

# [29] after/plain/mtc2/sw $8,0($2)
	mtc2	$8,$4
	sw	$8,0($2)
	nop
	nop

# [30] after/plain/mtc2/lw $9,0($8)
	mtc2	$8,$4
	lw	$9,0($8)
	nop
	nop

# [31] after/plain/mtc2/lw $8,0($2)
	mtc2	$8,$4
	lw	$8,0($2)
	nop
	nop

# [32] after/plain/mtc2/mtc2 $8,$5
	mtc2	$8,$4
	mtc2	$8,$5
	nop
	nop

# [33] after/plain/mtc2/ctc2 $8,$5
	mtc2	$8,$4
	ctc2	$8,$5
	nop
	nop

# [34] after/plain/mtc2/mfc2 $8,$5
	mtc2	$8,$4
	mfc2	$8,$5
	nop
	nop

# [35] after/plain/mtc2/cfc2 $8,$5
	mtc2	$8,$4
	cfc2	$8,$5
	nop
	nop

# [36] after/plain/mtc2/addu $9,$4,$10
	mtc2	$8,$4
	addu	$9,$4,$10
	nop
	nop

# [37] after/plain/mtc2/addu $9,$10,$11
	mtc2	$8,$4
	addu	$9,$10,$11
	nop
	nop

# [38] after/plain/mtc2/read-gap1
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [39] after/plain/mtc2/read-gap2
	mtc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [40] after/plain/ctc2/addu $9,$8,$10
	ctc2	$8,$4
	addu	$9,$8,$10
	nop
	nop

# [41] after/plain/ctc2/addu $8,$9,$10
	ctc2	$8,$4
	addu	$8,$9,$10
	nop
	nop

# [42] after/plain/ctc2/sw $8,0($2)
	ctc2	$8,$4
	sw	$8,0($2)
	nop
	nop

# [43] after/plain/ctc2/lw $9,0($8)
	ctc2	$8,$4
	lw	$9,0($8)
	nop
	nop

# [44] after/plain/ctc2/lw $8,0($2)
	ctc2	$8,$4
	lw	$8,0($2)
	nop
	nop

# [45] after/plain/ctc2/mtc2 $8,$5
	ctc2	$8,$4
	mtc2	$8,$5
	nop
	nop

# [46] after/plain/ctc2/ctc2 $8,$5
	ctc2	$8,$4
	ctc2	$8,$5
	nop
	nop

# [47] after/plain/ctc2/mfc2 $8,$5
	ctc2	$8,$4
	mfc2	$8,$5
	nop
	nop

# [48] after/plain/ctc2/cfc2 $8,$5
	ctc2	$8,$4
	cfc2	$8,$5
	nop
	nop

# [49] after/plain/ctc2/addu $9,$4,$10
	ctc2	$8,$4
	addu	$9,$4,$10
	nop
	nop

# [50] after/plain/ctc2/addu $9,$10,$11
	ctc2	$8,$4
	addu	$9,$10,$11
	nop
	nop

# [51] after/plain/ctc2/read-gap1
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [52] after/plain/ctc2/read-gap2
	ctc2	$8,$4
	addu	$10,$11,$12
	addu	$10,$11,$12
	addu	$9,$8,$10
	nop
	nop

# [53] follow/mfc2/8,4/swc2 $8,0($2)
	mfc2	$8,$4
	swc2	$8,0($2)
	nop
	nop

# [54] follow/mfc2/8,4/lwc2 $8,0($2)
	mfc2	$8,$4
	lwc2	$8,0($2)
	nop
	nop

# [55] follow/mfc2/8,4/lwc2 $4,0($8)
	mfc2	$8,$4
	lwc2	$4,0($8)
	nop
	nop

# [56] follow/mfc2/8,4/swc2 $4,0($8)
	mfc2	$8,$4
	swc2	$4,0($8)
	nop
	nop

# [57] follow/cfc2/8,4/swc2 $8,0($2)
	cfc2	$8,$4
	swc2	$8,0($2)
	nop
	nop

# [58] follow/cfc2/8,4/lwc2 $8,0($2)
	cfc2	$8,$4
	lwc2	$8,0($2)
	nop
	nop

# [59] follow/cfc2/8,4/lwc2 $4,0($8)
	cfc2	$8,$4
	lwc2	$4,0($8)
	nop
	nop

# [60] follow/cfc2/8,4/swc2 $4,0($8)
	cfc2	$8,$4
	swc2	$4,0($8)
	nop
	nop

# [61] follow/mtc2/8,4/swc2 $8,0($2)
	mtc2	$8,$4
	swc2	$8,0($2)
	nop
	nop

# [62] follow/mtc2/8,4/lwc2 $8,0($2)
	mtc2	$8,$4
	lwc2	$8,0($2)
	nop
	nop

# [63] follow/mtc2/8,4/lwc2 $4,0($8)
	mtc2	$8,$4
	lwc2	$4,0($8)
	nop
	nop

# [64] follow/mtc2/8,4/swc2 $4,0($8)
	mtc2	$8,$4
	swc2	$4,0($8)
	nop
	nop

# [65] follow/ctc2/8,4/swc2 $8,0($2)
	ctc2	$8,$4
	swc2	$8,0($2)
	nop
	nop

# [66] follow/ctc2/8,4/lwc2 $8,0($2)
	ctc2	$8,$4
	lwc2	$8,0($2)
	nop
	nop

# [67] follow/ctc2/8,4/lwc2 $4,0($8)
	ctc2	$8,$4
	lwc2	$4,0($8)
	nop
	nop

# [68] follow/ctc2/8,4/swc2 $4,0($8)
	ctc2	$8,$4
	swc2	$4,0($8)
	nop
	nop

# [69] copload/lwc2/mfc2/4,8
	lwc2	$8,0($18)
	mfc2	$4,$8
	nop
	nop

# [70] copload/swc2/mfc2/4,8
	swc2	$8,0($18)
	mfc2	$4,$8
	nop
	nop

# [71] copload/lwc2/mfc2/8,4
	lwc2	$8,0($18)
	mfc2	$8,$4
	nop
	nop

# [72] copload/swc2/mfc2/8,4
	swc2	$8,0($18)
	mfc2	$8,$4
	nop
	nop

# [73] copload/lwc2/cfc2/4,8
	lwc2	$8,0($18)
	cfc2	$4,$8
	nop
	nop

# [74] copload/swc2/cfc2/4,8
	swc2	$8,0($18)
	cfc2	$4,$8
	nop
	nop

# [75] copload/lwc2/cfc2/8,4
	lwc2	$8,0($18)
	cfc2	$8,$4
	nop
	nop

# [76] copload/swc2/cfc2/8,4
	swc2	$8,0($18)
	cfc2	$8,$4
	nop
	nop

# [77] copload/lwc2/mtc2/4,8
	lwc2	$8,0($18)
	mtc2	$4,$8
	nop
	nop

# [78] copload/swc2/mtc2/4,8
	swc2	$8,0($18)
	mtc2	$4,$8
	nop
	nop

# [79] copload/lwc2/mtc2/8,4
	lwc2	$8,0($18)
	mtc2	$8,$4
	nop
	nop

# [80] copload/swc2/mtc2/8,4
	swc2	$8,0($18)
	mtc2	$8,$4
	nop
	nop

# [81] copload/lwc2/ctc2/4,8
	lwc2	$8,0($18)
	ctc2	$4,$8
	nop
	nop

# [82] copload/swc2/ctc2/4,8
	swc2	$8,0($18)
	ctc2	$4,$8
	nop
	nop

# [83] copload/lwc2/ctc2/8,4
	lwc2	$8,0($18)
	ctc2	$8,$4
	nop
	nop

# [84] copload/swc2/ctc2/8,4
	swc2	$8,0($18)
	ctc2	$8,$4
	nop
	nop

