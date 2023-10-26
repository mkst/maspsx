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
    "lwl",
    "lwr",
]
store_mnemonics = [
    "sb",
    "sh",
    "sw",
    "swl",
    "swr",
]

single_reg_loads = [
    "mult",
    "multu",
    "div",
    "divu",
    "rem",
    "move",
    "negu",
]
double_reg_loads = [
    "and",
    "andi",
    "or",
    "ori",
    "xor",
    "xori",
    "addu",
    "subu",
    "sll",
    "slr",
    "srl",
    "sra",
    "slt",
    "slti",
    "sltu",
]


def line_loads_from_reg(line, r_src) -> bool:
    line = line.split("#")[0]  # strip comments
    line = line.strip()

    # escape dollar
    r_src = r_src.replace("$", r"\$")

    if line.count("\t") != 1:
        # print warning?
        return False

    op, rest = line.split("\t")

    if op == "jal":
        if re.match(rf"^.*,\s*{r_src}$", rest):
            return True

    elif op == "j":
        if re.match(rf"^{r_src}$", rest):
            return True

    elif op in branch_mnemonics:
        if re.match(rf"^{r_src},.*$", rest):
            return True
        elif re.match(rf"^.*,\s*{r_src},.*$", rest):
            return True

    elif op in load_mnemonics:
        # lwl	$9,7($2)
        if re.match(rf"^.*,\s?-?(0x)?[0-9a-f]*\(\s*{r_src}\s*\)$", rest):
            return True

    elif op in store_mnemonics:
        if re.match(rf"^.*,\s?-?(0x)?[0-9a-f]*\(\s*{r_src}\s*\)$", rest):
            return True
        # "line_loads_from_reg" is a bit of a lie
        if re.match(rf"^{r_src},.*$", rest):
            return True

    elif op in single_reg_loads:
        if re.match(rf"^.*,\s*{r_src}$", rest):
            return True
        if op.startswith("mult"):
            # TODO: do we need to check for div too?
            if re.match(rf"^{r_src},.*$", rest):
                return True

    elif op in double_reg_loads:
        if re.match(rf"^.*,\s*{r_src},.*$", rest):
            return True
        elif re.match(rf"^.*,.*,\s*{r_src}$", rest):
            return True

    return False


def uses_at(line: str) -> bool:
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


def uses_gp(line: str, sdata_limit: int) -> bool:
    line = line.split("#")[0]
    line = line.strip()

    if uses_at(line):
        op, *_ = line.split("\t")
        if op in ["lw", "sw"] and sdata_limit >= 4:
            return True
        if op in ["lh", "lhu", "sh"] and sdata_limit >= 2:
            return True
        if op in ["lb", "lbu", "sb"] and sdata_limit >= 1:
            return True

    return False


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
    if ignore_set and line in (".set\treorder", ".set\tnoreorder"):
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
    if line in (".set\tmacro", ".set\tnomacro"):
        return False
    if line in ("#.set\tvolatile", "#.set\tnovolatile"):
        return False
    if line in ("#APP", "#NO_APP"):
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
    is_reorder = True
    skip_instructions = 0
    file_num = 1
    line_index = 0

    def __init__(
        self, lines: List[str], expand_div=False, verbose=False, sdata_limit=0
    ):
        self.lines = [x.strip() for x in lines]
        self.expand_div = expand_div
        self.verbose = verbose
        self.sdata_limit = sdata_limit

    def process_lines(self):
        self.is_reorder = True
        self.skip_instructions = 0
        self.file_num = 1
        self.bss_entries = []

        res = []
        for i, line in enumerate(self.lines):
            self.line_index = i

            if is_instruction(line) and self.skip_instructions > 0:
                self.skip_instructions -= 1
                res += [f"# {line}  # DEBUG: skipped"]
            else:
                res += self.process_line(line)

        if len(self.bss_entries) > 0:
            res.append(".section .bss")
            for symbol, size in self.bss_entries:
                res.extend(
                    [
                        f"\t.globl {symbol}",
                        f"{symbol}:",
                        f"\t.space {size}",
                    ]
                )

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

    def _handle_mflo_mfhi(self):
        # we cannot use a div/mult within 2 instructions of mflo/mfhi
        res = []

        next_instruction = self.get_next_instruction(
            skip=0, ignore_nop=True, ignore_set=True, ignore_label=True
        )
        next_next_instruction = self.get_next_instruction(
            skip=1, ignore_nop=True, ignore_set=True, ignore_label=True
        )
        if any(
            next_instruction.startswith(x)
            for x in ["mult\t", "multu\t", "div\t", "divu\t"]
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
                    if inst.startswith("div") and self.expand_div:
                        res.append("# DEBUG: expand_div is True")
                        skip -= 1
                    else:
                        res.append(inst)
                    break
                if not inst.startswith("#"):
                    res.append(inst)
            self.skip_instructions = skip

        elif any(
            next_next_instruction.startswith(x)
            for x in ["mult\t", "multu\t", "div\t", "divu\t"]
        ):
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
                    res.append(inst)
                    res.append(
                        "nop  # DEBUG: mflo/mfhi with mult/div and 1 instruction"
                    )
                elif inst == next_next_instruction:
                    if self.expand_div:
                        res.append("# DEBUG: expand_div is True")
                        skip -= 1
                    else:
                        res.append(inst)
                    break
                elif not inst.startswith("#"):
                    res.append(inst)
            self.skip_instructions = skip

        else:
            # do nothing
            pass

        return res

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

            elif line.startswith(".comm\t"):
                # 	.comm	MENU_RadarScale_800AB480,4
                _, var = line.split()
                symbol, size = var.split(",")
                self.bss_entries.append((symbol, int(size)))

            else:
                res.append(line)

            return res

        op, *rest = line.split()

        if op == "li.s":
            res += load_immediate_single(line)

        elif op == "li.d":
            res += load_immediate_double(line)

        elif op in ("mflo", "mfhi"):
            res.append(line)
            res += self._handle_mflo_mfhi()

        elif op == "break":
            # turn 'break 7' into 'break 0x0,0x7'
            num = int(rest[0])
            line = f"break\t0x0,0x{num:X}"
            res.append(line)

        elif self.expand_div and op in ("div", "rem"):
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
            if line_loads_from_reg(next_instruction, r_dest):
                res.append(f"nop  # DEBUG: next op ({op}) loads from {r_dest}")
            else:
                res += self._handle_mflo_mfhi()

        elif self.expand_div and op == "divu":
            r_dest, r_source, r_operand = rest[0].split(",")
            res.append("# EXPAND_DIV START")
            res.append(".set\tnoat")
            res.append(f"divu\t$zero,{r_source},{r_operand}")
            res.append(f"bnez\t{r_operand},.L_NOT_DIV_BY_ZERO_{self.line_index}")
            res.append("nop")
            res.append("break\t0x7")
            res.append(f".L_NOT_DIV_BY_ZERO_{self.line_index}:")
            res.append(f"mflo\t{r_dest}")
            res.append(".set\tat")
            res.append("# EXPAND_DIV START")

            next_instruction = self.get_next_instruction(skip=0, ignore_set=True)
            if line_loads_from_reg(next_instruction, r_dest):
                res.append(f"nop  # DEBUG: next op ({op}) loads from {r_dest}")
            else:
                res += self._handle_mflo_mfhi()

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
                res.append(f"{line} # DEBUG: leaving for assembler to expand")
                nop = self.get_next_instruction(skip=0)
                if nop == "#nop":
                    op, *_ = next_instruction.split()
                    if op in branch_mnemonics:
                        res.append("nop  # DEBUG: next instruction is branch")
                        self.skip_instructions = 1
                    elif line_loads_from_reg(next_instruction, r_dest):
                        res.append(f"nop  # DEBUG: next op ({op}) loads from {r_dest}")
                        self.skip_instructions = 1
                    else:
                        res.append(
                            f"#nop  # DEBUG: next op ({op}) does not load from {r_dest}"
                        )

            elif is_addend and r_source is None:
                # e.g. lb	$s0,D_800E52E0
                res.append(line)

                if line_loads_from_reg(next_instruction, r_dest):
                    if not uses_at(next_instruction) or uses_gp(
                        next_instruction, self.sdata_limit
                    ):
                        label = self.get_next_instruction(
                            skip=0, ignore_nop=True, ignore_set=True
                        )
                        if is_label(label):
                            res.append(label)
                            self.skip_instructions = 1
                        res.append(f"nop # DEBUG: next op loads from {r_dest}")
                else:
                    res.append(
                        f"#nop # DEBUG: {next_instruction} does not load from {r_dest}"
                    )

            elif is_addend and r_source:
                # e.g. lw	$2,test_sym($4)
                res.append("# EXPAND_AT START")
                res.append(".set\tnoat")
                res.append(f"lui\t$at,%hi({operand})")
                res.append(f"addu\t$at,$at,{r_source}")
                res.append(f"{op}\t{r_dest},%lo({operand})($at)")
                res.append(".set\tat")
                res.append("# EXPAND_AT START")

                if not uses_at(next_instruction) and line_loads_from_reg(
                    next_instruction, r_dest
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

            else:
                if r_source and int(operand) > 32767:
                    # e.g. lhu	$2,49344($2)
                    res.append("# EXPAND_AT START")
                    res.append(".set\tnoat")
                    res.append(f"lui\t$at,%hi({operand})")
                    res.append(f"addu\t$at,{r_source},$at")
                    res.append(f"{op}\t{r_dest},%lo({operand})($at)")
                    res.append(".set\tat")
                    res.append("# EXPAND_AT START")
                else:
                    # e.g. lhu	$2,528482304
                    res.append(line)

                # TODO: properly handle multi-line macros
                if ";" in next_instruction:
                    next_instruction = next_instruction.split(";")[0]

                if not uses_at(next_instruction) and line_loads_from_reg(
                    next_instruction, r_dest
                ):
                    label = self.get_next_instruction(
                        skip=0, ignore_nop=True, ignore_set=True
                    )
                    if is_label(label):
                        res.append(label)
                        self.skip_instructions = 1
                    res.append(
                        f"nop # DEBUG: {r_dest} in {next_instruction} and '{next_instruction}' does not use $at"
                    )

        elif op == "li":
            res.append(line)
            rest = " ".join(rest)
            r_dest, *_ = rest.split(",")
            # TODO: make this more generic
            next_instruction = self.get_next_instruction(skip=0)
            if next_instruction.startswith("div") and next_instruction.endswith(
                f",{r_dest}"
            ):
                res.append(
                    f"nop # DEBUG: li {r_dest} followed by div that uses {r_dest}"
                )

        else:
            if line == ".rdata":
                line = ".section .rodata"

            res.append(line)

        return res
