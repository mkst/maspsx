# maspsx AKA "Modern ASPSX"

The goal of `maspsx` is to facilitate the replacement of the combination of `ASPSX.EXE` + [psyq-obj-parser](https://github.com/grumpycoders/pcsx-redux/tree/main/tools/psyq-obj-parser) when attempting to generate byte-perfect ELF objects.

`maspsx` takes the assembly code output of `gcc` and massages it such that it can be assembled via GNU `as` to the equivalent object as what the original PSYQ SDK would create.

`ASPSX` does not appear to do very much in terms of code *optimisation*, therefore the belief is that this will be a straightforward process.

There are a number of reasons why using `maspsx` with GNU `as` is preferable to the original toolchain:
 - No need to run 16-bit DOS or 32-bit Windows applications
   - Native, vanilla, [gcc](https://github.com/decompals/old-gcc) versions make dosemu2 and wine unnecessary.
 - Decomp tooling expects ELF objects
 - Support for line numbers in diff!
   - Pass `-gcoff` to gcc to get line numbers in [asm-differ](https://github.com/simonlindholm/asm-differ)


## Usage

`maspsx` supports the following arguments:

### `--run-assembler`
The default behaviour of `maspsx` is to write the output to stdout, by passing `--run-assembler`, `maspsx` will run `mips-linux-gnu-as` directly.

### `--gnu-as-path`
If `mips-linux-gnu-as` isn't on your path, or you want to use a different assembler (e.g. `mipsel-linux-gnu-as`), specify the full path here.

### `--dont-force-G0`
Current understanding is that `-G0` needs to be passed to GNU `as` in order to get correct behaviour. If you need to pass a non-zero value for `-G` to the GNU assembler, use this flag.

### `--expand-div`
If you need `maspsx` to expand `div/divu` and `rem/remu` ops, pass `--expand-div` to `maspsx`. There is already handling for partial div expansion (i.e. where `-0` was passed to `ASPSX.EXE`).

### `--no-macro-inc`
By default, `maspsx` adds a `include "macro.inc"` statement to the output, pass this flag to suppress it.

### `--aspsx-version`
**EXPERIMENTAL** There are slight nuances in `nop` placement across `ASPSX` versions. In order to emulate the correct behaviour, pass the `ASPSX` version to `maspsx`, e.g. `--aspsx-version=2.78`.

### `-G`
**EXPERIMENTAL** If your project uses `$gp`, maspsx needs to be explicitly passed a non-zero value for `-G`.


## Examples

Projects that use `maspsx` include:
  - [Castlevania: Symphony of the Night Decompilation](https://github.com/Xeeynamo/sotn-decomp)
  - [open-ribbon](https://github.com/open-ribbon/open-ribbon)
  - [Evo's Space Adventures](https://github.com/mkst/esa)


## Bugs

This project is a work-in-progress. If you encounter scenarios where `maspsx` output differs from the original PSYQ toolchain please create a [GitHub Issue](https://github.com/mkst/maspsx/issues/new) - ideally with a link to a [decomp.me](https://decomp.me/) scratch that demonstrates the problem.
