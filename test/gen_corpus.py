#!/usr/bin/env python3
"""Decode corpora for the FR module (big-endian, 6-byte slots: the longest FR instruction is
LDI:32, 6 bytes; FR81 instructions are at most 4 bytes).

  gen_corpus.py <outdir> [seed]
      first.bin  every 16-bit first halfword (65,536) x 3 second/third halfword pairs
                 (zero, all ones, random), 196,608 slots
      fuzz.bin   100,000 random 6-byte slots
"""
import os
import random
import struct
import sys


def main():
    out = sys.argv[1]
    rnd = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    with open(os.path.join(out, "first.bin"), "wb") as f:
        for tail in (0, 1, 2):
            for h in range(0x10000):
                if tail == 0:
                    t = (0, 0)
                elif tail == 1:
                    t = (0xffff, 0xffff)
                else:
                    t = (rnd.getrandbits(16), rnd.getrandbits(16))
                f.write(struct.pack(">HHH", h, *t))
    with open(os.path.join(out, "fuzz.bin"), "wb") as f:
        for _ in range(100000):
            f.write(rnd.getrandbits(48).to_bytes(6, "big"))
    print("first 196608 slots, fuzz 100000 slots")


if __name__ == "__main__":
    main()
