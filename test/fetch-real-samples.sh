#!/usr/bin/env bash
# Fetch public C sources (pinned, SHA-256 checked) and build them with fr30-elf-gcc (GCC 14.3,
# newlib 4.5; see build-toolchain.sh) into <outdir>/*.elf, at -O2 and -Os, with DWARF.
# Nothing fetched or built here is committed.
#   test/fetch-real-samples.sh <outdir>
# Sources and licences: Lua 5.4.7 (MIT), zlib 1.3.1 (zlib licence); newlib (BSD-style) and
# libgcc (GPL with the runtime exception) come from the toolchain.
set -euo pipefail
O=$(mkdir -p "$1" && cd "$1" && pwd)
S=$O/src
mkdir -p "$S"
fetch() { # url sha256 file
	[[ -f $S/$3 ]] || curl -fsSL -o "$S/$3" "$1"
	echo "$2  $S/$3" | sha256sum -c --quiet
}
fetch https://www.lua.org/ftp/lua-5.4.7.tar.gz 9fbf5e28ef86c69858f6d3d34eccc32e911c1a28b4120ff3e84aaa70cfbf1e30 lua-5.4.7.tar.gz
fetch https://zlib.net/fossils/zlib-1.3.1.tar.gz 9a93b2b7dfdac77ceba5a558a580e74667dd6fede4585b91eefb60f03b72df23 zlib-1.3.1.tar.gz
(cd "$S" && rm -rf lua-5.4.7 zlib-1.3.1 && tar xzf lua-5.4.7.tar.gz && tar xzf zlib-1.3.1.tar.gz)
fr30-elf-gcc --version | head -1
# newlib's reentrant wrappers call _gettimeofday and _link, which libgloss's fr30 simulator
# library does not provide: link stubs
printf '%s\n' '#include <errno.h>' 'struct timeval; struct timezone;' \
	'int _gettimeofday(struct timeval *t, void *z) { errno = ENOSYS; return -1; }' \
	'int _link(const char *a, const char *b) { errno = ENOSYS; return -1; }' >"$S/stubs.c"
L="-Wl,--no-warn-rwx-segments $S/stubs.c"
Z="adler32.c compress.c crc32.c deflate.c gzclose.c gzlib.c gzread.c gzwrite.c infback.c inffast.c inflate.c inftrees.c trees.c uncompr.c zutil.c"
for v in "O2:-O2" "Os:-Os"; do
	n=${v%%:*} F="${v#*:} -g"
	(cd "$S/lua-5.4.7/src" && fr30-elf-gcc $F $L -std=gnu99 -DLUA_USE_C89 -o "$O/${n}_lua.elf" \
		$(ls ./*.c | grep -v luac.c) -lm)
	for p in example minigzip; do
		(cd "$S/zlib-1.3.1" && fr30-elf-gcc $F $L -include unistd.h -I. -o "$O/${n}_zlib_$p.elf" test/$p.c $Z)
	done
done
# relocatable objects for the relocation handler
(cd "$S/zlib-1.3.1" && fr30-elf-gcc -O2 -g -c -I. inflate.c -o "$O/zlib_inflate.o" &&
	fr30-elf-gcc -O2 -g -c -I. deflate.c -o "$O/zlib_deflate.o")
ls -l "$O"/*.elf "$O"/*.o
