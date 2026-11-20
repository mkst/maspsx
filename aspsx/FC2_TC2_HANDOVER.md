# COP2 transfer behavior handover

## Investigation completed

See [COP2_BEHAVIOR.md](COP2_BEHAVIOR.md) for the characterized nop rules,
version tables, fixture links, reproduction commands, and remaining limits.
The investigation covers all 13 versions and preserves 382 probe blocks in
seven fixtures, plus the original `cfc2`/`mtc2` cases. Maspsx now implements
the characterized rules; [tests/test_cop2.py](../tests/test_cop2.py) runs the
unit specifications in normal discovery. The ASPSX suite also compares
Maspsx + GNU as directly with 117 reference source/version cases.

The notes below are the original handover and describe the earlier state.

## Goal

Characterize ASPSX behavior for the COP2 transfer instructions `mfc2`, `mtc2`,
`cfc2`, and `ctc2` across available versions. In particular, determine when
ASPSX inserts `nop`s around loads and transfers, then decide whether Maspsx
needs matching behavior and Maspsx-level unit tests.

The ASPSX fixtures are reference tests: they invoke ASPSX directly and compare
its object output. They do **not** invoke Maspsx. No COP2 behavior has been
implemented or tested in Maspsx as part of this work.

## Existing fixture: `cfc2`

The existing source is [`ASM/CFC2.S`](ASM/CFC2.S), with expected output in
[`fixtures/cfc2.yaml`](fixtures/cfc2.yaml). It covers `cfc2`, `mfc2`, and two
`ctc2` operand combinations. Each transfer follows `lhu $8,370($18)` and is
wrapped with the GCC inline-assembly markers used by the original input.

Observed output groups:

| ASPSX versions | Observed `nop` behavior in this fixture |
| --- | --- |
| 1.05, 1.07, 2.05, 2.08 | A `nop` follows each `lhu` before the COP2 transfer. |
| 2.21, 2.56, 2.67, 2.77, 2.79, 2.81, 2.86 | No `nop` before the first three transfers; a `nop` appears before the last `ctc2 $8,$4`. |
| 2.30, 2.34 | A `nop` appears before `ctc2 $4,$8`; no `nop` appears before the last `ctc2 $8,$4`. |

These are observations about this exact sequence, not yet a complete hazard
model. The difference between the 2.21 and 2.30 groups is especially worth
isolating with register-dependency probes.

## New `mtc2` characterization fixture

[`ASM/MTC2.S`](ASM/MTC2.S) and [`fixtures/mtc2.yaml`](fixtures/mtc2.yaml) cover
three `mtc2` transfers for ASPSX 2.56 through 2.86. All six Wibo-backed cases
passed.

The probe shows the same output across those versions:

```text
lhu $8,370($18)
mtc2 $4,$8       # no nop: source GPR is $4
lhu $8,370($18)
nop
mtc2 $8,$4       # nop after the load of source GPR $8
lw $8,0($2)
nop
mtc2 $8,$31      # nop after the load of source GPR $8
```

The raw expected words are recorded in the YAML fixture. This fixture currently
covers only 2.56+; older versions still need comparison.

## Probe and harness notes

- The installed version map is in [`util.py`](util.py): Daze runs 1.05 through
  2.34, and Wibo runs 2.56 through 2.86.
- ASPSX source files need DOS CRLF line endings. Use tabs/spacing and
  `#APP`/`#NO_APP` markers consistent with `CFC2.S` when probing.
- Keep probe inputs focused. An earlier combined probe mixed directives and
  unsupported mnemonics, so its failures on old versions were not useful
  evidence.
- COP2 transfer operands in the successful probes use numeric register names,
  such as `$8` and `$31`. Bare `31` as the second operand was rejected; the
  `$zero` spelling was also rejected in one probe, so do not treat those failed
  forms as evidence about instruction support without isolating syntax first.
- The harness expects the parser at `binaries/psyq-obj-parser` relative to this
  directory.
- In the sandboxed laptop session, Daze sometimes printed
  `Failed to create stream fd: Operation not permitted`. The full 203-case
  baseline had passed in a non-sandboxed run before the new fixtures were
  added, so this was an environment constraint rather than an ASPSX mismatch.

Run the relevant ASPSX fixtures from this directory:

```sh
python3 -m unittest -v -k test_cfc2_
python3 -m unittest -v -k test_mtc2_
```

Or use the parallel runner:

```sh
python3 run_parallel.py --case cfc2 --jobs 1
python3 run_parallel.py --case mtc2 --jobs 1
```

The root Maspsx unit suite is separate:

```sh
cd ..
python3 -m unittest
```

## Suggested next probes

1. Extend or add a fixture for `mtc2` on Daze-backed versions, especially
   2.05, 2.08, 2.21, 2.30, and 2.34. Preserve the input formatting from the
   existing fixture.
2. Probe all four transfers after a load to the same GPR and to a different
   GPR. Vary `lw` and `lhu`, source/destination GPRs, and zero, one, or two
   intervening instructions.
3. Test operand/register boundaries and aliases separately from scheduling.
   Keep a successful control case beside each candidate syntax form.
4. Compare each version's exact output and errors. Only after the behavior is
   characterized should a Maspsx transformation or Maspsx unit test be added.

## Current-workspace state

The recent `li` range work and the COP2 fixture files are uncommitted in the
workspace. The last complete Maspsx unit run passed 168 tests. The six
Wibo-backed `mtc2` fixture cases and the ASPSX 2.56 `li` fixture case passed.
The full ASPSX matrix had passed 203 cases before these fixture additions; it
has not been rerun as a complete matrix since then.
