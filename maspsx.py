import sys
import subprocess
import argparse


from maspsx import MaspsxProcessor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-assembler", action="store_true")
    parser.add_argument("--no-macro-inc", action="store_true")
    parser.add_argument("--force-stdin", action="store_true")
    parser.add_argument("--gnu-as-path", default="mips-linux-gnu-as")
    parser.add_argument("--expand-div", action="store_true")
    parser.add_argument("--verbose", action="store_true")

    args, as_args = parser.parse_known_args()

    read_from_file = sys.stdin.isatty()

    if not read_from_file:
        in_lines = sys.stdin.readlines()
        if len(in_lines) == 0:
            if args.force_stdin:
                sys.stderr.write("Error: No input from stdin!\n")
                sys.exit(1)
            else:
                sys.stderr.write(
                    "Warning: No input from stdin, will try to read from a file\n"
                )
                read_from_file = True

    if read_from_file:
        try:
            input_file = as_args.pop()
        except IndexError:
            sys.stderr.write("Error: No input file found!\n")
            sys.exit(1)

        with open(input_file, "r") as f:
            in_lines = f.readlines()

    in_lines.append("")  # Warning: end of file not at end of a line; newline inserted

    preamble = [
        "" if args.no_macro_inc else '.include "macro.inc"',
    ]

    maspsx_processor = MaspsxProcessor(
        in_lines, expand_div=args.expand_div, verbose=args.verbose
    )
    try:
        out_lines = maspsx_processor.process_lines()
    except Exception as err:
        sys.stderr.write(f"Exception occurred: {err}\n")
        sys.exit(1)

    out_text = "\n".join(preamble + out_lines)

    # FIXME: can we stop gcc from passing us this flag?
    if "-KPIC" in as_args:
        # sys.stderr.write("WARNING: Removed -KPIC flag!\n")
        as_args.remove("-KPIC")

    if args.run_assembler:
        cmd = [
            args.gnu_as_path,
            *as_args,
            "-",  # read from stdin
        ]
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE
        )
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
