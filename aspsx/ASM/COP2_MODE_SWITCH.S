# [01] reorder -> noreorder: load -> mfc2
	.set	reorder
	lw	$8,0($18)
	.set	noreorder
	mfc2	$8,$4
	nop
	nop

# [02] reorder -> noreorder: mfc2 -> GPR read
	.set	reorder
	mfc2	$8,$4
	.set	noreorder
	addu	$9,$8,$10
	nop
	nop

# [03] reorder -> noreorder: load -> cfc2
	.set	reorder
	lw	$8,0($18)
	.set	noreorder
	cfc2	$8,$4
	nop
	nop

# [04] reorder -> noreorder: cfc2 -> GPR read
	.set	reorder
	cfc2	$8,$4
	.set	noreorder
	addu	$9,$8,$10
	nop
	nop

# [05] reorder -> noreorder: load -> mtc2
	.set	reorder
	lw	$8,0($18)
	.set	noreorder
	mtc2	$8,$4
	nop
	nop

# [06] reorder -> noreorder: mtc2 -> GPR read
	.set	reorder
	mtc2	$8,$4
	.set	noreorder
	addu	$9,$8,$10
	nop
	nop

# [07] reorder -> noreorder: load -> ctc2
	.set	reorder
	lw	$8,0($18)
	.set	noreorder
	ctc2	$8,$4
	nop
	nop

# [08] reorder -> noreorder: ctc2 -> GPR read
	.set	reorder
	ctc2	$8,$4
	.set	noreorder
	addu	$9,$8,$10
	nop
	nop

# [09] noreorder -> reorder: load -> mfc2
	.set	noreorder
	lw	$8,0($18)
	.set	reorder
	mfc2	$8,$4
	nop
	nop

# [10] noreorder -> reorder: mfc2 -> GPR read
	.set	noreorder
	mfc2	$8,$4
	.set	reorder
	addu	$9,$8,$10
	nop
	nop

# [11] noreorder -> reorder: load -> cfc2
	.set	noreorder
	lw	$8,0($18)
	.set	reorder
	cfc2	$8,$4
	nop
	nop

# [12] noreorder -> reorder: cfc2 -> GPR read
	.set	noreorder
	cfc2	$8,$4
	.set	reorder
	addu	$9,$8,$10
	nop
	nop

# [13] noreorder -> reorder: load -> mtc2
	.set	noreorder
	lw	$8,0($18)
	.set	reorder
	mtc2	$8,$4
	nop
	nop

# [14] noreorder -> reorder: mtc2 -> GPR read
	.set	noreorder
	mtc2	$8,$4
	.set	reorder
	addu	$9,$8,$10
	nop
	nop

# [15] noreorder -> reorder: load -> ctc2
	.set	noreorder
	lw	$8,0($18)
	.set	reorder
	ctc2	$8,$4
	nop
	nop

# [16] noreorder -> reorder: ctc2 -> GPR read
	.set	noreorder
	ctc2	$8,$4
	.set	reorder
	addu	$9,$8,$10
	nop
	nop

