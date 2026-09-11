	.file	1 "labels.c"
	.text
	.set	reorder
	lw	$9,188($sp)
$L1:
$L2:
	lw	$2,40($9)
	.set	noreorder
	beq	$0,$0,$L1
	nop
	beq	$0,$0,$L2
	nop
