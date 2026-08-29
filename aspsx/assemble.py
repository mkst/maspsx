import sys
from pathlib import Path
from util import AssemblerError, disassemble, run_aspsx

if len(sys.argv) < 2:
    print(f"Usage: python3 {sys.argv[0]} PATH/TO/ASM.S")
    sys.exit(0)

asm_file = Path(sys.argv[1])

versions = [
    # "1.05",
    # "1.07",
    # "2.05",
    # "2.08",
    # "2.21",
    # "2.30",
    # "2.34",
    # "2.56",
    "2.67",
    # "2.77",
    # "2.79",
    # "2.81",
    # "2.86",
]

for version in versions:
    print(version)
    try:
        res = run_aspsx(asm_file, {"aspsx_version": version}, extra_flags="")
        for line in disassemble(res):
            print(line)
    except AssemblerError as e:
        print(f"FAILED:\n{e}")
    except Exception as e:
        print(f"INTERNAL ERROR: {e}")
