# maspsx AKA "Modern ASPSX"

The goal of this project is to produce assembly code that compiles to an equivalent object using GNU as, as to assembly code that is passed to ASPSX.EXE + psyq-obj-parser.

ASPSX.EXE does not appear to do very much in terms of code optimisation, therefore the transformations ought to be straightforward.

## Usage

`maspsx` supports the following arguments:

- `--run-assembler`; execute `mips-linux-gnu-as`
- `--gnu-as-path`; if `mips-linux-gnu-as` isn't on your path, or you want to use a different assembler
- `--no-macro-inc`; do not add `include "macro.inc"` to output
- `--expand-div`; if you need to expand `div`, `divu` and `rem` ops
