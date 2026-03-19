# AP-120B / FPS-100 Data General Nova/Eclipse Porting Package

## What Is This?

The Floating Point Systems AP-120B (1976) and FPS-100 (1980) are vector/array
processors that attach to a host minicomputer as math coprocessors. They were
originally designed for PDP-11 hosts, but FPS also sold versions with Data
General Nova/Eclipse interfaces.

The **Usagi Electric** community is restoring an FPS-100 board set with a Data
General Nova/Eclipse host. The PDP-11 driver source code exists (`DAPEX.MAC`),
but the **DG Nova driver is lost**. To rewrite it, we need to know which DG
Nova I/O instructions access which FPS registers.

This repository contains:
- **Analysis** of how the PDP-11 register interface maps to DG Nova I/O
- **Hardware documentation** (netlists, wire lists) for the Nova interface
- **A test program** to empirically discover the register mapping
- **A DG Nova assembler** (modified dgasm) to build the test program

## The Problem

On the PDP-11, the FPS has 10 memory-mapped registers (SWR, FN, CTRL, WC,
HMA, APMA, LITES, FMTH, FMTL, ABRT). The host just MOVs data to/from fixed
Unibus addresses.

On the DG Nova, there are no memory-mapped registers. Instead, the Nova has
3 I/O data channels (buffers A, B, C) accessed by DOA/DOB/DOC (write) and
DIA/DIB/DIC (read) instructions, each with 4 flag variants (none, Start,
Clear, Pulse) = 24 total instruction variants.

**The exact mapping of which Nova I/O instruction accesses which FPS register
is unknown.** The original DG driver source is lost, and the interface card
schematics are too low resolution to trace the decode logic. This test program
is designed to discover the mapping empirically.

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
| Register mapping | **UNKNOWN** -- this is what the test program discovers |
| FPS-100 interface | Has REGSEL00-05 (6-bit register select bus) |
| AP-120B interface | Uses direct strobes + HD2REG/REG2HD (no REGSEL) |

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

## Community Links

- [Nakazoto/FloatingPointSystems](https://github.com/Nakazoto/FloatingPointSystems) -- schematics, board scans, netlists
- [Usagi Electric](https://www.youtube.com/@UsagiElectric) -- restoration videos
- [VCFed FPS-100 thread](https://forum.vcfed.org/index.php?threads/floating-point-systems-fps-100-found.1254035/)
- [Bitsavers FPS archive](http://bitsavers.org/bits/FloatingPointSystems/)
