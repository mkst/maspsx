# ASPSX Tests

The idea of this directory is to leverage unit tests to catalog the various differences between ASPSX versions.


## Running the tests

**Install dosemu2 & wine**
[dosemu2](https://github.com/dosemu2/dosemu2) is required to run the 16 bit ASPSX versions, `wine` is required to run the 32bit ASPSX versions.

```
sudo add-apt-repository ppa:dosemu2/ppa
sudo apt update
sudo apt-get install dosemu2 wine
```

**Fetch ASPSX binaries**

```sh
mkdir -p binaries
wget https://github.com/mkst/maspsx/releases/download/aspsx/aspsx-binaries.tar.gz
tar xvzf aspsx-binaries.tar.gz -C binaries
rm aspsx-binaries.tar.gz
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
word arrays keyed directly by ASPSX version. Adding a case normally only requires editing
the relevant YAML file. Identical expected sequences use YAML anchors and
aliases; keep a literal sequence when a version differs in even one word.
Expected words have inline comments generated from `spimdisasm disasmdis
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
