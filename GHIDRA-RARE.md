# Ghidra-Rare notes: Fujitsu FR60 / FR81

This is the Apache-2.0 community module by Darren Thompson ([@desrdev](https://github.com/desrdev/ghidra-fr60)),
tested and corrected for Ghidra 12.1.4. It provides `fr60:BE:16:default` and
`fr81:BE:16:default`; the original DVRP firmware loader and function analyzer remain in the
extension. See [CREDITS.md](CREDITS.md) for provenance and changes.

Install the `FR60` release zip with *File > Install Extensions*, or build with
`GHIDRA_INSTALL_DIR=/path/to/ghidra gradle buildExtension`. FR30 ELF files (machine 84) now
select the FR60 language and the `fcc911` compiler spec on import.

## Verification

| Check | Result |
|---|---|
| FR60 decode vs GNU binutils 2.45 `fr30` | Every 16-bit first halfword with three tails (196,608 slots): 192,882/192,882 shared decodes match exactly. Another 100,000 random six-byte slots: 98,100/98,100 shared decodes match semantically; eight branch targets differ only in 32-bit versus 64-bit sign extension in the printed address. Zero Ghidra-only decodes. GNU's 1,020 / 512 reference-only slots print `???` for reserved registers, which this language rejects. |
| Constructor reachability | 251/258 FR60 and 401/408 FR81 constructors reached. The seven unreached in each are six immediate aliases shadowed by the wider immediate form and an unconditional branch condition shadowed by `BRA`; they add no distinct encoding. |
| FR81 | The FR30 corpus checks the shared core: 192,690 shared slots match exactly in the first-halfword corpus. FR81-only floating-point, BP-relative and long-call forms have no GNU FR30 oracle; 1,143 Ghidra-only slots are expected. Nine core emulator cases also pass on FR81. |
| P-code emulator | Nine hand-computed FR60 cases pass: arithmetic, negative four-bit immediates, condition flags, shifts including arithmetic right shift, word load and store. Nine pass on FR81. A deliberately wrong expectation produces one failure. |
| Real binaries | Six GCC 14.3 ELFs built from pinned Lua 5.4.7 and zlib 1.3.1 source at `-O2` and `-Os`: 3,523 functions, 257,785 decoded instructions. Every function decompiles with zero failures or timeouts, zero bad-instruction bookmarks, and all decoded instructions match GNU libopcodes exactly after removing Ghidra's delay-slot `_` prefix. The 671 error bookmarks are Ghidra's DWARF line importer rejecting negative line numbers from GCC. |
| Build | Ghidra 12.1.4 release zip builds with both `.sla` languages and the Java loader/analyzer. |

The test suite is under `test/`. `test/gen_corpus.py` generates the raw decode corpora;
`test/ghidra-slots.sh` and `test/slotdis.c` dump Ghidra and GNU decodes;
`test/compare.py` scores them. `test/emu_tests.py` and `test/EmuCheck.java` check p-code.
`test/fetch-real-samples.sh` builds the public-source ELFs (not committed), and
`test/real-binaries.sh` imports, decompiles and compares them.

## Limits

- Coprocessor instructions expose their operands but the hardware operation is a user operation;
  behavior depends on the attached coprocessor.
- FR81-only instruction semantics and actual FR60/FR81 firmware have not been checked against
  an independent executable reference. The public GCC toolchain targets the shared FR30 core.
- ELF auto-selection chooses FR60 for machine 84. Choose FR81 explicitly for FR81 code.
- The original DVRP loader targets the PlayStation PSX firmware layout; it has not been tested
  against a freely distributable DVRP firmware image here.
