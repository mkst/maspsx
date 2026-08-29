from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
from typing import Optional


ASPSX_RUNNER_LOOKUP = {
    "1.05": "dosemu2", "1.07": "dosemu2", "2.05": "dosemu2",
    "2.08": "dosemu2", "2.21": "dosemu2", "2.30": "dosemu2",
    "2.34": "dosemu2", "2.56": "wine", "2.67": "wine",
    "2.77": "wine", "2.79": "wine", "2.81": "wine", "2.86": "wine",
}

DEFAULT_TIMEOUT = 30.0


class ObjectFormatError(ValueError):
    """Raised when a PSYQ object does not contain a readable .text section."""


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


def _need(data: bytes, ptr: int, size: int, context: str) -> None:
    if ptr + size > len(data):
        raise ObjectFormatError(
            f"truncated {context} at byte 0x{ptr:x} (needed {size} bytes)"
        )


def read_text_section(data: bytes) -> bytes:
    # Based on the PSYQ object format notes in pcsx-redux's psyq-obj-parser.
    _need(data, 0, 4, "header")
    if data[:3] != b"LNK":
        raise ObjectFormatError("not a PSYQ object (missing LNK signature)")
    if data[3] != 2:
        raise ObjectFormatError(f"unknown PSYQ object version {data[3]}")

    ptr = 4
    sections: dict[int, str] = {}
    current_section: Optional[str] = None
    while ptr < len(data):
        opcode_offset = ptr
        opcode = data[ptr]
        ptr += 1
        if opcode == 46:  # PROGRAMTYPE
            _need(data, ptr, 1, "PROGRAMTYPE")
            ptr += 1
        elif opcode == 16:  # SECTION
            _need(data, ptr, 6, "SECTION header")
            section_index = int.from_bytes(data[ptr:ptr + 2], "little")
            ptr += 5  # index, group, alignment
            string_length = data[ptr]
            ptr += 1
            _need(data, ptr, string_length, "SECTION name")
            try:
                section_name = data[ptr:ptr + string_length].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ObjectFormatError(f"invalid SECTION name at byte 0x{ptr:x}") from exc
            ptr += string_length
            sections[section_index] = section_name
        elif opcode == 6:  # SWITCH
            _need(data, ptr, 2, "SWITCH")
            section_index = int.from_bytes(data[ptr:ptr + 2], "little")
            ptr += 2
            if section_index not in sections:
                raise ObjectFormatError(f"SWITCH references unknown section {section_index}")
            current_section = sections[section_index]
        elif opcode == 2:  # BYTES
            _need(data, ptr, 2, "BYTES header")
            size = int.from_bytes(data[ptr:ptr + 2], "little")
            ptr += 2
            _need(data, ptr, size, "BYTES payload")
            payload = data[ptr:ptr + size]
            ptr += size
            if current_section == ".text":
                return payload
        elif opcode == 28:
            _need(data, ptr, 3, "file record")
            ptr += 2
            string_length = data[ptr]
            ptr += 1
            _need(data, ptr, string_length, "file name")
            ptr += string_length
        else:
            raise ObjectFormatError(
                f"unknown object opcode {opcode} at byte 0x{opcode_offset:x}"
            )
    raise ObjectFormatError("object did not contain a .text section")


def _words_from_text(text_data: bytes) -> list[str]:
    if len(text_data) % 4 != 0:
        raise ObjectFormatError(f".text length {len(text_data)} is not aligned to 4 bytes")
    return [
        f"0x{int.from_bytes(text_data[i:i + 4], 'little'):08X}"
        for i in range(0, len(text_data), 4)
    ]


def _build_command(runner: str, aspsx_path: Path, workspace: Path,
                   source_name: str, object_name: str, data_limit: str,
                   extra_flags: str) -> list[str]:
    flags = [*shlex.split(data_limit), *shlex.split(extra_flags)]
    if runner == "wine":
        return ["wine", str(aspsx_path), *flags, "-o", object_name, source_name]
    if runner == "dosemu2":
        guest_command = shlex.join(["ASPSX.EXE", *flags, "-o", object_name, source_name])
        return ["dosemu", "-dumb", "-K", str(workspace), "-E", guest_command]
    raise ValueError(f"unsupported ASPSX runner {runner!r}")


def run_aspsx_result(source_asm: Path, version: dict, data_limit: str = "",
                     extra_flags: str = "", timeout: float = DEFAULT_TIMEOUT) -> RunResult:
    """Run one assembler case in a private workspace and return its result."""
    source_asm = Path(source_asm).resolve()
    aspsx_version = version["aspsx_version"]
    runner = ASPSX_RUNNER_LOOKUP.get(aspsx_version, "unknown")
    binaries_base = Path(__file__).parent / "binaries" / aspsx_version
    aspsx_path = binaries_base / "ASPSX.EXE"
    command: list[str] = []
    if runner == "unknown":
        return RunResult(source_asm, aspsx_version, runner, command,
                         error=f"no runner is configured for ASPSX {aspsx_version}",
                         failure_kind="unsupported_version")
    with tempfile.TemporaryDirectory(prefix=f"aspsx-{aspsx_version}-") as temp:
        workspace = Path(temp)
        staged_source = workspace / source_asm.name
        try:
            shutil.copy2(source_asm, staged_source)
            if runner == "dosemu2":
                shutil.copy2(aspsx_path, workspace / "ASPSX.EXE")
        except OSError as exc:
            return RunResult(source_asm, aspsx_version, runner, command,
                             error=f"could not stage assembler workspace: {exc}",
                             failure_kind="staging_error")
        try:
            command = _build_command(runner, aspsx_path, workspace, staged_source.name,
                                     "output.obj", data_limit, extra_flags)
        except (ValueError, OSError) as exc:
            return RunResult(source_asm, aspsx_version, runner, command,
                             error=f"could not build assembler command: {exc}",
                             failure_kind="command_error")
        started = time.monotonic()
        try:
            proc = subprocess.run(command, cwd=workspace, check=False,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout)
            result = RunResult(source_asm, aspsx_version, runner, command,
                               proc.returncode, _text(proc.stdout), _text(proc.stderr),
                               duration=time.monotonic() - started)
        except FileNotFoundError as exc:
            result = RunResult(source_asm, aspsx_version, runner, command,
                               error=f"required host executable is unavailable: {exc.filename}",
                               failure_kind="missing_tool",
                               duration=time.monotonic() - started)
        except PermissionError as exc:
            result = RunResult(source_asm, aspsx_version, runner, command,
                               error=f"cannot execute required host executable: {exc}",
                               failure_kind="permission_error",
                               duration=time.monotonic() - started)
        except OSError as exc:
            result = RunResult(source_asm, aspsx_version, runner, command,
                               error=f"could not start assembler process: {exc}",
                               failure_kind="runner_error",
                               duration=time.monotonic() - started)
        except subprocess.TimeoutExpired as exc:
            result = RunResult(source_asm, aspsx_version, runner, command,
                               stdout=_text(exc.stdout or b""), stderr=_text(exc.stderr or b""),
                               error=f"process exceeded timeout of {timeout:g}s",
                               failure_kind="timeout",
                               duration=time.monotonic() - started)
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
        try:
            result.instructions = _words_from_text(read_text_section(object_file.read_bytes()))
        except (OSError, ObjectFormatError) as exc:
            result.error = str(exc)
            result.failure_kind = "parse_error"
        return result


def run_aspsx(source_asm: Path, version: dict, data_limit: str = "",
              extra_flags: str = "", timeout: float = DEFAULT_TIMEOUT) -> list[str]:
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


def assert_assembly_equal(testcase, expected: list[str], actual: list[str]) -> None:
    """Assert words while retaining a useful assembly-level mismatch report."""
    if expected != actual:
        testcase.fail("assembly mismatch\n\n" + assembly_diff(expected, actual))
