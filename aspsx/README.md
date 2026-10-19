# ASPSX Tests

The idea of this directory is to leverage unit tests to catalog the various differences between ASPSX versions.


## Running the tests

Note that this test suite is designed for Linux x86_64 and does not support running on other platforms.

**Install Daze & Wibo**
[Daze](https://github.com/mkst/daze) runs the 16-bit ASPSX versions, and [Wibo](https://github.com/decompals/wibo) runs the 32-bit versions. Install them from the [Daze releases](https://github.com/mkst/daze/releases/latest) and [Wibo releases](https://github.com/decompals/wibo/releases), and make sure `daze` and `wibo` are available on your `PATH`.

**Fetch ASPSX binaries**

```sh
mkdir -p binaries
wget https://github.com/mkst/maspsx/releases/download/aspsx/aspsx-binaries.tar.gz
tar xvzf aspsx-binaries.tar.gz -C binaries
rm aspsx-binaries.tar.gz
```

**Fetch `psyq-obj-parser`**

`psyq-obj-parser` is a utility for parsing PsyQ objects (produced by ASPSX).
It is maintained in the [`pcsx-redux`](https://github.com/grumpycoders/pcsx-redux) project
and can be built from source if needed.

Alternatively, a pre-built version of the binary can be found in the same
location as the ASPSX binaries.

```sh
wget https://github.com/mkst/maspsx/releases/download/aspsx/psyq-obj-parser binaries/psyq-obj-parser
chmod +x binaries/psyq-obj-parser
```

**Run the tests**

```sh
python3 -m pip install -r requirements.txt
python3 check_environment.py
python3 -m unittest
```

The active assembler cases are data-driven: each source/version pair is
generated as its own unittest case. To run every ASPSX version for one
fixture, use unittest's `-k` substring filter:

```sh
python3 -m unittest -v -k test_gp_
```

To run one fixture/version pair, use its generated test name:

```sh
python3 -m unittest test_matrix.TestAssemblerMatrix.test_gp_2_67
```

The generated naming pattern is `test_<fixture>_<version>`. For example:

```sh
python3 -m unittest -v test_matrix.TestAssemblerMatrix.test_lwlw_2_34
python3 -m unittest -v test_matrix.TestAssemblerMatrix.test_v0_at_2_08
```

Fixture data lives in one YAML file per feature under `fixtures/`. Each file
contains the source assembly path, optional assembler flags, and expected
section contents keyed directly by ASPSX version.

Adding a case normally only requires editing the relevant YAML file.
Identical expected sequences use YAML anchors and aliases;
keep a literal sequence when a version differs in even one word.

Expected assembly code has inline comments generated from `spimdisasm disasmdis
--pseudos`, so the encoded output and readable assembly can be reviewed
together.

For the faster isolated matrix runner, use bounded parallel workers. It
reuses the existing fixtures and keeps output deterministic; `--jobs 1` is a
useful debugging mode.

```sh
python3 run_parallel.py
python3 run_parallel.py --jobs 1 --case gp:2.67 --verbose
```

Assembler failures include the command and captured diagnostics. Assembly
mismatches include raw words and decoded instructions.
