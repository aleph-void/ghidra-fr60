#!/usr/bin/env bash
# Import the six public-source FR30 ELFs, decompile, and compare each decoded instruction with
# GNU libopcodes at the same address. GHIDRA_INSTALL_DIR and SLOTDIS must be set.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SAMPLES=$(readlink -f "${1:?samples directory}")
W=$(mkdir -p "${2:-$PWD/fr-real-work}" && cd "${2:-$PWD/fr-real-work}" && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}" "${SLOTDIS:?set SLOTDIS}"

run_one() {
    local f=$1 n
    n=$(basename "$f")
    "$HERE/ghidra-script.sh" elf - "$f" RealCheck.java \
        "$W/$n.sum" "$W/$n.lst" "$W/$n.c" 60 >"$W/$n.log" 2>&1
    test -s "$W/$n.sum"
}

mapfile -t files < <(find "$SAMPLES" -maxdepth 1 -name '*.elf' | sort)
echo "== headless import and decompilation (${#files[@]} files)"
for f in "${files[@]}"; do run_one "$f"; done

for f in "${files[@]}"; do
    n=$(basename "$f")
    read -r base endian < <(python3 "$HERE/elf_exec_image.py" "$f" "$W/$n.img")
    python3 "$HERE/lst2slots.py" "$W/$n.lst" >"$W/$n.slots"
    "$SLOTDIS" fr30 6 "$W/$n.img" -l "$W/$n.slots" -b "$base" -e "$endian" >"$W/$n.ref"
    python3 "$HERE/compare.py" "$W/$n.slots" "$W/$n.ref" 2 >"$W/$n.cmp"
    echo "-- $n"
    grep -E '^(language|functions|instructions|bad-instruction|error bookmarks|decompile)' "$W/$n.sum" | sed 's/^/   /'
    head -1 "$W/$n.cmp" | sed 's/^/   /'
done
