"""Show ELF parsing changing subsequent hex-byte decoding; no files required."""

from importlib.metadata import version
import struct

import rabbitizer
from spimdisasm.common import GlobalConfig, InputEndian
from spimdisasm.disasmdis.DisasmdisInternals import getWordFromStr
from spimdisasm.elf32 import Elf32File


def little_endian_elf():
    """Build an empty ELF32/MIPS object with null and .shstrtab sections."""
    names = b"\0.shstrtab\0"
    ident = b"\x7fELF\x01\x01\x01" + bytes(9)
    header = struct.pack(
        "<16sHHIIIIIHHHHHH", ident, 1, 8, 1, 0, 0, 52, 0, 52, 0, 0, 40, 2, 1
    )
    null_section = bytes(40)
    string_section = struct.pack("<10I", 1, 3, 0, 0, 132, len(names), 0, 0, 1, 0)
    return header + null_section + string_section + names


def show(label):
    word = getWordFromStr("00220821")
    print(f"{label}: ENDIAN={GlobalConfig.ENDIAN.name}, word=0x{word:08X}")
    print(f"  {rabbitizer.Instruction(word).disassemble()}")


def main():
    print(f"spimdisasm {version('spimdisasm')}, rabbitizer {version('rabbitizer')}")
    saved_endian = GlobalConfig.ENDIAN
    try:
        GlobalConfig.ENDIAN = InputEndian.BIG
        show("Before ELF parsing")
        Elf32File(little_endian_elf())
        show("After ELF parsing")
        word = int("00220821", 16)
        print(f"Direct integer decoding: {rabbitizer.Instruction(word).disassemble()}")
    finally:
        GlobalConfig.ENDIAN = saved_endian


if __name__ == "__main__":
    main()
