from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
from typing import Optional

ASPSX_RUNNER_LOOKUP = {
    "1.05": "daze",
    "1.07": "daze",
    "2.05": "daze",
    "2.08": "daze",
    "2.21": "daze",
    "2.30": "daze",
    "2.34": "daze",
    "2.56": "wibo",
    "2.67": "wibo",
    "2.77": "wibo",
    "2.79": "wibo",
    "2.81": "wibo",
    "2.86": "wibo",
}

DEFAULT_TIMEOUT = 30.0

PSYQ_OBJ_PARSER = Path(__file__).parent / "binaries" / "psyq-obj-parser"

DATA_SECTIONS = (".rdata", ".data", ".sdata", ".sbss", ".bss")

# Symbol offsets keyed by symbol name. `.comm` symbols have no offset.
SymbolOffsets = dict[str, Optional[int]]

STT_SECTION = 3
STT_FILE = 4

# The instruction bits that each ELF relocation type fills in.
RELOCATION_MASKS = {
    2: 0xFFFFFFFF,  # R_MIPS_32
    4: 0x03FFFFFF,  # R_MIPS_26
    5: 0x0000FFFF,  # R_MIPS_HI16
    6: 0x0000FFFF,  # R_MIPS_LO16
    7: 0x0000FFFF,  # R_MIPS_GPREL16
}


class ObjectFormatError(ValueError):
    """Raised when a PSYQ object cannot be converted or read."""


@dataclass
class RunResult:
    source_asm: Path
    version: str
    runner: str
    command: list[str]
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    instructions: Optional[list[str]] = None
    error: Optional[str] = None
    duration: float = 0.0
    failure_kind: Optional[str] = None
    sections: dict[str, SymbolOffsets] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and self.instructions is not None

    @property
    def status(self) -> str:
        return "passed" if self.ok else (self.failure_kind or "failed")

    def diagnostic(self) -> str:
        lines = [
            f"ASPSX {self.version} ({self.runner}) failed for {self.source_asm}",
            f"command: {shlex.join(self.command)}",
        ]
        if self.returncode is not None:
            lines.append(f"return code: {self.returncode}")
        if self.error:
            lines.append(f"status: {self.status}")
            lines.append(f"reason: {self.error}")
        if self.stdout:
            lines.append(f"stdout:\n{self.stdout.rstrip()}")
        if self.stderr:
            lines.append(f"stderr:\n{self.stderr.rstrip()}")
        return "\n".join(lines)


class AssemblerError(AssertionError):
    """A case-level assembler failure with process and diagnostic context."""

    def __init__(self, result: RunResult):
        super().__init__(result.diagnostic())
        self.result = result


def _text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def convert_to_elf(
    object_file: Path, elf_file: Path, timeout: float = DEFAULT_TIMEOUT
) -> None:
    """Convert a PSYQ object to ELF with psyq-obj-parser."""
    try:
        proc = subprocess.run(
            [str(PSYQ_OBJ_PARSER), str(object_file), "-o", str(elf_file)],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ObjectFormatError(
            f"psyq-obj-parser exceeded timeout of {timeout:g}s"
        ) from exc
    if proc.returncode != 0 or not elf_file.exists():
        # Errors go to stderr; stdout only has progress messages.
        errors = [
            line.strip().removeprefix("::").strip()
            for line in _text(proc.stderr).splitlines()
            if line.strip()
        ]
        raise ObjectFormatError(
            f"psyq-obj-parser could not convert the object "
            f"(exit code {proc.returncode}): {' / '.join(errors) or 'no output'}"
        )


def clear_relocated_fields(text: bytes, relocations: list[tuple[int, int]]) -> bytes:
    """
    Zero the instruction bits filled in by each `(offset, type)` relocation.

    psyq-obj-parser stores relocation addends in the instructions, as ELF REL
    relocations require. ASPSX leaves those bits zero and keeps the addend in
    the relocation instead.
    """
    data = bytearray(text)
    for offset, relocation_type in relocations:
        mask = RELOCATION_MASKS.get(relocation_type)
        if mask is None:
            raise ObjectFormatError(
                f"unsupported relocation type {relocation_type} "
                f"at .text offset 0x{offset:x}"
            )
        if offset + 4 > len(data):
            raise ObjectFormatError(
                f"relocation at .text offset 0x{offset:x} is out of bounds"
            )
        word = int.from_bytes(data[offset : offset + 4], "little") & ~mask
        data[offset : offset + 4] = word.to_bytes(4, "little")
    return bytes(data)


def read_text_section(elf_data: bytes) -> bytes:
    """Return the .text section of an ELF object, as ASPSX emitted it."""
    from spimdisasm.common import FileSectionType
    from spimdisasm.elf32 import Elf32File

    elf = Elf32File(elf_data)
    text = elf.progbits.get(FileSectionType.Text)
    if text is None:
        return b""
    rel = elf.rel.get(FileSectionType.Text)
    relocations = [(r.offset, r.rType) for r in rel.relocations] if rel else []
    return clear_relocated_fields(
        elf_data[text.offset : text.offset + text.size], relocations
    )


def read_symbol_offsets(elf_data: bytes) -> dict[str, SymbolOffsets]:
    """Return the offset of each symbol ASPSX placed in a data section."""
    from spimdisasm.elf32 import Elf32File

    elf = Elf32File(elf_data)
    names = {
        index: elf.shstrtab[header.name]
        for index, header in enumerate(elf.sectionHeaders.sections)
    }
    sections: dict[str, SymbolOffsets] = {}
    for symbol in elf.symtab.symbols:
        name = elf.strtab[symbol.name]
        section = names.get(symbol.shndx)
        if not name or section not in DATA_SECTIONS:
            continue
        if symbol.info & 0xF in (STT_SECTION, STT_FILE):
            continue
        # The linker places `.comm` symbols, so their offsets come from
        # psyq-obj-parser rather than ASPSX. They're the only data symbols
        # with a size.
        offset = None if symbol.size else symbol.value
        sections.setdefault(section, {})[name] = offset
    return sections


def _words_from_text(text_data: bytes) -> list[str]:
    if len(text_data) % 4 != 0:
        raise ObjectFormatError(
            f".text length {len(text_data)} is not aligned to 4 bytes"
        )
    return [
        f"0x{int.from_bytes(text_data[i:i + 4], 'little'):08X}"
        for i in range(0, len(text_data), 4)
    ]


def _build_command(
    runner: str,
    aspsx_path: Path,
    workspace: Path,
    source_name: str,
    object_name: str,
    data_limit: str,
    extra_flags: str,
) -> list[str]:
    flags = [*shlex.split(data_limit), *shlex.split(extra_flags)]
    if runner == "wibo":
        return ["wibo", str(aspsx_path), *flags, "-o", object_name, source_name]
    if runner == "daze":
        return ["daze", "ASPSX.EXE", *flags, "-o", object_name, source_name]
    raise ValueError(f"unsupported ASPSX runner {runner!r}")


def run_aspsx_result(
    source_asm: Path,
    version: dict,
    data_limit: str = "",
    extra_flags: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> RunResult:
    """Run one assembler case in a private workspace and return its result."""
    source_asm = Path(source_asm).resolve()
    aspsx_version = version["aspsx_version"]
    runner = ASPSX_RUNNER_LOOKUP.get(aspsx_version, "unknown")
    binaries_base = Path(__file__).parent / "binaries" / aspsx_version
    aspsx_path = binaries_base / "ASPSX.EXE"
    command: list[str] = []
    if runner == "unknown":
        return RunResult(
            source_asm,
            aspsx_version,
            runner,
            command,
            error=f"no runner is configured for ASPSX {aspsx_version}",
            failure_kind="unsupported_version",
        )
    with tempfile.TemporaryDirectory(prefix=f"aspsx-{aspsx_version}-") as temp:
        workspace = Path(temp)
        staged_source = workspace / source_asm.name
        try:
            shutil.copy2(source_asm, staged_source)
            if runner == "daze":
                shutil.copy2(aspsx_path, workspace / "ASPSX.EXE")
        except OSError as exc:
            return RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                error=f"could not stage assembler workspace: {exc}",
                failure_kind="staging_error",
            )
        try:
            command = _build_command(
                runner,
                aspsx_path,
                workspace,
                staged_source.name,
                "output.obj",
                data_limit,
                extra_flags,
            )
        except (ValueError, OSError) as exc:
            return RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                error=f"could not build assembler command: {exc}",
                failure_kind="command_error",
            )
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command,
                cwd=workspace,
                check=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            result = RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                proc.returncode,
                _text(proc.stdout),
                _text(proc.stderr),
                duration=time.monotonic() - started,
            )
        except FileNotFoundError as exc:
            result = RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                error=f"required host executable is unavailable: {exc.filename}",
                failure_kind="missing_tool",
                duration=time.monotonic() - started,
            )
        except PermissionError as exc:
            result = RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                error=f"cannot execute required host executable: {exc}",
                failure_kind="permission_error",
                duration=time.monotonic() - started,
            )
        except OSError as exc:
            result = RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                error=f"could not start assembler process: {exc}",
                failure_kind="runner_error",
                duration=time.monotonic() - started,
            )
        except subprocess.TimeoutExpired as exc:
            result = RunResult(
                source_asm,
                aspsx_version,
                runner,
                command,
                stdout=_text(exc.stdout or b""),
                stderr=_text(exc.stderr or b""),
                error=f"process exceeded timeout of {timeout:g}s",
                failure_kind="timeout",
                duration=time.monotonic() - started,
            )
        if result.error:
            return result
        if result.returncode not in (None, 0):
            result.error = "assembler process exited unsuccessfully"
            result.failure_kind = "process_error"
            return result
        object_file = workspace / "output.obj"
        if not object_file.exists():
            result.error = "assembler completed but did not create output.obj"
            result.failure_kind = "missing_output"
            return result
        elf_file = workspace / "output.elf"
        try:
            convert_to_elf(object_file, elf_file, timeout)
            elf_data = elf_file.read_bytes()
            result.instructions = _words_from_text(read_text_section(elf_data))
            result.sections = read_symbol_offsets(elf_data)
        except FileNotFoundError as exc:
            result.error = f"required host executable is unavailable: {exc.filename}"
            result.failure_kind = "missing_tool"
        except PermissionError as exc:
            result.error = f"cannot execute required host executable: {exc}"
            result.failure_kind = "permission_error"
        except (OSError, ObjectFormatError) as exc:
            result.error = str(exc)
            result.failure_kind = "parse_error"
        return result


def run_aspsx(
    source_asm: Path,
    version: dict,
    data_limit: str = "",
    extra_flags: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> list[str]:
    """Compatibility wrapper returning words or a useful case-level error."""
    result = run_aspsx_result(source_asm, version, data_limit, extra_flags, timeout)
    if not result.ok:
        raise AssemblerError(result)
    return result.instructions or []


def disassemble(words: list[str]) -> list[str]:
    """Return one stable human-readable instruction line per machine word."""
    try:
        # Use spimdisasm's configured Rabbitizer bridge when available. This
        # keeps the harness aligned with the disassembler used by the project.
        from spimdisasm.disasmdis import DisasmdisInternals

        decoder = DisasmdisInternals.rabbitizer.Instruction
        parse_word = DisasmdisInternals.getWordFromStr
    except (ImportError, AttributeError):
        decoder = None
        parse_word = None
    try:
        if decoder is None:
            import rabbitizer

            decoder = rabbitizer.Instruction
    except ImportError:
        return [f"{word}  <Rabbitizer unavailable>" for word in words]
    lines = []
    for offset, word in enumerate(words):
        try:
            value = parse_word(word[2:]) if parse_word else int(word, 16)
            instruction = decoder(value).disassemble()
        except Exception as exc:
            instruction = f"<decode error: {exc}>"
        lines.append(f"0x{offset * 4:04X}: {word}  {instruction}")
    return lines


def assembly_diff(expected: list[str], actual: list[str]) -> str:
    """Format a compact raw-word and disassembled diff for assertion errors."""
    lines = ["offset  expected                         actual"]
    expected_dis = disassemble(expected)
    actual_dis = disassemble(actual)
    for index in range(max(len(expected), len(actual))):
        exp = expected[index] if index < len(expected) else "<missing>"
        got = actual[index] if index < len(actual) else "<missing>"
        if exp == got:
            continue
        exp_text = expected_dis[index] if index < len(expected_dis) else "<missing>"
        got_text = actual_dis[index] if index < len(actual_dis) else "<missing>"
        lines.append(f"0x{index * 4:04X}  {exp_text:<34} {got_text}")
    if len(expected) != len(actual):
        lines.append(f"length: expected {len(expected)} words, got {len(actual)}")
    return "\n".join(lines)


def _symbol_differs(expected: SymbolOffsets, actual: SymbolOffsets, name: str) -> bool:
    return name not in actual or expected[name] != actual[name]


def _format_offset(offset: Optional[int]) -> str:
    return "<comm>" if offset is None else f"0x{offset:X}"


def symbol_diff(expected: SymbolOffsets, actual: SymbolOffsets) -> str:
    """Format the expected symbols whose offsets differ, in section order."""
    lines = [f"{'symbol':<24}{'expected':<12}actual"]
    order = sorted(
        expected, key=lambda name: (expected[name] is None, expected[name] or 0, name)
    )
    for name in order:
        if _symbol_differs(expected, actual, name):
            got = _format_offset(actual[name]) if name in actual else "<missing>"
            lines.append(f"{name:<24}{_format_offset(expected[name]):<12}{got}")
    return "\n".join(lines)


def output_diff(
    expected_text: Optional[list[str]],
    expected_sections: dict[str, SymbolOffsets],
    result: RunResult,
) -> str:
    """
    Return a report for each expected section that differs, or "".

    Only the sections and symbols listed in the fixture are checked.
    """
    reports = []
    actual_text = result.instructions or []
    if expected_text is not None and expected_text != actual_text:
        reports.append(".text mismatch\n\n" + assembly_diff(expected_text, actual_text))
    for section, expected in expected_sections.items():
        actual = result.sections.get(section, {})
        if any(_symbol_differs(expected, actual, name) for name in expected):
            reports.append(f"{section} mismatch\n\n" + symbol_diff(expected, actual))
    return "\n\n".join(reports)
