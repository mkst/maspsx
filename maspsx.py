import argparse
import subprocess
import sys

from maspsx import MaspsxProcessor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--aspsx-version", type=str)
    parser.add_argument("--run-assembler", action="store_true")
    parser.add_argument("--gnu-as-path", default="mips-linux-gnu-as")
    parser.add_argument("--dont-force-G0", action="store_true")
    parser.add_argument("--expand-div", action="store_true")
    parser.add_argument("--macro-inc", action="store_true")
    parser.add_argument("--dont-expand-li", action="store_true")
    parser.add_argument("--force-stdin", action="store_true")
    # deprecated
    parser.add_argument("--no-macro-inc", action="store_true")
    parser.add_argument("--expand-li", action="store_true")

    args, as_args = parser.parse_known_args()

    if args.no_macro_inc:
        sys.stderr.write(
            "MASPSX: --no-macro-inc is no longer required and will be removed in a future update\n"
        )

    if args.expand_li:
        sys.stderr.write(
            "MASPSX: --expand-li is enabled automatically if --aspsx-version is below 2.56\n"
        )

    read_from_file = sys.stdin.isatty()

    if not read_from_file:
        in_lines = sys.stdin.readlines()
        if len(in_lines) == 0:
            if args.force_stdin:
                sys.stderr.write("MASPSX: --force-stdin but no input from stdin!\n")
                sys.exit(1)
            else:
                sys.stderr.write(
                    "MASPSX: Warning, no input from stdin, will try to read from a file\n"
                )
                read_from_file = True

    if read_from_file:
        try:
            input_file = as_args.pop()
        except IndexError:
            sys.stderr.write("MASPSX: Error, no input file found!\n")
            sys.exit(1)

        with open(input_file, "r") as f:
            in_lines = f.readlines()

    preamble = [
        '.include "macro.inc"' if args.macro_inc else "",
    ]

    sdata_limit = 0
    for arg in as_args:
        if arg.startswith("-G") and len(arg) > 2:
            sdata_limit = int(arg[2:])

    nop_v0_at = False  # insert nop between v0/at?
    sltu_at = True  # sltu uses at?
    expand_li = True  # turn li into lui/ori
    gp_allow_offset = False  # use gp for sym+offset?
    gp_allow_la = False  # use gp for la

    if args.aspsx_version:
        aspsx_version = tuple(int(x) for x in args.aspsx_version.split("."))
        if aspsx_version == (2, 21):
            nop_v0_at = True
        if aspsx_version > (2, 34):
            expand_li = False
        if aspsx_version >= (2, 77):
            sltu_at = False
            gp_allow_offset = True
        if aspsx_version >= (2, 81):
            gp_allow_la = True

    if args.dont_expand_li and expand_li:
        expand_li = False

    maspsx_processor = MaspsxProcessor(
        in_lines,
        sdata_limit=sdata_limit,
        expand_div=args.expand_div,
        expand_li=expand_li,
        nop_v0_at=nop_v0_at,
        sltu_at=sltu_at,
        gp_allow_offset=gp_allow_offset,
        gp_allow_la=gp_allow_la,
    )
    try:
        out_lines = maspsx_processor.process_lines()
    except Exception as err:
        sys.stderr.write(f"MASPSX: An exception occurred: {err}\n")
        sys.exit(1)

    out_text = "\n".join(preamble + out_lines)

    # avoid "Warning: end of file not at end of a line; newline inserted"
    out_text += "\n"

    # FIXME: can we stop gcc from passing us this flag?
    if "-KPIC" in as_args:
        # sys.stderr.write("WARNING: Removed -KPIC flag!\n")
        as_args.remove("-KPIC")

    if args.run_assembler:
        cmd = [
            args.gnu_as_path,
            "-EL",  # TODO: switch from 'mips-linux-gnu-as' to 'mipsel-linux-gnu-as'
            *as_args,
            "-",  # read from stdin
        ]
        if not args.dont_force_G0:
            cmd.insert(-1, "-G0")

        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
            out_bytes = out_text.encode("utf")
            stdout, stderr = process.communicate(input=out_bytes)
            if len(stdout):
                sys.stdout.write(stdout.decode("utf"))
            if len(stderr):
                sys.stderr.write(stderr.decode("utf"))
    else:
        sys.stdout.write(out_text)


if __name__ == "__main__":
    main()
