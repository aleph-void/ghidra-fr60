#!/usr/bin/env python3
"""Build hand-computed FR60 emulator cases. Usage: emu_tests.py <outdir> [--break NAME]."""
from pathlib import Path
import os
import subprocess
import sys

TESTS = [
    ("add", ["ldi:8 5,r0", "ldi:8 7,r1", "add r1,r0"], {}, {"R0": 12}),
    ("add2_minus", ["ldi:8 5,r0", "add2 -16,r0"], {}, {"R0": 0xfffffff5}),
    ("addn2_minus", ["ldi:8 5,r0", "addn2 -1,r0"], {}, {"R0": 4}),
    ("cmp2_minus", ["cmp2 -16,r0"], {"R0": 5}, {"R0": 5, "C": 1}),
    ("lsl2", ["lsl2 0,r0"], {"R0": 1}, {"R0": 0x10000}),
    ("lsr2", ["lsr2 0,r0"], {"R0": 0x80000000}, {"R0": 0x8000}),
    ("asr2", ["asr2 0,r0"], {"R0": 0x80000000}, {"R0": 0xffff8000}),
    ("load", ["ld @r1,r0"], {"R1": 0x1000, "m4:1000": 0x12345678}, {"R0": 0x12345678}),
    ("store", ["st r0,@r1"], {"R0": 0x12345678, "R1": 0x1000}, {"m4:1000": 0x12345678}),
]


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    broken = sys.argv[sys.argv.index("--break") + 1] if "--break" in sys.argv else None
    lines = [".text", ".globl _start", "_start:"]
    for name, code, _, _ in TESTS:
        lines.append(f"t_{name}:")
        lines.extend("  " + ins for ins in code)
        lines.append(f"e_{name}:")
        lines.append("  nop")
    (out / "emu.s").write_text("\n".join(lines) + "\n")
    prefix = os.environ.get("FR30_TOOL_PREFIX", "fr30-elf-")
    subprocess.run([prefix + "as", "-o", str(out / "emu.o"), str(out / "emu.s")], check=True)
    subprocess.run([prefix + "objcopy", "-O", "binary", "-j", ".text", str(out / "emu.o"), str(out / "emu.bin")], check=True)
    nm = subprocess.check_output([prefix + "nm", str(out / "emu.o")], text=True)
    symbols = {x[2]: int(x[0], 16) for line in nm.splitlines() if len(x := line.split()) == 3}
    tests = []
    for name, _, initial, expected in TESTS:
        expected = dict(expected)
        if name == broken:
            key = next(iter(expected))
            expected[key] ^= 1
        fmt = lambda d: ",".join(f"{k}={v:x}" for k, v in d.items()) or "-"
        tests.append(f"{name} {symbols['t_' + name]:x} {symbols['e_' + name]:x} {fmt(initial)} {fmt(expected)}")
    (out / "emu.txt").write_text("\n".join(tests) + "\n")
    print(f"{len(TESTS)} emulator cases")


if __name__ == "__main__":
    main()
