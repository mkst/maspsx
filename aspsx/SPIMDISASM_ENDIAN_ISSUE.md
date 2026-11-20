Title: Elf32File changes global endianness used by subsequent getWordFromStr calls

Using spimdisasm 1.42.4 and rabbitizer 1.16.2, parsing a little-endian ELF
changes `GlobalConfig.ENDIAN` for subsequent calls to
`DisasmdisInternals.getWordFromStr`. This creates an order dependency when
using these helpers in the same process. No concurrency is involved.

The attached `repro_spimdisasm_endian.py` constructs an empty ELF32/MIPS object
in memory, so it needs no assembler, external files, or project-specific code.

```sh
python -m pip install spimdisasm==1.42.4 rabbitizer==1.16.2
python repro_spimdisasm_endian.py
```

Observed output:

```text
spimdisasm 1.42.4, rabbitizer 1.16.2
Before ELF parsing: ENDIAN=BIG, word=0x00220821
  addu        $at, $at, $v0
After ELF parsing: ENDIAN=LITTLE, word=0x21082200
  addi        $t0, $t0, 0x2200
Direct integer decoding: addu        $at, $at, $v0
```

Is this global configuration mutation an intended part of the `Elf32File`
API? If so, is there a recommended way to isolate endianness when embedding
spimdisasm in a process that handles multiple inputs, or could that behavior
be documented?

I understand that `getWordFromStr` treats its input as hex bytes and therefore
may intentionally honor the configured endianness. Our original use passed
an already formatted numeric instruction word, for which `int(text, 16)` is
the appropriate workaround. This report concerns the global side effect of
ELF parsing and the resulting order dependency, rather than an incorrect
Rabbitizer decode or a claim that hex-byte parsing should ignore endianness.
