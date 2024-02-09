import struct
import re

from typing import List

branch_mnemonics = {
    "beq",
    "bgez",
    "bgtz",
    "blez",
    "bltz",
    "bne",
}
jump_mnemonics = {
    "j",
    "jal",
}
load_mnemonics = {
    "lb",
    "lbu",
    "lh",
    "lhu",
    "lw",
    "lwl",
    "lwr",
    "lwc2",
}
store_mnemonics = {
    "sb",
    "sh",
    "sw",
    "swl",
    "swr",
}

single_reg_loads = {
    "mult",
    "multu",
    "div",
    "divu",
    "rem",
    "move",
    "negu",
    "nor",
}
double_reg_loads = {
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
}


def strip_comments(line) -> str:
    if line.count("#") > 0:
        line = line.split("#")[0]
    return line.strip()


def line_loads_from_reg(line, r_src) -> bool:
    line = strip_comments(line)

    # escape dollar
    r_src = r_src.replace("$", r"\$")

    if line.count("\t") != 1:
        # print warning?
        return False

    op, rest = line.split("\t")

    if op in load_mnemonics:
        # lwl	$9,7($2)
        if re.match(rf"^.*,\s?-?(0x)?[0-9a-f]*\(\s*{r_src}\s*\)$", rest):
            return True

    elif op in store_mnemonics:
        if re.match(rf"^.*,\s?-?(0x)?[0-9a-f]*\(\s*{r_src}\s*\)$", rest):
            return True
        # "line_loads_from_reg" is a bit of a lie
        if re.match(rf"^{r_src},.*$", rest):
            return True

    elif op == "jal":
        if re.match(rf"^.*,\s*{r_src}$", rest):
            return True

    elif op == "j":
        if re.match(rf"^{r_src}$", rest):
            return True

    elif op in branch_mnemonics:
        if re.match(rf"^{r_src},.*$", rest):
            return True
        if re.match(rf"^.*,\s*{r_src},.*$", rest):
            return True

    elif op in single_reg_loads:
        if re.match(rf"^.*,\s*{r_src}$", rest):
            return True
        if op.startswith("mult"):
            if re.match(rf"^{r_src},.*$", rest):
                return True
        if op.startswith("div"):
            # e.g. div	$3,$3,$7
            if re.match(rf"^.*,{r_src}.*$", rest):
                return True

    elif op in double_reg_loads:
        if re.match(rf"^.*,\s*{r_src},.*$", rest):
            return True
        if re.match(rf"^.*,.*,\s*{r_src}$", rest):
            return True

    return False


def uses_at(line: str) -> bool:
    line = strip_comments(line)

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


def parse_load_or_store(rest):
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
        raise Exception(f"Unable to parse load/store instruction: {rest}")

    if re.match(r"^-?\d+$", operand) or re.match(r"^-?0x[A-Fa-f0-9]+$", operand):
        is_addend = False
    else:
        is_addend = True

    return (r_source, r_dest, operand, is_addend, needs_expanding)


def div_needs_expanding(line: str) -> bool:
    inst, *rest = line.split()
    if not (inst.startswith("div") or inst.startswith("rem")):
        return False

    r_dest, *_ = rest[0].split(",")
    return r_dest not in ("$zero", "$0")


def expand_load_immediate(line: str) -> List[str]:
    res = []

    match = re.match(r"li\s+(\$[0-9A-z]+),\s?(-?[x0-9a-fA-F]+)", line)
    r_dest = match.group(1)
    operand = int(match.group(2), 0)

    if 0 < operand < 0x10000:
        res.append(f"ori\t{r_dest},$zero,{operand}")
    elif operand >= 0x10000:
        res.append(f"lui\t{r_dest},%hi({operand})")
        if operand & 0xFFFF:
            res.append(f"ori\t{r_dest},{r_dest},{operand} & 0xFFFF")
    elif 0 > operand > -0x8000:
        res.append(f"addiu\t{r_dest},$zero,{operand}")
    elif operand == -0x8000:
        res.append(f"addiu\t{r_dest},$zero,{operand} & 0xFFFF")
    elif operand < -0x8000:
        res.append(f"lui\t{r_dest},({operand} >> 16) & 0xFFFF")
        if operand & 0xFFFF:
            res.append(f"ori\t{r_dest},{r_dest},{operand} & 0xFFFF")
    else:
        # this would be a sw rather than li, but for completeness:
        res.append(f"lui\t{r_dest},0")

    return res


def is_label(line: str):
    return re.match(r"\$L\d+:$", line)


def is_instruction(line: str, ignore_nop=False, ignore_set=False, ignore_label=False):
    if len(line) == 0:
        return False

    if ignore_nop and line == "#nop":
        return False
    if ignore_set and line in (
        ".set\treorder",
        ".set\tnoreorder",
        ".set\tvolatile",
        ".set\tnovolatile",
    ):
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
        # li $fx
        "$f0": "$f1",
        "$f2": "$f3",
        "$f4": "$f5",
        "$f6": "$f7",
        "$f12": "$f13",
        "$f14": "$f15",
        # names
        "$v0": "$v1",
        "$a0": "$a1",
        "$a2": "$a3",
        "$t0": "$t1",
        "$t2": "$t3",
        "$s0": "$s1",
        "$s2": "$s3",
        # nums
        "$2": "$3",  # $v0
        "$4": "$5",  # $a0
        "$6": "$7",  # $a2
        "$8": "$9",  # $t0
        "$10": "$11",  # t2
        "$18": "$19",  # s2
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
        self,
        lines: List[str],
        sdata_limit=0,
        expand_div=False,
        expand_li=False,
        nop_v0_at=False,
        nop_gp=False,
    ):
        self.lines = [x.strip() for x in lines]

        self.sdata_limit = sdata_limit

        self.expand_div = expand_div
        self.expand_li = expand_li

        self.nop_v0_at = nop_v0_at
        self.nop_gp = nop_gp

        self.bss_entries = {}
        self.sbss_entries = {}
        self.sdata_entries = {}

    def preprocess_lines(self):
        in_sdata = False
        uses_size = False

        for line in self.lines:
            if line.startswith(".align"):
                # TODO: worry about alignment later
                continue

            if line.startswith(".globl"):
                continue

            if line.startswith(".text"):
                in_sdata = False
                continue
            if line.startswith(".data"):
                in_sdata = False
                continue
            if line.startswith(".rdata"):
                in_sdata = False
                continue

            if line == ".section .text":
                in_sdata = False
                continue

            if line.startswith("#"):
                continue

            if line.startswith(".sdata"):
                in_sdata = True
                continue

            if line.startswith(".comm") or line.startswith(".lcomm"):
                # e.g.	.comm	MENU_RadarScale_800AB480,4
                in_sdata = False
                _, var = line.split()
                symbol, size = var.split(",")
                size = int(size)
                if size <= self.sdata_limit:
                    self.sbss_entries[symbol] = size
                else:
                    self.bss_entries[symbol] = size
                continue

            if in_sdata:
                # NOTE: newer compilers emit .size for sdata, old ones do not...
                if match := re.match(r"\.size\s+([^,]+),([0-9]+)", line):
                    current_symbol = match.group(1)
                    size = int(match.group(2))
                    self.sdata_entries[current_symbol] = size
                    uses_size = True
                    continue

                if not uses_size:
                    if line.endswith(":"):
                        current_symbol = line.replace(":", "")
                        self.sdata_entries[current_symbol] = 0
                    else:
                        if line.startswith(".type"):
                            continue

                        if line.startswith(".space"):
                            _, size = line.split()
                            size = int(size)
                        elif line.startswith(".word"):
                            size = 4
                        elif line.startswith(".half") or line.startswith(".short"):
                            size = 2
                        elif line.startswith(".byte"):
                            size = 1
                        elif line.startswith(".ascii"):
                            # e.g. .ascii	"Map poly groups\000"
                            # NOTE: len('.ascii\t""') == 9
                            size = len(line) - 9
                        else:
                            raise Exception(
                                f"Unable to parse .sdata instruction: {line}"
                            )
                        self.sdata_entries[current_symbol] += size

    def process_lines(self):
        self.is_reorder = True
        self.skip_instructions = 0
        self.file_num = 1

        self.bss_entries = {}
        self.sbss_entries = {}
        self.sdata_entries = {}

        self.preprocess_lines()

        res = []
        for i, line in enumerate(self.lines):
            self.line_index = i

            if is_instruction(line) and self.skip_instructions > 0:
                self.skip_instructions -= 1
                res += [f"# {line}  # DEBUG: skipped"]
            else:
                res += self.process_line(line)

        for section, entries in [
            ("sbss", self.sbss_entries),
            ("bss", self.bss_entries),
        ]:
            for i, (symbol, size) in enumerate(entries.items()):
                if i == 0:
                    res.append(f".section .{section}")
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

    def _uses_gp(self, line: str) -> bool:
        if self.sdata_limit == 0:
            return False

        line = strip_comments(line)
        if uses_at(line):
            op, *rest = line.split("\t")
            if op in load_mnemonics or op in store_mnemonics:
                rest = " ".join(rest)
                (
                    _,
                    _,
                    operand,
                    _,
                    _,
                ) = parse_load_or_store(rest)

                if operand.count("+") == 1:
                    symbol, _ = operand.split("+")
                else:
                    symbol = operand

                if symbol in self.sbss_entries:
                    return True
                if symbol in self.sdata_entries:
                    return True

        return False

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
                    if div_needs_expanding(inst):
                        res.append("# DEBUG: div needs expanding")
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

                    if op == "li":
                        expanded = expand_load_immediate(inst)

                        if self.expand_li:
                            res += expanded
                        else:
                            res.append(inst)

                        if len(expanded) == 2:
                            res.append(
                                "#nop  # DEBUG: mflo/mfhi with mult/div and li expands to 2 ops"
                            )
                        else:
                            res.append(
                                "nop  # DEBUG: mflo/mfhi with mult/div and li expands to 1 op"
                            )

                    else:
                        res.append(inst)
                        res.append(
                            "nop  # DEBUG: mflo/mfhi with mult/div and 1 instruction"
                        )

                elif inst == next_next_instruction:
                    if div_needs_expanding(inst):
                        res.append("# DEBUG: div needs expanding")
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

            elif line.startswith(".comm") or line.startswith(".lcomm"):
                # already handled via preprocess_lines
                pass

            elif line.startswith(".data"):
                res.append(".section .data")
            elif line.startswith(".sdata"):
                res.append(".section .sdata")
            elif line.startswith(".rdata"):
                res.append(".section .rodata")

            else:
                res.append(line)

            return res

        if line.startswith("$L"):
            return [line]

        op, *rest = line.split()

        if op in load_mnemonics:
            rest = " ".join(rest)
            r_source, r_dest, operand, is_addend, needs_expanding = parse_load_or_store(
                rest
            )

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
                if operand.count("+") == 1:
                    symbol, offset = operand.split("+")
                    gp_rel = f"%gp_rel({symbol}+{offset})($gp)"
                else:
                    symbol = operand
                    gp_rel = f"%gp_rel({symbol})($gp)"

                if symbol in self.sdata_entries or symbol in self.sbss_entries:
                    res.append(f"{op}\t{r_dest},{gp_rel}")
                else:
                    res.append(line)

                # TODO: properly handle multi-line macros
                if ";" in next_instruction:
                    next_instruction = next_instruction.split(";")[0]

                if line_loads_from_reg(next_instruction, r_dest):
                    nop_required = False

                    if not uses_at(next_instruction):
                        reason = f"'{next_instruction}' does not use $at"
                        nop_required = True
                    if self.nop_gp and self._uses_gp(next_instruction):
                        reason = f"'{next_instruction}' uses $gp"
                        nop_required = True
                    if self.nop_v0_at:
                        reason = f"'{next_instruction}' inject nop beween $v0 and $at"
                        nop_required = True

                    if nop_required:
                        label = self.get_next_instruction(
                            skip=0, ignore_nop=True, ignore_set=True
                        )
                        if is_label(label):
                            res.append(label)
                            self.skip_instructions = 1
                        res.append(f"nop # DEBUG: Reuse of '{r_dest}'. {reason}")
                else:
                    res.append(
                        f"#nop # DEBUG: {next_instruction} does not load from {r_dest}"
                    )

            elif is_addend and r_source:
                # e.g. lw	$2,test_sym($4)
                res.extend(
                    [
                        "# EXPAND_AT START",
                        ".set\tnoat",
                        f"lui\t$at,%hi({operand})",
                        f"addu\t$at,$at,{r_source}",
                        f"{op}\t{r_dest},%lo({operand})($at)",
                        ".set\tat",
                        "# EXPAND_AT END",
                    ]
                )

                # TODO: properly handle multi-line macros
                if ";" in next_instruction:
                    next_instruction = next_instruction.split(";")[0]

                if line_loads_from_reg(next_instruction, r_dest):
                    nop_required = False

                    if not uses_at(next_instruction):
                        reason = f"'{next_instruction}' does not use $at"
                        nop_required = True
                    if self.nop_gp and self._uses_gp(next_instruction):
                        reason = f"nop_gp and '{next_instruction}' uses $gp"
                        nop_required = True

                    if nop_required:
                        label = self.get_next_instruction(
                            skip=0, ignore_nop=True, ignore_set=True
                        )
                        if is_label(label):
                            res.append(label)
                            self.skip_instructions = 1
                        res.append(
                            f"nop # DEBUG: is_addend (r_dest: {r_dest}) {reason}"
                        )

            else:
                if r_source and int(operand) > 32767:
                    # e.g. lhu	$2,49344($2)
                    res.extend(
                        [
                            "# EXPAND_AT START",
                            ".set\tnoat",
                            f"lui\t$at,%hi({operand})",
                            f"addu\t$at,{r_source},$at",
                            f"{op}\t{r_dest},%lo({operand})($at)",
                            ".set\tat",
                            "# EXPAND_AT END",
                        ]
                    )
                else:
                    # e.g. lhu	$2,528482304
                    res.append(line)

                # TODO: properly handle multi-line macros
                if ";" in next_instruction:
                    next_instruction = next_instruction.split(";")[0]

                if line_loads_from_reg(next_instruction, r_dest):
                    nop_required = False
                    if not uses_at(next_instruction):
                        reason = f"'{next_instruction}' does not use $at"
                        nop_required = True
                    if self.nop_gp and self._uses_gp(next_instruction):
                        reason = f"'{next_instruction}' uses $gp"
                        nop_required = True

                    if nop_required:
                        label = self.get_next_instruction(
                            skip=0, ignore_nop=True, ignore_set=True
                        )
                        if is_label(label):
                            res.append(label)
                            self.skip_instructions = 1
                        res.append(f"nop # DEBUG: Reuse of '{r_dest}'. {reason}")

        elif op in store_mnemonics or (op == "la" and self.sdata_limit > 0):
            rest = " ".join(rest)
            r_source, r_dest, operand, is_addend, _ = parse_load_or_store(rest)

            if is_addend and r_source is None:
                # e.g. sw	$v0,D_800E52E0
                if operand.count("+") == 1:
                    symbol, offset = operand.split("+")
                    gp_rel = f"%gp_rel({symbol}+{offset})($gp)"
                else:
                    symbol = operand
                    gp_rel = f"%gp_rel({symbol})($gp)"

                if symbol in self.sdata_entries or symbol in self.sbss_entries:
                    res.append(f"{op}\t{r_dest},{gp_rel}")
                else:
                    res.append(line)
            else:
                res.append(line)

        elif op in branch_mnemonics or op in jump_mnemonics:
            res.append(line)
            if self.is_reorder:
                res.append("nop  # DEBUG: branch/jump")
            # else:
            # res.append(f"#nop # DEBUG: branch/jump, is_reorder: {self.is_reorder}")

        elif op in ("addu", "subu", "move", "sra", "srl", "srr", "sll"):
            # no extra processing required
            res.append(line)

        elif op == "li":
            # TODO: handle non-soft floats?
            if self.expand_li:
                res += expand_load_immediate(line)
            else:
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

        elif op == "li.s":
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

        elif op in ("div", "rem"):
            r_dest, r_source, r_operand = rest[0].split(",")
            if r_dest in ("$zero", "$0"):
                # e.g. div $zero, $v0, $a0
                return [line]

            move_from = "mfhi" if op == "rem" else "mflo"
            if self.expand_div:
                res.extend(
                    [
                        "# EXPAND_DIV START",
                        ".set\tnoat",
                        f"div\t$zero,{r_source},{r_operand}",
                        f"bnez\t{r_operand},.L_NOT_DIV_BY_ZERO_{self.line_index}",
                        "nop",
                        "break\t0x7",
                        f".L_NOT_DIV_BY_ZERO_{self.line_index}:",
                        "addiu\t$at,$zero,-1",
                        f"bne\t{r_operand},$at,.L_DIV_BY_POSITIVE_SIGN_{self.line_index}",
                        "lui\t$at,0x8000",
                        f"bne\t{r_source},$at,.L_DIV_BY_POSITIVE_SIGN_{self.line_index}",
                        "nop",
                        "break\t0x6",
                        f".L_DIV_BY_POSITIVE_SIGN_{self.line_index}:",
                        f"{move_from}\t{r_dest}",
                        ".set\tat",
                        "# EXPAND_DIV END",
                    ]
                )
            else:
                res.extend(
                    [
                        "# EXPAND_ZERO_DIV START",
                        f"div\t$zero,{r_source},{r_operand}",
                        f"{move_from}\t{r_dest}",
                        "# EXPAND_ZERO_DIV END",
                    ]
                )

            extra_nops = self._handle_mflo_mfhi()
            if len(extra_nops) > 0:
                res += extra_nops
            else:
                next_instruction = self.get_next_instruction(skip=0, ignore_set=True)
                if line_loads_from_reg(next_instruction, r_dest):
                    res.append(
                        f"nop  # DEBUG: {op} and next_instruction ({next_instruction}) loads from {r_dest}"
                    )

        elif op in ("divu", "remu"):
            r_dest, r_source, r_operand = rest[0].split(",")
            if r_dest in ("$zero", "$0"):
                # e.g. divu $zero, $v1, $a2
                return [line]

            move_from = "mfhi" if op == "remu" else "mflo"
            if self.expand_div:
                res.extend(
                    [
                        "# EXPAND_DIVU START",
                        ".set\tnoat",
                        f"divu\t$zero,{r_source},{r_operand}",
                        f"bnez\t{r_operand},.L_NOT_DIV_BY_ZERO_{self.line_index}",
                        "nop",
                        "break\t0x7",
                        f".L_NOT_DIV_BY_ZERO_{self.line_index}:",
                        f"{move_from}\t{r_dest}",
                        ".set\tat",
                        "# EXPAND_DIVU END",
                    ]
                )
            else:
                res.extend(
                    [
                        "# EXPAND_ZERO_DIVU START",
                        f"divu\t$zero,{r_source},{r_operand}",
                        f"{move_from}\t{r_dest}",
                        "# EXPAND_ZERO_DIVU END",
                    ]
                )

            extra_nops = self._handle_mflo_mfhi()
            if len(extra_nops) > 0:
                res += extra_nops
            else:
                next_instruction = self.get_next_instruction(skip=0, ignore_set=True)
                if line_loads_from_reg(next_instruction, r_dest):
                    res.append(
                        f"nop  # DEBUG: {op} and next_instruction ({next_instruction}) loads from {r_dest}"
                    )

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

        else:
            res.append(line)

        return res
