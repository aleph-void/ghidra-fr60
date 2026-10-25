#!/usr/bin/env python3
"""Compare Ghidra slot disassembly (DumpSlots.java) with GNU objdump slot disassembly (slotdis)
for Fujitsu FR.

  compare.py <ghidra.txt> <objdump.txt> [examples-per-class]

exact:    same length and text after lower-casing, removing blanks and '#' in the operands,
          writing R13/R14/R15 as AC/FP/SP (Fujitsu's names, which Ghidra uses) and every
          number as signed hex
semantic: additionally immediates and addresses modulo 2^32
objdump rejects with "*unknown*".
"""
import re
import sys
from collections import Counter, defaultdict

NUM = re.compile(r"(?<![\w.])(-?)(0x[0-9a-f]+|\d+)(?![\w])")
GPR = {"r13": "ac", "r14": "fp", "r15": "sp"}


def load(path):
    d = {}
    for line in open(path):
        p = line.rstrip("\n").split(" ", 2)
        if len(p) < 2:
            continue
        d[int(p[0], 16)] = (int(p[1]), p[2] if len(p) > 2 else "")
    return d


def canon(m):
    v = int(m.group(2), 0)
    return ("-" if m.group(1) else "") + hex(v)


def exact_norm(t):
    t = t.lower().replace("\t", " ").strip()
    t = re.sub(r"\s*<[^>]*>", "", t)
    m, _, ops = t.partition(" ")
    # Ghidra prefixes instructions in a delay slot with "_"; GNU prints the mnemonic itself.
    m = m.lstrip("_")
    ops = ops.replace(" ", "").replace("#", "")
    ops = re.sub(r"(?<![\w])(r1[345])(?![\w])", lambda x: GPR[x.group(1)], ops)
    # The module prints FR's AC post-increment register without '@'; objdump prints @r13+.
    ops = ops.replace("@ac+", "ac+")
    # The coprocessor registers are numeric operands in SLEIGH and CRn in GNU's syntax.
    ops = re.sub(r"\bcr(\d+)\b", lambda x: hex(int(x.group(1))), ops)
    return (m + " " + NUM.sub(canon, ops)).strip()


def sem_norm(t):
    t = exact_norm(t)
    m, _, ops = t.partition(" ")
    ops = NUM.sub(lambda x: hex((-int(x.group(2), 0) if x.group(1) else int(x.group(2), 0)) & 0xffffffff), ops)
    return (m + " " + ops).strip()


def mnem(t):
    return t.split(" ")[0].lower() if t else "-"


def main():
    g = load(sys.argv[1])
    o = load(sys.argv[2])
    nex = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    cnt = Counter()
    classes = defaultdict(list)
    for off in sorted(o):
        gl, gt = g.get(off, (0, "BAD"))
        ol, ot = o[off]
        gbad = gl == 0
        obad = ol == 0 or ot.startswith("(bad)") or "*unknown*" in ot
        cnt["total"] += 1
        if gbad and obad:
            cnt["both_reject"] += 1
            continue
        if gbad:
            cnt["ref_only"] += 1
            classes["ref only: " + mnem(ot)].append((off, gt, ot, ol))
            continue
        if obad:
            cnt["ghidra_only"] += 1
            classes["ghidra only: " + mnem(gt)].append((off, gt, ot, gl))
            continue
        cnt["both_decode"] += 1
        if gl == ol and exact_norm(gt) == exact_norm(ot):
            cnt["exact"] += 1
            cnt["semantic"] += 1
        elif gl == ol and sem_norm(gt) == sem_norm(ot):
            cnt["semantic"] += 1
            classes["~ " + mnem(ot)].append((off, gt, ot, gl))
        else:
            key = ("LEN " if gl != ol else "DIFF ") + mnem(ot) + " / " + mnem(gt)
            classes[key].append((off, gt, ot, "%d/%d" % (gl, ol)))
    bd = cnt["both_decode"] or 1
    print("compared %d slots: both decode %d, exact %d (%.2f%%), semantic %d (%.2f%%), "
          "ghidra-only %d, ref-only %d, both reject %d"
          % (cnt["total"], cnt["both_decode"], cnt["exact"], 100.0 * cnt["exact"] / bd,
             cnt["semantic"], 100.0 * cnt["semantic"] / bd, cnt["ghidra_only"], cnt["ref_only"],
             cnt["both_reject"]))
    for k in sorted(classes, key=lambda k: (k.startswith("~"), -len(classes[k]))):
        v = classes[k]
        print("  [%d] %s" % (len(v), k))
        for off, gt, ot, ln in v[:nex]:
            print("      %08x len %s  ghidra: %-36s objdump: %s" % (off, ln, gt, ot))


if __name__ == "__main__":
    main()
