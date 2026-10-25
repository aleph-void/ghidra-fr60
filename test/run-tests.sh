#!/usr/bin/env bash
# FR60/FR81 verification. Required: GHIDRA_INSTALL_DIR, SLOTDIS (compiled from slotdis.c),
# and fr30-elf-as/objcopy/nm on PATH. REAL_SAMPLES optionally points to fetch-real-samples.sh's
# output directory. Usage: test/run-tests.sh [workdir]
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
W=$(mkdir -p "${1:-$PWD/fr-test-work}" && cd "${1:-$PWD/fr-test-work}" && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}" "${SLOTDIS:?set SLOTDIS}"

for spec in "$HERE/../data/languages/"*.slaspec; do
    "$GHIDRA_INSTALL_DIR/support/sleigh" "$spec" >"$W/$(basename "$spec").log" 2>&1
done
python3 "$HERE/gen_corpus.py" "$W"
for corpus in first fuzz; do
    "$SLOTDIS" fr30 6 "$W/$corpus.bin" -e big >"$W/o_$corpus.txt"
    "$HERE/ghidra-slots.sh" fr60:BE:16:default "$W/$corpus.bin" 6 "$W/g_$corpus.txt"
    python3 "$HERE/compare.py" "$W/g_$corpus.txt" "$W/o_$corpus.txt" 2 >"$W/cmp_$corpus.txt"
    echo "$corpus: $(head -1 "$W/cmp_$corpus.txt")"
    python3 - "$W/cmp_$corpus.txt" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
m = re.search(r'both decode (\d+).*semantic (\d+).*ghidra-only (\d+)', s)
assert m and m.group(1) == m.group(2) and m.group(3) == '0', s[:400]
assert not re.search(r'^  \[\d+\] (?:LEN|DIFF|ghidra only)', s, re.M), s[:400]
PY
done
head -c 64 /dev/zero >"$W/zero.bin"
for lang in fr60 fr81; do
    "$HERE/ghidra-script.sh" raw "$lang:BE:16:default" "$W/zero.bin" CoverageCheck.java "$W/cov_$lang.txt" 256
    echo "$lang: $(tail -1 "$W/cov_$lang.txt")"
done
python3 "$HERE/emu_tests.py" "$W"
for lang in fr60 fr81; do
    "$HERE/ghidra-script.sh" raw "$lang:BE:16:default" "$W/emu.bin" EmuCheck.java "$W/emu.txt" "$W/emu_$lang.out"
    tail -1 "$W/emu_$lang.out"
    grep -q 'emulator tests: 9 passed, 0 failed' "$W/emu_$lang.out"
done
if [[ -n ${REAL_SAMPLES:-} ]]; then
    "$HERE/real-binaries.sh" "$REAL_SAMPLES" "$W/real"
fi
