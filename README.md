# AP-120B / FPS-100 Data General Nova/Eclipse Porting Package

## What Is This?

The Floating Point Systems AP-120B (1976) and FPS-100 (1980) are vector/array
processors that attach to a host minicomputer as math coprocessors. They were
originally designed for PDP-11 hosts, but FPS also sold versions with Data
General Nova/Eclipse interfaces.

The **Usagi Electric** community is restoring an FPS-100 board set with a Data
General Nova/Eclipse host. The PDP-11 driver source code exists (`DAPEX.MAC`),
but the **DG Nova driver is lost**. This repository contains the complete
replacement software stack: register mapping analysis, a SimH emulator with
full microcode execution, a DG Nova DAPEX driver, an ANSI C driver/API layer,
a linker replacement, and test harnesses.

This repository contains:
- **SimH AP-120B/FPS-100 emulator** (`nova_fps.c`) with full microcode execution engine
- **DG Nova DAPEX driver** (`dapex_dg.asm`) -- all 25 routines, complete replacement for PDP-11 DAPEX.MAC
- **ANSI C driver** (`fdapex.c/h`) and **host-independent API** (`iapex.c/h`)
- **LNK100 linker replacement** (`lnk100.py`) -- links all 9 APO libraries (11,420 instructions, 596 symbols)
- **LOD100 loader replacement** (`lod100.py`) -- load modules, overlays, PS partition tables, TCBs, HASI routines
- **Register mapping analysis** derived from 280B schematic trace
- **Hardware documentation** (netlists, wire lists) for the Nova interface
- **Test programs** -- hardware probe, SimH pipeline tests, HSR library tests
- **A DG Nova assembler** (modified dgasm) to build the test program

## The Problem

On the PDP-11, the FPS has 10 memory-mapped registers (SWR, FN, CTRL, WC,
HMA, APMA, LITES, FMTH, FMTL, ABRT). The host just MOVs data to/from fixed
Unibus addresses.

On the DG Nova, there are no memory-mapped registers. Instead, the Nova has
3 I/O data channels (buffers A, B, C) accessed by DOA/DOB/DOC (write) and
DIA/DIB/DIC (read) instructions, each with 4 flag variants (none, Start,
Clear, Pulse) = 24 total instruction variants.

**The register mapping has been derived from detailed schematic analysis** of the
280B Nova Eclipse I/O Adapter (512-3280-004, Rev B). The 280B uses a standard
2-to-4 NAND decode of the DG flag bits (CLR/STRT) within each DOx channel:

| Channel | none | S | C | P |
|---------|------|---|---|---|
| DOA (write) | SWR | FN | CTRL | INT/APIRT |
| DOB (write) | WC | HMA | APMA | DMA start |
| DOC (write) | FMTH | FMTL | — | — |
| DIA (read) | FN | SWR | LITES | APMA |
| DIB (read) | FMTH | — | — | — |
| DIC (read) | FMTL | — | — | — |

See `adapter.md` for the full schematic trace and `dg_register_mapping.md`
for the complete analysis. The test program below can verify this on hardware.

## The Test Program (`fps_probe.asm`)

A 5-phase DG Nova assembly program that systematically probes the FPS
interface at device code 055 (octal). It halts after each probe so the
operator can examine the CPU accumulators and the FPS front panel.

### Phase 1: Find the FN (Function) Register Read Channel
Reads all 12 DI variants after reset. The FN register should have a non-zero
value (AP halted bit in MSB). The DI instruction that returns a non-zero value
is the one that reads FN status.

### Phase 2: Find the SWR Write and FN Write Channels
Writes 0xFFFF to each of the 12 DO variants, then reads all three DI base
channels after each write. Look for:
- Which DO changes the LITES LEDs on the FPS front panel?
- Which DI shows a changed value after each DO?

### Phase 3: FN Command Protocol Verification (Key Test)
The Processor Handbook shows the host loads programs by alternating SWR writes
(data) and FN writes (commands). This phase tests all 6 possible DO-pair
combinations (DOA+DOB, DOA+DOC, DOB+DOA, DOB+DOC, DOC+DOA, DOC+DOB) for the
SWR+FN protocol. For each pair:
1. Write 0xA5A5 to SWR candidate (first DO)
2. Write DEP-into-PSA command to FN candidate (second DO)
3. Write EXAM-PSA command to FN candidate
4. Read all three DI channels to find the EXAM result (should be 0xA5A5)

**The pair that produces 0xA5A5 in one of the DI reads is the correct
SWR/FN mapping.** This is the single most important test.

### Phase 4: DMA Register Discovery
Tests flag variants (Start, Pulse) of each DO channel with a safe pattern
(0xA5A5, no HDMA start bit) to find which DO+flag combinations access the
DMA registers (CTL, WC, HMA, APMA).

### Phase 5: DONE/BUSY Flag Behavior
Tests the standard DG DONE/BUSY flag flip-flops after NIOC (Clear), NIOS
(Start), and NIOP (Pulse).

### How to Run
1. Build the assembler: `cd dgasm && mkdir build && cd build && cmake .. && make`
2. Assemble: `./dgasm/build/dgasm -o fps_probe.bin fps_probe.asm`
3. Load `fps_probe.bin` at Nova address 0100 (octal)
4. Start execution at 0100
5. At each HALT, examine AC0 (and AC1/AC2/AC3 for Phases 3-4)
6. Press CONTINUE to advance to the next probe
7. There are ~43 halts total. Record all values.

### Interpreting Results
- **Phase 1**: The halt where AC0 >= 0x8000 (or any non-zero) identifies the
  DI instruction that reads FN status
- **Phase 2**: The halt where FPS LEDs change identifies the DO that writes
  LITES. AC1/AC2/AC3 show what DIA/DIB/DIC read after each write.
- **Phase 3**: The halt where AC1, AC2, or AC3 = 0xA5A5 identifies the
  correct SWR/FN DO-pair. **This is the key result.**
- **Phase 4**: Tests flag variants to find DMA register access
- **Phase 5**: AC0 encodes flags: 0=both clear, 1=BUSY set, 2=DONE set, 3=both

Results from all 12 Phase 1 reads are also stored at zero-page addresses
050-063 (octal) for post-mortem examination.

## Hardware Documentation

### Netlists (from [Nakazoto/FloatingPointSystems](https://github.com/Nakazoto/FloatingPointSystems))
- `4448_APIF_netlist.txt` -- FPS-100 AP Interface board **(Nova version)**.
  Has REGSEL00-05 register select lines unique to the Nova interface.
- `4421_PDPIF_netlist.txt` -- FPS-100 PDP-11 Interface board (for comparison).
- `4429_FMT_netlist.txt` -- Formatter board (shared between PDP-11 and Nova).

### Wire List (from [bitsavers](http://bitsavers.org) via [archive.org](https://archive.org))
- `AP-120B_Nova_E_31Card_Wirelist_198204.pdf` -- 82-page backplane wire list
  for a GE AP-CT (CT scanner) AP-120B with Nova Eclipse host. Shows every
  signal between the Nova I/O adapter and the AP backplane, including:
  - `LDSR*` (Load Switch Register), `LDFN*` (Load Function Register)
  - `FN2HD` (FN to Host Data), `SR2HD`, `LT2HD` (read strobes)
  - `HD2REG` / `REG2HD` (master write/read direction strobes)
  - `HMACLK*`, `HCTLCLK*`, `HDMACLK*` (register load clocks)
  - `CTL10`, `CLT08*`, `CTL5INTR*` (individual CTRL register bits)
  - `WC=0*` (DMA word count zero = transfer complete)

### Processor Handbook (OCR'd)
- `860-7259-003_procHbkFeb79_ocr.pdf` -- AP-120B Processor Handbook with
  searchable OCR text. **Critical**: Section 4.2 describes SWR/FN/LITES
  registers, Section 4.4 describes DMA registers, Section 4.7 shows the
  exact loading procedure (alternating SWR and FN writes). Contains complete
  FN command encoding and CTL register bit layout.

### PDP-11 Reference Source Code
- `DAPEX.MAC` -- The PDP-11 driver that must be rewritten for DG. Contains the
  complete register map, SWR/FN handshake protocol, DMA setup, and SENDER routine.
- `DRIVER.MAC` -- PDP-11 RSX-11M device driver (lower level).
- `FDAPEX.FTN` -- FORTRAN driver layer (mostly host-independent).
- `ADUTIL.MAC` -- PDP-11 host utility functions (IOR16, INOT16, etc.)
  called by the FORTRAN layer.

## Analysis Document

`dg_register_mapping.md` contains the full technical analysis:
- PDP-11 vs DG Nova I/O architecture comparison
- 280B Nova I/O Adapter schematic findings (decode logic, signal names)
- FPS-100 vs AP-120B interface differences (REGSEL vs direct strobes)
- DG Nova I/O instruction encoding reference
- Proposed (speculative) register mapping with rationale
- Verification methods
- Archival leads for finding the original DG driver source

## Key Facts

| | |
|---|---|
| FPS device code | 055 (octal) on DG Nova I/O bus |
| AP-120B / FPS-100 | Architecturally identical (same instruction set) |
| Interface type | PDP-11 uses Unibus memory-mapped I/O; Nova uses DOA/DOB/DOC programmed I/O |
| Register mapping | **Derived from 280B schematics**, verified in SimH emulator |
| FPS-100 interface | Has REGSEL00-05 (6-bit register select bus) |
| AP-120B interface | Uses direct strobes + HD2REG/REG2HD (no REGSEL) |
| SimH emulator | Full microcode execution, DMA with float conversion, FN DEP/EXAM |
| DG DAPEX driver | All 25 routines implemented in DG Nova assembly |
| ANSI C driver | Complete fdapex.c + iapex.c host-independent API |
| Linker | lnk100.py links all 9 APO libraries (11,420 instructions) |
| Tape forensics | Tape complete, extraction faithful, TMRAM routines never on tape |

## DG Nova Assembler (`dgasm/`)

Modified fork of [CWood1/dgasm](https://github.com/CWood1/dgasm). Changes
documented in `dgasm/CHANGES.md`:
- Fixed CMakeLists.txt include paths
- Added `;` semicolon comments (standard DG assembly syntax)
- Added octal number literals (`055` parsed as octal)
- Added `INTEN`/`INTDS` pseudo-ops
- Standard device definitions in `dgasm/devices.inc` (FPS=055, TTI, TTO, etc.)

Build: `cd dgasm && mkdir build && cd build && cmake .. && make`

Requires: C compiler, cmake, flex, bison.

## DG Nova DAPEX Driver (`dapex_dg.asm`)

Complete DG Nova assembly rewrite of the PDP-11 `DAPEX.MAC` driver. All 25
routines implemented using the schematic-derived register mapping. Includes
the two-step scratch pad DEP protocol (SPD pointer + SPFN value) matching
the real DAPEX.MAC implementation.

## ANSI C Driver and API

- **`fdapex.c/h`** -- C equivalent of FDAPEX.FTN, complete with two-step
  scratch pad DEP, DMA setup, FN DEP/EXAM protocol
- **`iapex.c/h`** -- C equivalent of IAPEX.FTN host-independent API:
  `apex()`, `apinit()`, `apwait()`, `apput()`/`apget()`, and all other
  APEX entry points

## LNK100 Linker Replacement (`lnk100.py`)

Python replacement for the missing LNK100 linker. Links all 9 APO libraries
from the FPS-100 software archive: 11,420 microcode instructions, 596 symbols.

## LOD100 Loader Replacement (`lod100.py`)

Python replacement for the missing LOD100 loader, built from the LOD100
Reference Manual (860-7423-000) cross-checked against `FSLMLD` in
`FDAPEX.FTN` -- the routine that actually parses load modules. Where the
manual and the code disagree on field naming, the code wins.

- load module blocks: code to program source memory (4 host words per 64-bit
  instruction) and to main data (2 words per value), data blocks including
  the 38-bit triple split, information block, and both the logical and
  terminating end blocks
- overlay support: `TREE` structure parsing, PS allocation, PS partition
  table, per-task overlay tables (8-word entries), and task communication
  blocks (150 main-data words) with ready-queue linkage
- HASI ADC/UDC host interface routines from each module's formal parameter
  block
- the LOD100 command language, plus command-line flags
- host-resident FORTRAN and binary output forms

Not implemented: DBDB/DBIB data-block object records (the shipped `.APO`
libraries contain none) and ISR vector wiring, which belongs to APX100.

### Why both tools were missing

Neither LNK100 nor LOD100 is on the FPS-100 software tape. The tape is a
12-Sep-1986 FLX dump of a disk holding the unpacked distribution sources --
not the FPS distribution tape (which per INSTAL.TXT §2.1 carries MAGTAP as
file 0 and a names file with pass numbers), and not a post-install disk
(there are zero build products among its 182 files). The install was never
run on that disk, so the deletions in `PDS100.CMD` do not explain the
absence. LNK100 and LOD100 are missing both source *and* build driver
(`LNK100.FTN`, `LNK10.CMD`, `LOD100.FTN`, `LOD10.CMD`, plus `LIB100.CMD`)
while all six sibling PDS tools have both -- a missing product tier.
`INSTAL.TXT` §9.13 and §9.14 do reproduce the two build command files
verbatim, and §9.14's overlay descriptor lists LOD100's ~50 module names.

## SimH AP-120B Emulator (`nova_fps.c`)

A SimH device plugin that emulates the FPS AP-120B / FPS-100 array processor.
Runs as device 055 on the SimH Nova simulator.

**Working features:**
- Schematic-derived I/O mapping: DOA+flag->SWR/FN/CTRL/INT,
  DOB+flag->WC/HMA/APMA/DMA, DOC+flag->FMTH/FMTL,
  DIA+flag->FN/SWR/LITES/APMA, DIB->FMTH, DIC->FMTL
- All host interface registers (SWR, FN, LITES, CTL, WC, HMA, APMA, FMTH, FMTL)
- FN command protocol (DEP, EXAM, START, STOP, CONT, STEP, RESET)
- Program Store loading via panel DEP (4 x 16-bit words per 64-bit instruction)
- Three-subdevice DONE/BUSY model: RUN (dev 055), DMA (dev 056), CTL05 (dev 057)
- SKPDN/SKPBN skip instructions work on all three subdevices
- AP instruction execution: 24-field 64-bit microinstruction decode
- S-pad operations: ADD, SUB, MOV, AND, OR, EQV, CLR, INC, DEC, COM, LDSPI
- Branch conditions: all 16 types (integer and float)
- JMP/JSR/RET with subroutine return stack
- HALT (both DF=0 and DF=1)
- SPEC ops: HALT, JMP, JSR, SETEXIT, SWDB
- 38-bit FPS floating point: ADD, SUB, MUL with normalization
- Floating adder pipeline: FAB1->FAB2->FA with unconditional FAB2->FA shift each cycle
- FADD/FSUB/FSUBR/FEQV/FAND/FOR with A1/A2 input selection
- A1 sources: 1=FM, 4=TMR (not MD) (from SIM100.FTN)
- MI field: MI=1=FA, MI=2=FM, MI=3=DPBS (from SIM100.FTN)
- Floating multiplier with M1/M2 input selection
- Data Pad X/Y: 32 entries each, DPA+index addressing
- DPBS=6 SPFN bus (normalized float conversion)
- MDPX (modify data pad read for integer->float)
- Main Data memory: 64K x 64-bit, read/write via MI field
- Table Memory ROM: 2K sin/cos tables (generated mathematically)
- DMA engine with format conversion (38-bit float <-> IEEE 32-bit, 32-bit int, 16-bit int)
- IEEE 32-bit <-> FPS 38-bit float conversion: mantissa shift <<3/>>3, exponent bias 387
- Bit reversal (FFT address scrambling)
- I/O operations: LDDA, OUT, IN, LDOMA, LDDPA, SWDB
- Two-step s-pad DEP protocol (SPD pointer + SPFN value, matching real DAPEX.MAC)
- Branch displacement formula: PSA+1+DISPF-17 (from SIM100.FTN)
- JMP/JSR PC-relative: PSA+VALUE (no +1 bias, from SIM100.FTN)
- SPS=8 JMP/JSR vs CLR conflict resolved (use_value check)

**Bug fixes (March 2026):**
- DOBP now properly clears DMA DONE on subdevice 1 when starting a new transfer
- 38-bit float <-> IEEE 32-bit conversion corrected: mantissa shift was <<4/>>4,
  fixed to <<3/>>3; exponent bias correction from 384 to 387
- Flag side-effect ordering fixed: flags processed before data transfer to prevent
  DOAS+START from clearing DONE after halt

**Not yet implemented:**
- Memory read pipeline (3-stage MDB1->MDB2->MDB3->MDR, from SIM100 lines 1327-1334)
- Table Memory read pipeline (2-stage TMB1->TMB2->TMR, from SIM100 line 40000)
- LDTMA operation (loads TMA from bus value, different from TMA_OP field)

These pipelines are needed for correct execution of production HSR library
routines, which rely on precise pipeline timing.

**To use:** Copy `nova_fps.c` to `simh/NOVA/`, add to makefile NOVA sources
and `nova_sys.c` device list, rebuild SimH. Enable with `set fps enabled`.

**Tested:** All 12 register read/write paths verified in SimH. S-pad arithmetic
(LDSPI, ADD, SUB, MOV) verified correct. Panel DEP/EXAM protocol verified.
Synchronous execution on START. DONE/BUSY flag scoping verified (DOA S/C
affects RUN only, DOB S/C does not affect RUN). Full VADD pipeline test
passes (see below). Production HSR VADD test produces non-zero results but
values not yet correct due to missing memory/TM pipelines.

## Test Suite

### `gen_vadd_test.py` -- Single FADD Pipeline Test (PASSES)

Python script that generates SimH command files exercising the full AP pipeline.
The generated test (`test_vadd.simh`) performs:

1. **FN DEP protocol** -- loads hand-crafted FADD microcode into Program Store
   and sets up scratch pad registers via the SWR/FN deposit sequence
2. **DMA Host->AP** -- transfers IEEE 32-bit float data from host memory to AP
   Main Data with automatic IEEE-to-FPS 38-bit float conversion
3. **AP microcode execution** -- runs the FADD program on the AP
4. **DMA AP->Host** -- transfers results back with FPS 38-bit-to-IEEE 32-bit
   float conversion
5. **Verification** -- checks that 1.5 + 2.5 = 4.0

### `gen_real_vadd_test.py` -- 12-Instruction VADD Loop

Tests a VADD loop with scratch pad control flow. Needs pipeline-aware scheduling.

### `gen_hsr_vadd_test.py` -- Production HSR VADD Test

Tests the actual 20-instruction VADD microcode from `BAAHSR.MAC`. Produces
non-zero results but values not yet correct due to missing memory/TM read
pipelines in the emulator.

### `test_subdev.simh` -- Subdevice DONE/BUSY Verification

Verifies SKPDN/SKPBN behavior on all three subdevices (RUN dev 055,
DMA dev 056, CTL05 dev 057).

### `lnk100.py` -- Linker Verification

Also serves as a validation tool: parses and links all 9 APO libraries,
reporting symbol counts and instruction totals.

## Files In This Repository

### New Software
- `nova_fps.c` -- **SimH AP-120B/FPS-100 emulator** (full microcode execution engine)
- `nova_fps_load.c` -- SimH FPS device loader helper
- `dapex_dg.asm` -- **DG Nova DAPEX driver** (all 25 routines)
- `fdapex.c` / `fdapex.h` -- **ANSI C driver** (C equivalent of FDAPEX.FTN)
- `iapex.c` / `iapex.h` -- **ANSI C host-independent API** (C equivalent of IAPEX.FTN)
- `lnk100.py` -- **LNK100 linker replacement** (links all 9 APO libraries)
- `lod100.py` -- **LOD100 loader replacement** (load modules, overlays, HASI)
- `gen_vadd_test.py` -- Test generator: single FADD pipeline test (PASSES)
- `gen_real_vadd_test.py` -- Test generator: 12-instruction VADD loop
- `gen_hsr_vadd_test.py` -- Test generator: production 20-instruction HSR VADD
- `test_vadd.simh` -- SimH test script: full pipeline verification
- `test_subdev.simh` -- SimH test script: SKPDN/SKPBN subdevice verification
- `fps_probe.asm` -- DG Nova hardware test program to discover register mapping
- `dgasm/` -- Modified DG Nova assembler

### Analysis Documents
- `adapter.md` -- Detailed 280B schematic trace (tile-by-tile)
- `dg_register_mapping.md` -- Complete DG register mapping analysis
- `microcode.md` -- AP microcode instruction format reference

### Reference Hardware Documentation
- `860-7259-003_procHbkFeb79_ocr.pdf` -- AP-120B Processor Handbook (OCR'd)
- `4448_APIF_netlist.txt` -- FPS-100 AP Interface (Nova version) netlist
- `4421_PDPIF_netlist.txt` -- FPS-100 PDP-11 Interface netlist (comparison)
- `4429_FMT_netlist.txt` -- Formatter board netlist (shared)
- `AP-120B_Nova_E_31Card_Wirelist_198204.pdf` -- GE AP-CT Nova E wire list

### Reference PDP-11 Source Code
- `DAPEX.MAC` -- PDP-11 RSX-11M host-dependent driver (reference for DG port)
- `DRIVER.MAC` -- PDP-11 RSX-11M device driver
- `FDAPEX.FTN` -- FORTRAN driver layer (mostly portable)
- `ADUTIL.MAC` -- PDP-11 host utility functions (bit manipulation)

## What's Remaining

- **Memory read pipeline** (3-stage MDB1->MDB2->MDB3->MDR, from SIM100 lines 1327-1334) --
  needed for correct HSR library execution
- **Table Memory read pipeline** (2-stage TMB1->TMB2->TMR, from SIM100 line 40000)
- **LDTMA operation** (loads TMA from bus value, different from TMA_OP field)
- **TMRAM routines** (MTMOV/TMMOV/MTTMUL) -- from TMR option, never on tape
- **FPS-100 REGSEL interface determination** -- whether single-cycle or two-step

## Community Links

- [Nakazoto/FloatingPointSystems](https://github.com/Nakazoto/FloatingPointSystems) -- schematics, board scans, netlists
- [Usagi Electric](https://www.youtube.com/@UsagiElectric) -- restoration videos
- [VCFed FPS-100 thread](https://forum.vcfed.org/index.php?threads/floating-point-systems-fps-100-found.1254035/)
- [Bitsavers FPS archive](http://bitsavers.org/bits/FloatingPointSystems/)
