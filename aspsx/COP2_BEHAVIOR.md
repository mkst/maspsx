# ASPSX COP2 transfer nop behavior

This records **assembler output**, not the delays that PlayStation hardware
requires. ASPSX sometimes inserts unnecessary nops and sometimes omits a
potential dependency. Matching ASPSX means preserving those distinctions.
Maspsx now implements these fixture-backed rules through a small COP2-only
helper in its existing processing loop; see the implementation notes below.

All 13 versions in `util.ASPSX_RUNNER_LOOKUP` were executed locally with their
configured Daze/Wibo runners. Unless stated otherwise, the tables describe
adjacent instructions in the default reorder mode, numeric register spellings,
and no extra assembler flags.

## Version groups

| Group | Versions tested |
| --- | --- |
| A | 1.05, 1.07, 2.05, 2.08 |
| B | 2.21 |
| C | 2.30, 2.34 |
| D | 2.56, 2.67, 2.77, 2.79, 2.81, 2.86 |

The checked sequences have identical output within each group. These are
observed release boundaries; the repository has no versions between several
of them, so the exact release introducing a change is unknown.

## Loads immediately before a transfer

For `load $r,...` followed by `transfer $g,$c`, the following condition inserts
**one** nop between the instructions. Here `$g` is the first operand (GPR),
`$c` is the second operand (COP2 register), and `r` is nonzero. A comparison
with `c` below compares register **numbers across different register banks**.

| Transfer | A | B | C | D |
| --- | --- | --- | --- | --- |
| `mfc2 $g,$c` | `r == g OR r == c` | `r == g` | never | never |
| `cfc2 $g,$c` | `r == g OR r == c` | `r == g` | never | never |
| `mtc2 $g,$c` | `r == g OR r == c` | `r == g` | `r == g` | `r == g` |
| `ctc2 $g,$c` | `r == g OR r == c` | `r == g` | **`r == c`** | `r == g` |

These rules held for each of `lb`, `lbu`, `lh`, `lhu`, `lw`, `lwl`, and `lwr`.
The operand pairs `(4,8)`, `(8,4)`, `(8,8)`, and `(4,5)` distinguish a match
on the COP2 operand, the GPR operand, both, and neither after a load into `$8`.

For example:

```asm
lhu  $8,370($18)
ctc2 $4,$8          # nop before ctc2 in A and C; none in B or D

lhu  $8,370($18)
ctc2 $8,$4          # nop before ctc2 in A, B, D; none in C

lhu  $8,370($18)
mfc2 $8,$4          # nop in A/B despite overwriting the loaded GPR; none in C/D
```

One or two intervening independent `addu` instructions eliminate the nop in
all groups. A load into numeric `$0` does not trigger a nop, including when a
transfer operand is `$0`. Numeric GPR/COP2 pairs were also checked at `$2`
and `$31`; the same comparison rules apply. None of the paired `lwc2` or
`swc2` predecessors in the fixture creates a delay before the transfer,
including when its COP2 register matches a transfer operand.

Evidence: [load fixture](fixtures/cop2_load_delay.yaml),
[source](ASM/COP2_LOAD_DELAY.S), [register fixture](fixtures/cop2_registers.yaml),
and `copload` blocks in the [read fixture](fixtures/cop2_read_delay.yaml).
The original [cfc2 fixture](fixtures/cfc2.yaml) is explained by this table;
the [mtc2 fixture](fixtures/mtc2.yaml) now covers all 13 versions.

## Instructions immediately after a transfer

`mfc2 $g,$c` establishes a one-instruction GPR delay in every tested version.
`cfc2 $g,$c` establishes such a delay only in C/D. Neither `mtc2` nor `ctc2`
establishes a corresponding GPR delay in these probes.

The dependency test on the following instruction also changes:

| Following instruction, after `mfc2 $8,$4` | A | B | C | D |
| --- | --- | --- | --- | --- |
| `addu $9,$8,$10` (reads GPR) | 1 | 1 | 1 | 1 |
| `addu $8,$9,$10` (only overwrites GPR) | 1 | 1 | 0 | 0 |
| `sw $8,0($2)` | 1 | 1 | 1 | 1 |
| `lw $9,0($8)` (uses GPR as address) | 1 | 1 | 1 | 1 |
| `lw $8,0($2)` (only overwrites GPR) | 1 | 1 | 0 | 0 |
| `mtc2 $8,$5` | 1 | 1 | 1 | 1 |
| `ctc2 $8,$5` | 1 | 1 | **0** | 1 |
| `mfc2 $8,$5` or `cfc2 $8,$5` | 1 | 1 | 0 | 0 |
| `lwc2 $8,0($2)` (COP2 register-number match) | 1 | 0 | 0 | 0 |
| `swc2 $8,0($2)` (COP2 register-number match) | 1 | 0 | **1** | 0 |
| `lwc2 $4,0($8)` or `swc2 $4,0($8)` (GPR base) | 1 | 1 | 1 | 1 |
| `addu $9,$4,$10` (reads number of producer's COP2 operand) | 0 | 0 | 0 | 0 |
| `addu $9,$10,$11` (independent) | 0 | 0 | 0 | 0 |

Numbers are **inserted nops between the two instructions**. For a `cfc2`
producer, all entries are zero in A/B; in C/D they match the corresponding
`mfc2` entries. Thus C's unusual `ctc2` operand test applies after a COP2
read as well as after an ordinary memory load. The `swc2` anomaly in C is
another comparison between registers from different banks.

One independent instruction between a delayed read and a consumer is enough;
two also work. Reading the number of the producer's COP2 operand does not
itself trigger a GPR delay. The fixture also checks reading that
other number after each transfer to distinguish the two operand roles.

Evidence: [read fixture](fixtures/cop2_read_delay.yaml) and
[source](ASM/COP2_READ_DELAY.S). The special `swc2`/`lwc2` comparisons are in
the `follow` blocks; they should not be generalized from ordinary GPR stores.

## Transfer followed by a COP2 command

A separate rule applies to `mtc2`/`ctc2` before `cop2` in D:
ASPSX inserts enough nops to place **two instructions between the transfer
and the command**.

| Sequence before `cop2 0x0180001` | A/B/C added nops | D added nops |
| --- | --- | --- |
| `mtc2 $8,$4` or `ctc2 $8,$4` immediately before command | 0 | 2 |
| Transfer, one independent `addu` | 0 | 1 |
| Transfer, two independent `addu` instructions | 0 | 0 |
| Transfer, three independent `addu` instructions | 0 | 0 |
| Transfer, one explicit `nop` | 0 | 1 |
| Transfer, two or three explicit `nop`s | 0 | 0 |
| `mfc2 $8,$4` or `cfc2 $8,$4` immediately before command | 0 | 0 |

The same immediate-transfer distinction holds for the literal `cop2 0`.
This spacing remains active under **`.set noreorder`**, as well as inside
`#APP`/`#NO_APP` and semicolon-separated input. There is no universal
padding after a write: the checked `mtc2`/`ctc2` to `mfc2`/`cfc2` pairs do
not receive these two nops, even with matching COP2 register numbers.

```asm
# D, including under .set noreorder:
mtc2 $8,$4
nop                    # inserted
nop                    # inserted
cop2 0x0180001
```

Evidence: [command-delay fixture](fixtures/cop2_gte_delay.yaml) and
[source](ASM/COP2_GTE_DELAY.S). These observations concern the assembler's
`cop2` instruction handling, not a complete model of GTE operation latency.
The `rtps` mnemonic was rejected in isolated syntax checks on all versions;
the fixtures use the accepted numeric `cop2` form.

## Scheduling controls and inline-assembly markers

| Setting | Observed behavior |
| --- | --- |
| Default reorder mode | Rules above apply. |
| `#APP`/`#NO_APP` around transfer alone or whole pair | Same output as without markers. |
| Semicolon-separated instructions inside `#APP` | Same output when a space follows each semicolon. |
| `.set noreorder`: load before transfer | No inserted load-delay nop in any tested version. |
| `.set noreorder`: `mfc2` before GPR consumer | No inserted GPR-delay nop in any tested version. |
| `.set noreorder`: `cfc2` before GPR consumer | A/B insert none; **C/D still insert the delay nop** before the tested dependent `addu`, `sw`, address-dependent `lw`, `mtc2`, and (in D) `ctc2` consumers. |
| `.set noreorder`: `mtc2`/`ctc2` before `cop2` | D still fills the two intervening slots; A/B/C insert none. |

The retained `cfc2` nop under noreorder is reproducible; do not infer that
all COP2 scheduling is disabled by this directive. Conversely, `#APP` is a
comment marker and does not act like `.set noreorder` in these tests.

Evidence: [mode fixture](fixtures/cop2_modes.yaml),
[source](ASM/COP2_MODES.S), and the noreorder/semicolon blocks in the
command-delay fixture.

ASPSX 1.05/1.07 reject a second mnemonic immediately following `;` without
whitespace. An isolated `lw ...;mtc2 ...` failed, while `lw ...; mtc2 ...`
and `lw ...;\tmtc2 ...` passed. All later versions accepted the no-whitespace
form too. This is a syntax distinction, not missing instruction support;
the retained fixtures use the form accepted by every version. Source files
use DOS CRLF line endings throughout.

## Reproducing the evidence

Seven source/YAML pairs preserve **382 probe blocks** across all 13
versions: 104 load blocks, 84 read blocks, 64 mode blocks, 72 command-delay
blocks, 24 register blocks, 16 mode-switch blocks, and 18 expansion-gap blocks.
The latter two fixtures are [mode switches](fixtures/cop2_mode_switch.yaml)
and [expansion gaps](fixtures/cop2_expansion_gap.yaml). A producer retains
the source reorder mode at which it was encountered; a later mode switch
does not change its pending delay. Wide immediates and expanded memory loads
can fill both command-delay slots without extra nops. Each source block ends with **two explicit
separator nops** so one probe cannot leave a pending delay for the next.
Matching numbered block comments in the YAML identify the output; the final
two nops in each block are annotated as explicit separators. Other nops in
the output are assembler insertions, except explicit gap nops visible in
that block's source. Identical whole-version outputs use YAML aliases.

From the repository root:

```sh
source venv/bin/activate
cd aspsx
python -m unittest -v -k test_cop2_
python -m unittest -v -k test_mtc2_
python -m unittest -v -k test_cfc2_
python -m unittest
```

The new fixtures were assembled again through unittest after their expected
words were recorded. Their pass/fail checks compare complete raw instruction
sequences, including inserted nops and explicit separators; disassembly
comments are only explanatory. The existing fixture harness is unchanged.

## Maspsx implementation and validation

[tests/test_cop2.py](../tests/test_cop2.py) promotes the original failing
specifications into normal discovery and extends them across all 13 versions.
It covers operand selection, read and overwrite delays, COP2 memory consumers,
source mode switches, inline macros, zero, explicit nops, expanded instructions,
and CLI version forwarding.

The production changes are localized:

- `AspsxVersionConfig.cop2_version` passes the requested version to the processor;
  the default COP2 behavior is the latest available version, 2.86.
- `_cop2_uses_reg` contains the version-dependent operand comparisons.
- `_handle_cop2` examines each chunk returned by `process_line`. It remembers
  the previous instruction's opcode, first operand and source reorder mode,
  plus the remaining transfer-to-command slots. It inspects semicolon-separated
  instructions and preserves emitted lines unless inserting a nop.
- The existing load lookahead defers COP2 decisions to that helper, avoiding
  duplicate insertion. Ordinary load scheduling and branch handling keep their
  existing paths. Generated `.set noreorder` lines do not change source mode.

Instruction widths are counted after Maspsx expansion, including explicit nops.
For literal `li`/`la` and remaining memory macros deferred to GNU as, the helper
also accounts for one-word versus multiword output when a command delay is
pending. It only needs to distinguish one word from at least two.

[aspsx/test_cop2_maspsx.py](test_cop2_maspsx.py) additionally checks **117
source/version cases** by feeding Maspsx output to GNU as (`-EL -march=r3000
-G0`) and comparing the resulting raw text bytes with the ASPSX fixtures.
Only GNU as's trailing section alignment padding is excluded. This test skips
if `mips-linux-gnu-as` is unavailable. Run it from `aspsx/`:

```sh
python -m unittest test_cop2_maspsx
```

Validation:

- Root default suite: **181 tests passed**.
- Maspsx + GNU as: **117 reference cases passed**, covering all 13 versions.
- Full ASPSX suite: **328 tests passed**, including all **307 ASPSX
  fixture cases**, the GNU comparison test, and the endianness regression test.
- Changed Python files formatted with Black and checked with `black --check`.

The former failure in
`test_util.TestAssemblyDiff.test_includes_raw_words_and_disassembly` is fixed.
The helper now converts numeric instruction words with `int(word, 16)` instead
of interpreting their text as bytes through spimdisasm's global endianness.
The regression test exercises both big- and little-endian settings and checks
that decoding leaves the setting unchanged. The standalone reproduction still
demonstrates the upstream global-state interaction, but the harness no longer
depends on that parsing behavior.

## Boundaries and open questions

This establishes rules for the sequences above, not every possible input.
Further work could examine branches/delay slots, labels and section switches,
assembler optimization flags, additional symbolic/expanded operands, additional COP2
command encodings and register-specific GTE semantics, and aliases for the
numeric registers. Numeric `$0` works in the isolated tests; that does not
establish whether the `$zero` alias works. Register `$1` was excluded from
boundary fixtures because its use without `.set noat` produces warnings
and nonzero exits in some versions.

Whether the anomalies arise from shared internal operand classifications is
an inference. The observed output establishes the compatibility requirements
without relying on that implementation theory. No claim is made that the
older or newer output is the hardware-correct schedule.

Older ASPSX versions also have independent pseudo-op encoding differences
for small literal `la` and some unsigned `li` spellings. Their existing Maspsx
expansion rules are outside this scheduling change; the expansion-gap fixtures
use forms whose encodings match as well as checking nop placement.
