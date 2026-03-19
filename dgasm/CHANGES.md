# Changes to dgasm (forked from https://github.com/CWood1/dgasm)

## Modifications for FPS-100 / Usagi Electric project

### Bug fixes

- **CMakeLists.txt**: Added `target_include_directories` for source and binary
  dirs so bison/flex-generated headers (parser.h, lexer.h) are found without
  manual `-I` flags.

### New features

- **Semicolon comments**: Added `;` as a comment character (standard DG Nova
  assembly syntax). Previously only `//` was supported.

- **Octal number literals**: Added proper octal parsing for numbers with leading
  zero (e.g., `055` is octal 45 decimal). Previously all bare numbers were
  parsed as decimal via `strtol(..., 0)` which should have worked but the lex
  rules matched `0x` hex before the generic decimal rule. Now octal (`0[0-7]+`)
  is explicitly matched first, then hex (`0x[0-9a-f]+`), then decimal.

- **INTEN/INTDS instructions**: Added `INTEN` (enable interrupts = `NIOS CPU`)
  and `INTDS` (disable interrupts = `NIOC CPU`) as constant-encoding pseudo-ops.
  Other CPU control pseudo-ops (READS, MSKO, INTA) can be written as their I/O
  equivalents: `DIA ac,077`, `DOB ac,077`, `DIB ac,077`.

- **devices.inc**: Standard DG Nova device code definitions file. Includes TTI,
  TTO, RTC, CPU, and FPS (055) for the Floating Point Systems AP-120B/FPS-100
  array processor. Use with `include "devices.inc"` at the top of your program.

### Previously applied fix (already in this fork)

- **DOA accumulator encoding** (opcode.c line 564): The accumulator field is
  correctly shifted to bits 11-12 with `encoding |= accumulator<<11`. The
  original bug had the accumulator being added to the device code field instead.

### Reference

- dgnsdk (https://github.com/Quantx/dgnsdk) `dgnasm_old/` was used as a
  reference implementation to verify instruction encodings. All I/O instruction
  base encodings (NIO, DIA, DOA, DIB, DOB, DIC, DOC) and accumulator placement
  match between the two assemblers.
