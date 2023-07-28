import struct
import re

from typing import List

branch_mnemonics = [
    "beq",
    "bgez",
    "bgtz",
    "blez",
    "bltz",
    "bne",
]
jump_mnemonics = [
    "j",
    "jal",
]
load_mnemonics = [
    "lb",
    "lbu",
    "lh",
    "lhu",
    "lw",
    "lwr",
]


def reg_in_line(reg, line):
    if len(line) == 0:
        return False

    line = line.split("#")[0]  # strip comments
    line = line.strip()

    # escape dollar
    reg = reg.replace("$", r"\$")

    if re.match(rf"[a-z]+\s+{reg}$", line):
        # "j	$2"
        return True
    if re.match(rf"[a-z]+\s+{reg},.*", line):
        # "lhu	$2,0($3)"
        return True
    if re.match(rf"mtc2\s+{reg},.*", line):
        # "mtc2	$2, $8"
        return True
    if re.match(rf".*,{reg},.*", line):
        return True
    if re.match(rf".*,{reg}$", line):
        # subu	$3,$3,$2
        return True
    if re.match(rf".*\({reg}\).*", line):
        # "lh	$4,0($2)"
        return True

    return False


def uses_at(line: str):
    # take everything before the comment
    line = line.split("#")[0]
    line = line.strip()

    # sw	$2,D_801813A4
    # sw	$3,g_CurrentRoom+40
    if match := re.match(r"^s[wbh]\s+(\$[a-z0-9]+),\s*([A-z0-9_+]+)$", line):
        return True

    if match := re.match(r"l[a-z]+\s+(\$[a-z0-9]+),\s*([^(]+)\(([^)]+)\)", line):
        operand = match.group(2)

    # sb	$2,g_InputSaveName($3)
    elif match := re.match(r"^s[wbh]\s+(\$[a-z0-9]+),\s*([^(]+)\(([^)]+)\)", line):
        operand = match.group(2)

    else:
        return False

    if re.match(r"^-?\d+$", operand) or re.match(r"^-?0x[A-Fa-f0-9]+$", operand):
        # sw	$2,-26($16)
        return False

    return True


def is_load(line: str):
    op, *_ = line.split()
    return op in load_mnemonics


def is_label(line: str):
    return re.match(r"\$L\d+:$", line)


def is_instruction(line: str, ignore_nop=False, ignore_set=False, ignore_label=False):
    if len(line) == 0:
        return False

    if ignore_nop and line == "#nop":
        return False
    if ignore_set and (line == ".set\treorder" or line == ".set\tnoreorder"):
        return False
    if ignore_label and is_label(line):
        return False

    if line.startswith(".stab"):
        return False
    if line.startswith(".def") or line.startswith(".bend") or line.startswith(".begin"):
        return False
    if line.startswith(".loc"):
        return False
    if line.startswith("L") and line[1] not in "0123456789" and line.endswith(":"):
        return False
    if line == ".set\tmacro" or line == ".set\tnomacro":
        return False
    if line == "#.set\tvolatile" or line == "#.set\tnovolatile":
        return False
    if line == "#APP" or line == "#NO_APP":
        return False

    return True


def get_next_register(reg: str):
    lut = {
        "$a0": "$a1",
        "$a2": "$a3",
        "$s2": "$s3",
        "$t0": "$t1",
        "$4": "$5",
        "$6": "$7",
        "$8": "$9",
        "$18": "$19",
    }
    next_reg = lut.get(reg)
    assert next_reg is not None, f"Unknown mapping for {reg}"
    return next_reg


def load_immediate_single(line: str):
    res = []
    r1, value = line[5:].split(",")
    (value,) = struct.unpack(">i", struct.pack(">f", float(value)))
    upper = (value & 0xFFFF_0000) >> 16
    lower = (value & 0x0000_FFFF) >> 0

    res.append(f"lui\t{r1},0x{upper:X}")
    # we don't always need the lower part
    if lower:
        res.append(f"ori\t{r1},0x{lower:X}")
    return res


def load_immediate_double(line: str):
    res = []
    r1, value = line[5:].split(",")
    r2 = get_next_register(r1)
    (value,) = struct.unpack(">q", struct.pack(">d", float(value)))

    r1_upper = (value & 0x0000_0000_FFFF_0000) >> 16
    r1_lower = (value & 0x0000_0000_0000_FFFF) >> 0
    r2_upper = (value & 0xFFFF_0000_0000_0000) >> 48
    r2_lower = (value & 0x0000_FFFF_0000_0000) >> 32

    if r1_upper or r1_lower:
        res.append(f"lui\t{r1},0x{r1_upper:X}")
        if r1_lower:
            res.append(f"ori\t{r1},0x{r1_lower:X}")
    else:
        res.append(f"li\t{r1},0x0")

    res.append(f"lui\t{r2},0x{r2_upper:X}")
    if r2_lower:
        res.append(f"ori\t{r2},0x{r2_lower:X}")

    return res


class MaspsxProcessor:
    def __init__(self, lines: List[str], expand_div=False, verbose=False):
        self.lines = [x.strip() for x in lines]
        self.expand_div = expand_div
        self.verbose = verbose

    def process_lines(self):
        self.is_reorder = True
        self.skip_instructions = 0
        self.file_num = 1

        res = []
        for i, line in enumerate(self.lines):
            self.line_index = i

            if is_instruction(line) and self.skip_instructions > 0:
                self.skip_instructions -= 1
                res += [f"# {line}  # DEBUG: skipped"]
            else:
                res += self.process_line(line)

        return res

    def get_next_instruction(
        self, skip=0, ignore_nop=False, ignore_set=False, ignore_label=False
    ):
        i = self.line_index + 1
        while i < len(self.lines):
            line = self.lines[i]
            if is_instruction(
                line,
                ignore_nop=ignore_nop,
                ignore_set=ignore_set,
                ignore_label=ignore_label,
            ):
                if skip == 0:
                    return line
                skip -= 1
            i += 1

        return ""  # warn user?

    def process_line(self, line):
        res = []

        if len(line) == 0:
            return [line]

        if line == "#nop":
            return []

        if line.startswith("."):
            if (
                line.startswith(".def\t")
                or line.startswith(".begin\t")
                or line.startswith(".bend\t")
            ):
                # skip these coff directives - gnu as does not like them
                pass

            elif line.startswith(".set\t"):
                if line.endswith("\tnoreorder"):
                    self.is_reorder = False
                elif line.endswith("\treorder"):
                    self.is_reorder = True

            elif line.startswith(".file\t"):
                # fix same-numbered files
                _, num, filename = line.split()
                res.append(f".file\t{self.file_num} {filename}")
                self.file_num += 1

            elif line.startswith(".ent\t"):
                # enforce noreorder for each function
                res.append(line)
                res.append(".set\tnoreorder")

            else:
                res.append(line)

            return res

        op, *rest = line.split()

        if op == "li.s":
            res += load_immediate_single(line)

        elif op == "li.d":
            res += load_immediate_double(line)

        elif op in ("mflo", "mfhi"):
            # cannot use a mult within 2 instructions of mflo/mfhi
            res.append(line)
            next_instruction = self.get_next_instruction(
                skip=0, ignore_nop=True, ignore_set=True, ignore_label=True
            )
            next_next_instruction = self.get_next_instruction(
                skip=1, ignore_nop=True, ignore_set=True, ignore_label=True
            )
            if next_instruction.startswith("mult\t") or next_instruction.startswith(
                "div\t"
            ):
                # #nop
                # #nop
                # mult...
                skip = 0
                while True:
                    inst = self.get_next_instruction(skip=skip)
                    skip += 1
                    if inst == next_instruction:
                        res.append("nop")
                        res.append("nop")
                        res.append(inst)
                        break
                    if not inst.startswith("#"):
                        res.append(inst)
                self.skip_instructions = skip

            elif next_next_instruction.startswith(
                "mult\t"
            ) or next_next_instruction.startswith("div\t"):
                # #nop
                # #nop
                # addu or lh ...
                # mult ...
                skip = 0
                while True:
                    inst = self.get_next_instruction(skip=skip)
                    skip += 1
                    if inst == next_instruction:
                        op, *_ = inst.strip().split()
                        if op in load_mnemonics:
                            # allow for $at handling later in the script
                            skip = 0
                            break
                        else:
                            res.append(inst)
                            res.append(
                                "nop  # DEBUG: mflo/mfhi with mult/div and 1 instruction"
                            )
                    elif inst == next_next_instruction:
                        res.append(inst)
                        break
                    elif not inst.startswith("#"):
                        res.append(inst)
                self.skip_instructions = skip

            else:
                # do nothing
                pass

        elif op == "break":
            # turn 'break 7' into 'break 0x0,0x7'
            num = int(rest[0])
            line = f"break\t0x0,0x{num:X}"
            res.append(line)

        elif self.expand_div and op in ("div", "rem"):
            # FIXME: handle mult within next 3 instructions!
            move_from = "mfhi" if op == "rem" else "mflo"
            r_dest, r_source, r_operand = rest[0].split(",")
            res.append("# EXPAND_DIV START")
            res.append(".set\tnoat")
            res.append(f"div\t$zero,{r_source},{r_operand}")
            res.append(f"bnez\t{r_operand},.L_NOT_DIV_BY_ZERO_{self.line_index}")
            res.append("nop")
            res.append("break\t0x7")
            res.append(f".L_NOT_DIV_BY_ZERO_{self.line_index}:")
            res.append("addiu\t$at,$zero,-1")
            res.append(
                f"bne\t{r_operand},$at,.L_DIV_BY_POSITIVE_SIGN_{self.line_index}"
            )
            res.append("lui\t$at,0x8000")
            res.append(f"bne\t{r_source},$at,.L_DIV_BY_POSITIVE_SIGN_{self.line_index}")
            res.append("nop")
            res.append("break\t0x6")
            res.append(f".L_DIV_BY_POSITIVE_SIGN_{self.line_index}:")
            res.append(f"{move_from}\t{r_dest}")
            res.append(".set\tat")
            res.append("# EXPAND_DIV END")

            next_instruction = self.get_next_instruction(skip=0, ignore_set=True)
            if reg_in_line(r_dest, next_instruction):
                res.append(f"nop # DEBUG: {op} and {r_dest} in {next_instruction}")

        elif self.expand_div and op == "divu":
            # FIXME: handle mult within next 3 instructions!
            r_dest, r_source, r_operand = rest[0].split(",")
            res.append(".set\tnoat")
            res.append(f"divu\t$zero,{r_source},{r_operand}")
            res.append(f"bnez\t{r_operand},.L_NOT_DIV_BY_ZERO_{self.line_index}")
            res.append("nop")
            res.append("break\t0x7")
            res.append(f".L_NOT_DIV_BY_ZERO_{self.line_index}:")
            res.append(f"mflo\t{r_dest}")
            res.append(".set\tat")

            next_instruction = self.get_next_instruction(skip=0, ignore_set=True)
            if reg_in_line(r_dest, next_instruction):
                res.append(f"nop # DEBUG: {op} and {r_dest} in {next_instruction}")

        elif op == "sltu":
            r_dest, r_source, r_operand = rest[0].split(",")
            if re.match(r"^-?\d+$", r_operand) or re.match(
                r"^-?0x[A-Fa-f0-9]+$", r_operand
            ):
                value = int(r_operand)
                if value < 0:
                    res.append(f"li\t$at,{r_operand}")
                    res.append(f"{op}\t{r_dest},{r_source},$at")
                else:
                    res.append(line)
            else:
                res.append(line)

        elif op in branch_mnemonics + jump_mnemonics:
            res.append(line)
            if self.is_reorder:
                res.append("nop  # DEBUG: branch/jump")

        elif op in load_mnemonics:
            rest = " ".join(rest)
            if match := re.match(r"(\$[a-z0-9]+),\s*%lo\(([^(]+)\)\(([^(]+)\)", rest):
                r_dest = match.group(1)
                operand = match.group(2)
                r_source = match.group(3)
                needs_expanding = False
            elif match := re.match(r"(\$[a-z0-9]+),\s*([^(]+)\(([^)]+)\)", rest):
                r_dest = match.group(1)
                operand = match.group(2)
                r_source = match.group(3)
                needs_expanding = True
            elif match := re.match(r"(\$[a-z0-9]+),\s*([^(]+)", rest):
                r_dest = match.group(1)
                operand = match.group(2)
                r_source = None
                needs_expanding = True
            else:
                raise Exception(f"Unable to parse load instruction: {line}")

            if re.match(r"^-?\d+$", operand) or re.match(
                r"^-?0x[A-Fa-f0-9]+$", operand
            ):
                is_addend = False
            else:
                is_addend = True

            next_instruction = self.get_next_instruction(
                skip=0, ignore_nop=True, ignore_set=True, ignore_label=True
            )

            if not needs_expanding:
                res.append(f"{line} # DEBUG: for assembler to expand")
                nop = self.get_next_instruction(skip=0)
                if nop == "#nop":
                    op, *_ = next_instruction.split()
                    if op in branch_mnemonics:
                        res.append("nop  # DEBUG: next instruction is branch")
                        self.skip_instructions = 1

            elif is_addend and r_source is None:
                # e.g. lb	$s0,D_800E52E0
                res.append(line)

                if not uses_at(next_instruction) and reg_in_line(
                    r_dest, next_instruction
                ):
                    next_op, *_ = next_instruction.split()
                    if next_op in ("li", "la"):
                        # ignore load address / load immediate
                        self.verbose and res.append(
                            "#nop # DEBUG: load address/immediate into r_dest"
                        )
                    elif next_op in load_mnemonics:
                        if f"({r_dest})" in next_instruction:
                            label = self.get_next_instruction(
                                skip=0, ignore_nop=True, ignore_set=True
                            )
                            if is_label(label):
                                res.append(label)
                                self.skip_instructions = 1

                            res.append(f"nop # DEBUG: next op READS from {r_dest}")
                        else:
                            # we dont need a nop
                            self.verbose and res.append(
                                f"#nop # DEBUG: next op WRITES to {r_dest}"
                            )
                    else:
                        label = self.get_next_instruction(
                            skip=0, ignore_nop=True, ignore_set=True
                        )
                        if is_label(label):
                            res.append(label)
                            self.skip_instructions = 1

                        res.append(
                            "nop # DEBUG: is_addend (not uses_at and reg_in_line)"
                        )

                    self.verbose and res.append(f"# {r_dest} in {next_instruction}")
                else:
                    self.verbose and res.append(f"# not {r_dest} in {next_instruction}")

            elif is_addend and r_source:
                # e.g. lw	$2,test_sym($4)
                res.append(".set\tnoat")
                res.append(f"lui\t$at,%hi({operand})")
                res.append(f"addu\t$at,$at,{r_source}")
                res.append(f"{op}\t{r_dest},%lo({operand})($at)")
                res.append(".set\tat")

                if not uses_at(next_instruction) and reg_in_line(
                    r_dest, next_instruction
                ):
                    label = self.get_next_instruction(
                        skip=0, ignore_nop=True, ignore_set=True
                    )
                    if is_label(label):
                        res.append(label)
                        self.skip_instructions = 1
                    res.append(
                        f"nop # DEBUG: is_addend (r_dest: {r_dest}) '{next_instruction}' does not use $at"
                    )

            elif (
                not is_addend
                and r_source in ("$2", "$v0")
                and r_source == r_dest
                and int(operand) > 32767
            ):
                # e.g. lhu	$2,49344($2)
                res.append(".set\tnoat")
                res.append(f"lui\t$at,%hi({operand})")
                res.append(f"addu\t$at,{r_source},$at")
                res.append(f"{op}\t{r_dest},%lo({operand})($at)")
                res.append(".set\tat")

                if not uses_at(next_instruction) and reg_in_line(
                    r_dest, next_instruction
                ):
                    label = self.get_next_instruction(
                        skip=0, ignore_nop=True, ignore_set=True
                    )
                    if is_label(label):
                        res.append(label)
                        self.skip_instructions = 1
                    res.append(
                        f"nop # DEBUG: is_addend (r_dest: {r_dest}) '{next_instruction}' does not use $at"
                    )

            elif not is_addend and r_source and reg_in_line(r_dest, next_instruction):
                # e.g. lw	$v0,364($a3)
                #      beq	$a3,$a0,$L14
                res.append(line)

                if uses_at(next_instruction):
                    res.append(
                        f"#nop # DEBUG: {r_dest} in {next_instruction} and '{next_instruction}' uses $at"
                    )
                else:
                    label = self.get_next_instruction(skip=0)
                    if is_label(label):
                        res.append(label)
                        self.skip_instructions = 1
                    res.append(
                        f"nop # DEBUG: {r_dest} in {next_instruction} and '{next_instruction}' does not use $at"
                    )
            else:
                res.append(line)

        else:
            if line == ".rdata":
                line = ".section .rodata"

            res.append(line)

        return res
