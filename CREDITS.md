# Credits: Fujitsu FR60 / FR81 module

| | |
|---|---|
| Upstream | [desrdev/ghidra-fr60](https://github.com/desrdev/ghidra-fr60), commit `02c151866e6b34a804fedc2b9f0c4736aadac69b` |
| Author | Darren Thompson ([@desrdev](https://github.com/desrdev)); original FR60/FR81 SLEIGH, DVRP loader, analyzer and scripts |
| License | Apache-2.0, preserved from upstream `LICENSE` |
| Reference | GNU binutils 2.45 FR30 disassembler, used as a black-box decode oracle; no binutils code copied into this module |

Ghidra-Rare corrected negative four-bit immediate semantics and display, the ASR2 arithmetic
shift, the 8-bit coprocessor command field and COPSV length. It added an FR30 ELF opinion, fixed
the malformed DWARF mapping, set the extension name and authors, and added decode, constructor,
emulator and real-binary verification. The fork preserves upstream history on branch
`ghidra-rare`.
