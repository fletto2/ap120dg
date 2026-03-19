# FPS-100 Data General Nova/Eclipse Register Mapping Analysis

## Summary

This document analyzes how the PDP-11 memory-mapped register interface of the
FPS-100 maps to Data General Nova/Eclipse programmed I/O instructions. The
analysis is based on:

- 280B Nova Eclipse I/O Adapter schematics (512-3280-00A, 5 pages)
- 4448 AP I/F (Nova version) netlist and schematics (512-3448-010)
- 4421 PDP-11 I/F netlist (for comparison)
- 4429 Formatter netlist
- DAPEX.MAC and DRIVER.MAC source code (PDP-11 reference implementation)
- Adversarial LLM analysis of the decode architecture (March 2026)

## Background: Two Different I/O Models

### PDP-11 (Unibus) - Memory-Mapped I/O

The PDP-11 uses memory-mapped I/O. Each FPS register appears at a fixed offset
from the device's CSR (Control/Status Register) base address:

| Offset (octal) | Register | Description |
|---|---|---|
| 000 | FMTH | Format High |
| 002 | FMTL | Format Low |
| 100 | WC | Word Count (DMA) |
| 102 | HMA | Host Memory Address (DMA) |
| 104 | CTRL | Control register |
| 106 | APMA | AP Memory Address (DMA) |
| 110 | SWR | Switch Register (host->AP data) |
| 112 | FN | Function Register (AP->host status) |
| 114 | LITES | Lights register |
| 116 | ABRT | Reset/Abort |

The PDP-11 simply MOVs data to/from these addresses. The Unibus decodes the
address and generates the appropriate register select.

### Data General Nova/Eclipse - Programmed I/O

The DG Nova uses I/O instructions with three data channels per direction:

**Output (host writes to device):**
- `DOA ac,dev` -- Data Out to buffer A: write accumulator to device
- `DOB ac,dev` -- Data Out to buffer B: write accumulator to device
- `DOC ac,dev` -- Data Out to buffer C: write accumulator to device

**Input (host reads from device):**
- `DIA ac,dev` -- Data In from buffer A: read device into accumulator
- `DIB ac,dev` -- Data In from buffer B: read device into accumulator
- `DIC ac,dev` -- Data In from buffer C: read device into accumulator

**Flag control (combinable with any DO/DI or NIO):**
- `S` (Start) -- sets BUSY, clears DONE
- `C` (Clear) -- clears both BUSY and DONE
- `P` (Pulse) -- device-specific pulse

**Key architectural fact:** "Each I/O device will have three independent buffers
available for programming. These are referenced by the letters A, B, and C.
Not all devices use all three available buffers."

**Problem:** 10 PDP-11 registers must be accessed through only 3 DG data
channels plus S/C/P flag variants.

## Hardware Findings

### 280B Nova Eclipse I/O Adapter (in DG chassis)

The 280B board sits in the DG backplane and decodes I/O instructions for the FPS.

**DG bus inputs** (from schematic page 1, top):
- DS0\*-DS5\*: Device select bits -> decoded by two 7442 BCD-to-decimal decoders
- DATOA, DATOB, DATOC: Data Out A/B/C strobes
- DATIA, DATIB, DATIC: Data In A/B/C strobes
- CLR, STRT: Flag control (Clear/Start)

**Outputs to FPS backplane** (from schematic page 1, bottom):
- LDSR\* -- Load Switch Register (write SWR)
- LDFN\* -- Load Function Register (write FN)
- HWCCLK\* -- Host Word Count Clock (write WC)
- HMACLK\* -- Host Memory Address Clock (write HMA)
- HADRCLK\* -- Host Address Register Clock (write APMA)
- HDMACLK\* -- Host DMA Clock (DMA start)
- HCTCLK\* -- Host Control Clock (write CTRL)
- INTCLK\* -- Interrupt Clock
- BDCLK\* -- Board Data Clock
- AP0-AP3: AP unit select (active high and low versions)

**Additional signals** (from schematic page 2):
- DOAQ -- "DOA Qualified": DOA gated with device select 055, the clean
  internal strobe (not the raw DATOA from the bus)
- APDIR\* -- "AP Direction": controls bidirectional bus transceivers.
  Low = write (DOx cycle, Nova->AP), High = read (DIx cycle, AP->Nova)

**DG flag logic** (from schematic page 4):
- RUN DONE / RUN BUSY flip-flops (A6, 7474)
- DMA DONE / DMA BUSY flip-flops (A7, 7474)
- NIOCAP0-2, NIOSAP0-1: NIO Clear/Start decoded per AP unit

**Decode logic** (from schematic page 1, middle):
The 280B decodes DOA/DOB/DOC combined with device select through 7410 (triple
3-input NAND) gates (C6, C1) and 74S74 flip-flops (C7, C5), then through
74S02 NOR gates (D6, D8, D5) to generate the individual register strobes.
Each `(DATOx & DEV_SEL & FLAG)` combination generates a unique strobe.

### 4448 AP I/F Board (Nova version, in FPS chassis)

The 4448 replaces the 4421 PDP-11 I/F in a Nova-hosted system. Key signals
unique to the Nova version (not present on PDP-11 I/F):

| Pin | Signal | Description |
|---|---|---|
| B54 | REGSEL00 | Register Select bit 0 |
| B56 | REGSEL01 | Register Select bit 1 |
| B57 | REGSEL02 | Register Select bit 2 |
| B59 | REGSEL03 | Register Select bit 3 |
| B61 | REGSEL04 | Register Select bit 4 |
| B65 | REGSEL05 | Register Select bit 5 |

**Write strobes** (active low, shared with PDP-11 version):
- LDSR\* (B74) -- Load Switch Register
- LDFN\* (B72) -- Load Function Register
- HADRCLK\* (B13) -- Host Address Register Clock (APMA)

**Read-back strobes** (active low, select which register drives the HD bus):
- FN2HD\* (B90) -- Function Register to Host Data
- SR2HD\* (B92) -- Switch Register to Host Data
- LT2HD\* (B88) -- Lights Register to Host Data
- HADR2HD\* (B91) -- Host Address Register to Host Data

### Common Signals (same on both PDP-11 and Nova versions)

Both the 4421 and 4448 share the same interface to the rest of the FPS:
- HD00-HD15: Host Data bus (16-bit)
- HST00-HST15: Host Status bus
- DMA00-DMA15: DMA data bus
- LDSR\*, LDFN\*, HADRCLK\*: Register write strobes
- FN2HD\*, SR2HD\*, LT2HD\*, HADR2HD\*: Register read strobes
- Various DMA control signals

## Processor Handbook Findings (Key Discovery)

The OCR'd AP-120B Processor Handbook (860-7259-003, Feb 1979) reveals that the
FPS host interface is fundamentally a **two-register command protocol**, not a
register file:

### FN Register is a Command Register

The FN register is **writable** by the host for commands AND **readable** for
status. When written, it triggers panel operations (START, STOP, DEP, EXAM,
etc.). When read, it returns AP status (halted, SWR acknowledge, etc.).

FN register bit layout (bit 0 = MSB, DG/FPS convention):

| Bit | Name | Function |
|---|---|---|
| 0 | STOP/HALTED | Write: stop AP. Read: 1 if AP halted. |
| 1 | START | Start execution at address in SWR |
| 2 | CONT | Continue from current PSA |
| 3 | STEP | Single-step one instruction |
| 4 | RESET | Hard reset AP |
| 5 | EXAM | Examine register selected by REG SELECT |
| 6 | DEP | Deposit SWR contents into selected register |
| 7 | BREAK | Set breakpoint at SWR address |
| 8-9 | INC | Post-increment: 0=none, 1=MA, 2=DPA, 3=TMA |
| 10-11 | WORD | Which 16-bit portion of 38/64-bit register (0-3) |
| 12-15 | REG SELECT | Which register to examine/deposit (0-17 octal) |

REG SELECT values: 0=PSA, 1=SPD, 2=MA, 3=TA(TMA), 4=DPA, 5=SPFN,
6=AP STATUS, 7=DA, 10=PS(by TMA), 11=CB, 12=DPX, 13=DPY, 14=DPZ,
15=MD(by MA), 16=SPFN(exam), 17=TM(by TMA)

### Loading Procedure Uses Only SWR + FN

The handbook's program loading example (section 4.7) writes ONLY to SWR
and FN. No direct register writes to CTL, WC, HMA, or APMA during loading:

```
0 -> SWR              ; Put 0 in switches
001003 -> FN           ; DEP into register 3 (TMA): sets TMA=0
(bits 0-15) -> SWR    ; Program word bits 0-15
001010 -> FN           ; DEP into PS(by TMA), WORD=0: write PS bits 0-15
(bits 16-31) -> SWR
001030 -> FN           ; DEP into PS(by TMA), WORD=1: write PS bits 16-31
(bits 32-47) -> SWR
001050 -> FN           ; DEP into PS(by TMA), WORD=2: write PS bits 32-47
(bits 48-63) -> SWR
001370 -> FN           ; DEP into PS(by TMA), WORD=3, INC=TMA: write bits 48-63 + advance TMA
```

This means the host alternates SWR and FN writes rapidly. **Both must be
directly accessible via single I/O instructions.**

### CTL Register Complete Bit Layout

| Bit | Name | Function |
|---|---|---|
| 0 | WC=0 | Word count zero (READ ONLY) |
| 1 | INTR AP | Interrupt the AP (= APIRT in DAPEX) |
| 2 | TAPWC | Interrupt AP when DMA done |
| 3 | IHHALT | Enable host interrupt on AP halt |
| 4 | IHWC | Enable host interrupt when DMA done |
| 5 | IHENB | Interrupt Host Enable (host-only writable) |
| 6 | FERR | Format error (READ ONLY) |
| 7 | DLATE | Data late (READ ONLY) |
| 8 | CC | Consecutive cycle (block DMA) |
| 9 | APDMA | Enable AP-side DMA |
| 10 | WRTHOST | Direction: 1=AP->host, 0=host->AP |
| 11 | DECAPMA | 1=decrement APMA, 0=increment |
| 12 | DECHMA | 1=decrement HMA, 0=increment |
| 13-14 | FMT | Format control |
| 15 | HDMA | Start DMA (write) / DMA active (read) |

Cross-reference with DAPEX.MAC confirms bit numbering:
- DAPEX APIRT=040000 (PDP-11 bit 14) = Handbook bit 1 (MSB convention)
- DAPEX IHHALT=010000 (PDP-11 bit 12) = Handbook bit 3
- DAPEX HDMAGO=000001 (PDP-11 bit 0) = Handbook bit 15

### Bit Numbering Convention

The handbook uses **bit 0 = MSB** throughout, matching the DG Nova convention.
This is opposite to PDP-11 (bit 0 = LSB). The same physical wire carries
the MSB in both systems -- the only difference is naming.

### Implications for Nova Mapping

The host interface is fundamentally a **command/data protocol over SWR and FN**:
1. Host writes data to SWR (the "data" register)
2. Host writes commands to FN (the "command" register)
3. Host reads status from FN (the "status" register)
4. For DMA, host also writes CTL, WC, HMA, APMA directly

The most likely Nova mapping:
- **DOA -> SWR** (data writes, most frequent)
- **DOB -> FN** (command writes)
- **DIA -> FN** (status reads)
- **DIB -> LITES** (diagnostic reads)
- DOC / flag variants -> CTL, WC, HMA, APMA for DMA setup

This explains why the loading procedure only needs two registers: everything
is accessed through the SWR/FN panel command mechanism. DMA registers are
only needed when setting up block transfers.

## Architecture: Hybrid — Model-Dependent (Revised)

Critical review (including adversarial analysis with multiple LLMs)
reveals that the register access mechanism is **more complex than initially
concluded** and differs between the AP-120B and FPS-100.

### AP-120B Nova Interface

The GE AP-CT wire list shows the AP-120B uses:
- **Dedicated strobes** for commonly-used registers: LDSR\*, LDFN\*
  (write SWR/FN), and FN2HD, SR2HD, LT2HD (read FN/SWR/LITES)
- **Master direction strobes** HD2REG and REG2HD for data bus direction
- **Individual control bits** CTL10, CLT08\*, CTL5INTR\* exposed as
  separate signals (atomic set/clear without read-modify-write)
- **Buffer paths** BH2HD, BL2HD\* (likely FMTH/FMTL read paths)
- **No REGSEL lines** — register selection appears to be either direct
  decode or implicit in the I/O instruction

This suggests the AP-120B uses **primarily direct decode** with dedicated
hardware paths for each register.

### FPS-100 Nova Interface (4448 board)

The FPS-100's 4448 AP I/F board has:
- **REGSEL00-05** (6-bit register select bus) — NOT present on AP-120B
- The same dedicated strobes (LDSR\*, LDFN\*, FN2HD, SR2HD, etc.)
- HADRCLK\*, HWCCLK\* — dedicated clocks for APMA and WC registers
  that the AP-120B wire list lacks

**Why REGSEL exists on FPS-100 but not AP-120B:**
The FPS-100 is a miniaturized AP-120B. The 4448 board consolidates
register decoding that was distributed across multiple boards in the
AP-120B. REGSEL allows the 280B I/O adapter to communicate the decoded
register address to the 4448, which then generates the appropriate
individual strobes internally. In the AP-120B, the register strobes
travel directly on the backplane from the I/O adapter.

**This means REGSEL is a decoded output (not a latched address) on the
FPS-100.** The 280B decodes each DOx+flag combination into a REGSEL
code AND the appropriate strobe simultaneously. The 4448 uses REGSEL
to route data to the correct register. This is still single-cycle.

However, **we cannot rule out a two-step mechanism** without better
schematic evidence. The 6 REGSEL bits (64 values) for only ~10 registers
remains unexplained by pure direct decode. Possible explanations:
- Future expansion / shared with other FPS models
- Sub-register addressing (e.g., high/low words of 38-bit registers)
- REGSEL encodes both register AND direction, using more bits

### Revised Architecture Model

```
Nova DOA/B/C + DEV(055) + S/C/P Flag
    |
    v
280B Decode Logic (7410 NANDs + 74S74 FFs + 74S02 NORs)
    |
    +---> Named strobes (LDSR*, LDFN*, HMACLK*, etc.)  [AP-120B: on backplane]
    +---> REGSEL00-05                                   [FPS-100: to 4448 board]
    +---> APDIR* / HD2REG / REG2HD (direction control)
    |
    v
Register access (write: HD bus -> register latch; read: register -> HD bus)
```

### Key Differences Between Models

| Feature | AP-120B (GE AP-CT) | FPS-100 (4448) |
|---|---|---|
| Register selection | Direct strobes on backplane | REGSEL bus to 4448 |
| WC/APMA access | Unknown (no HWCCLK/HADRCLK) | Dedicated clocks |
| Direction control | HD2REG / REG2HD | APDIR\* (probably) |
| CTRL access | Atomic bit signals (CTL10, CLT08\*) | HCTCLK\* (full register) |
| Format registers | BH2HD / BL2HD\* | Unknown |

### What Remains Unknown

1. Whether the 280B generates REGSEL combinationally (single-cycle, direct
   decode) or latches it from a previous I/O instruction (two-step)
2. The exact DOx+flag -> register mapping for either model
3. How the AP-120B accesses WC and APMA without dedicated clock signals
4. Whether CTL10/CLT08\* mean the host sets individual CTRL bits via
   different I/O instructions (rather than writing the full register)

## Proposed Register Mapping (Speculative)

**IMPORTANT: This mapping is speculative and must be verified by hardware
probing. The AP-120B and FPS-100 may have different mappings due to their
different interface architectures.**

With 3 DOx channels x 4 flag options = 12 write slots and 3 DIx x 4 flag
options = 12 read slots, there are 24 total instruction variants -- more than
enough for 10 registers.

**Mapping principles (if direct decode):**
- DOA/DIA (buffer A) handles the most frequent operations (SWR write, FN read)
- S flag = "Start/Go" -- used for CTRL (launch DMA/function) and DMA setup
- C flag = "Clear/Initialize" -- used for reset-related operations
- P flag = "Pulse" -- device-specific, used for less common operations
- DOB/DOC handle secondary registers (DMA setup, format)
- Individual CTRL bits (CTL10, CLT08\*) may be set/cleared by specific
  DOx+flag combinations rather than writing the full 16-bit CTRL register

**Mapping principles (if two-step with REGSEL):**
- One DOx instruction (likely DOA) writes the REGSEL address
- Another DOx (likely DOB or DOC) transfers data to/from the selected register
- Frequently-used registers (SWR, FN) may still have direct-access shortcuts

### Best-estimate mapping assuming direct decode (needs hardware verification)

**Writes (host -> AP):**

| DG Instruction | FPS Register | Strobe | Rationale |
|---|---|---|---|
| `DOA ac,055` (no flag) | SWR | LDSR\* | Most frequent write. Every APEX message word goes through SWR. |
| `DOAS ac,055` | CTRL | HCTCLK\* | S=Start. Write CTRL with HDMAGO to launch DMA. |
| `DOAC ac,055` | ABRT | -- | C=Clear. Reset the AP. |
| `DOAP ac,055` | FN | LDFN\* | P=Pulse. Load function register (used by supervisor). |
| `DOB ac,055` (no flag) | WC | HWCCLK\* | DMA word count -- part of DMA setup sequence. |
| `DOBS ac,055` | HMA | HMACLK\* | S=Start. Host memory address for DMA. |
| `DOBC ac,055` | APMA | HADRCLK\* | C flag. AP memory address for DMA. |
| `DOBP ac,055` | FMTH | -- | P flag. Format high (rare). |
| `DOC ac,055` (no flag) | FMTL | -- | Format low (rare). |
| `DOCS ac,055` | -- | HDMACLK\* | S=Start. May directly trigger DMA start. |

**Reads (AP -> host):**

| DG Instruction | FPS Register | Strobe | Rationale |
|---|---|---|---|
| `DIA ac,055` (no flag) | FN | FN2HD\* | Most frequent read. Status polling (halt, SWR ack). |
| `DIAS ac,055` | CTRL | -- | S flag. Read control/interrupt status. |
| `DIAC ac,055` | SWR | SR2HD\* | C flag. Read back SWR value. |
| `DIAP ac,055` | LITES | LT2HD\* | P flag. Read lights/diagnostic register. |
| `DIB ac,055` (no flag) | WC | -- | Read word count (after DMA). |
| `DIBC ac,055` | APMA | HADR2HD\* | C flag. Read AP memory address. |
| `DIC ac,055` (no flag) | HMA | -- | Read host memory address. |

**Flag-only operations:**

| DG Instruction | Effect |
|---|---|
| `NIOS 055` | Set RUN BUSY (start AP execution) |
| `NIOC 055` | Clear all flags, reset device |
| `NIOP 055` | Pulse (AP interrupt -- equivalent to APIRT) |
| `SKPBN 055` | Skip if RUN BUSY set (AP running) |
| `SKPBZ 055` | Skip if RUN BUSY clear (AP stopped) |
| `SKPDN 055` | Skip if RUN DONE set (AP halted/completed) |
| `SKPDZ 055` | Skip if RUN DONE clear |

### DMA setup sequence (probable)

```
; Set up DMA transfer from host memory to AP main data
    LDA 0, WORD_COUNT
    DOB 0, FPS          ; Write WC (word count)
    LDA 0, HOST_ADDR
    DOBS 0, FPS         ; Write HMA (host memory address)
    LDA 0, AP_ADDR
    DOBC 0, FPS         ; Write APMA (AP memory address)
    LDA 0, CTRL_VAL     ; HDMAGO bit set
    DOAS 0, FPS         ; Write CTRL + Start -> launches DMA
```

### APEX message sequence (probable)

The host sends a 5-word APEX message to the AP via the SWR/FN handshake:

```
; Send DATUM (word 0 of APEX message)
    LDA 0, DATUM
    DOA 0, FPS          ; Write to SWR
    NIOP FPS             ; Pulse -> interrupt the AP (APIRT)
wait1:
    DIA 1, FPS           ; Read FN
    MOVZL 1,1,SZC        ; Test bit 14 (SWR read ack) -- DG bit 1
    JMP wait1            ; Loop until AP acknowledges

; Send remaining 4 words (FPOPT, FPSCT, FPSWR, FPFNR)
    LDA 0, FPOPT
    DOA 0, FPS          ; Write to SWR
; ... (wait for ack, repeat for each word)
```

**NOTE:** This mapping is a best estimate. The exact assignment of registers
to DOx+flag combinations must be verified by hardware probing. See
"Verification" section below.

## Verification

### Method 1: Logic analyzer on FPS backplane

Probe the named strobe signals (LDSR\*, LDFN\*, HWCCLK\*, HMACLK\*, HADRCLK\*,
HDMACLK\*, HCTCLK\*) on the FPS backplane while issuing each DOA/DOB/DOC
instruction with each flag variant. This directly reveals the decode truth table.

### Method 2: Software probe after reset

After power-on or `NIOC 055`, the AP should be halted. The FN register bit 15
(DG bit 0, MSB) should be set. Try all DIx variants to find which reads FN:

```
    NIOC FPS             ; Reset device
    DIA 0, FPS           ; Try buffer A -- check if bit 0 (MSB) set
    DIB 1, FPS           ; Try buffer B
    DIC 2, FPS           ; Try buffer C
    HALT                 ; Examine AC0, AC1, AC2
```

### Method 3: SWR/FN handshake test

If the AP is running ECHO.B, write a known value and watch for acknowledgment:

```
    LDA 0, TEST_VAL
    DOA 0, FPS           ; Try writing to SWR via buffer A
    DIA 1, FPS           ; Read FN -- if bit 14 set, DOA writes SWR
```

## DG Nova I/O Instruction Encoding

The DG Nova uses big-endian bit numbering (bit 0 = MSB).

```
   0 1 1  AC   Transfer  Ctrl  Device Code
   -----  ---  --------  ----  -----------
   Bit 0-2: 011       (I/O instruction class)
   Bit 3-4: AC        (accumulator: 0-3)
   Bit 5-7: Transfer  (transfer type)
   Bit 8-9: Control   (flag control)
   Bit 10-15: Device  (device code, 0-77 octal)
```

Transfer types (bits 5-7):
```
000 = NIO  (No I/O transfer, flag control only)
001 = DIA  (Data In from buffer A -- read into AC)
010 = DOA  (Data Out to buffer A -- write from AC)
011 = DIB  (Data In from buffer B)
100 = DOB  (Data Out to buffer B)
101 = DIC  (Data In from buffer C)
110 = DOC  (Data Out to buffer C)
111 = SKP  (skip on device condition)
```

Flag control (bits 8-9):
```
00 = (none)
01 = S  (Start -- sets BUSY, clears DONE)
10 = C  (Clear -- clears both BUSY and DONE)
11 = P  (Pulse -- device-specific)
```

FPS-100 device code: **055** (octal) = 45 decimal = 101101 binary

Example instruction encodings:
```
DOA  0,055  =  060455 (octal)           ; Write AC0 to FPS buffer A
DOAS 0,055  =  060555 (octal)           ; DOA + Start flag
DOB  0,055  =  064055 (octal)           ; Write AC0 to FPS buffer B
DIA  0,055  =  060455 (octal)           ; Read FPS buffer A into AC0
NIOC 055    =  060255 (octal)           ; Clear FPS flags (reset)
NIOS 055    =  060155 (octal)           ; Start FPS (set BUSY)
SKPBN 055   =  063455 (octal)           ; Skip if BUSY set
SKPDN 055   =  063655 (octal)           ; Skip if DONE set
```

## GE AP-CT Nova Eclipse Wire List (Key Find)

A complete 82-page backplane wire list for a GE AP-CT AP-120B Nova Eclipse
system was found on archive.org (bitsavers collection):

`520-0000-072 525-0098-001 31 Card Chassis Wire List AP120-B NOVA E 198204`

Saved locally: `AP-120B_Nova_E_31Card_Wirelist_198204.pdf`

This wire list confirms all signal names between the Nova I/O adapter (board
position B219 = GPIFJ1) and the AP backplane:

| Wire | Signal | Description |
|---|---|---|
| 11 | HMACLK\* | Host Memory Address Clock (write HMA) |
| 13 | HCTLCLK\* | Host Control Clock (write CTRL) |
| 15 | HDMACLK\* | Host DMA Clock |
| 23 | HD2REG | Host Data TO Register (write direction strobe) |
| 27 | REG2HD | Register TO Host Data (read direction strobe) |
| 43 | SETREQ\* | Set Request (interrupt) |
| 45 | CLINT\* | Clear Interrupt |
| 47 | CTL10 | Control bit 10 |
| 49 | CLT08\* | Control bit 08 |
| 51 | CTL5INTR\* | Control 5 Interrupt |
| 67 | AD2BUS\* | Address to Bus |
| 75 | SYRT\* | System Reset |
| 79 | WC=0\* | Word Count = Zero (DMA complete) |
| 81 | LT2HD | Lights register to Host Data (read LITES) |
| 83 | FN2HD | Function register to Host Data (read FN) |
| 85 | SR2HD | Switch register to Host Data (read SWR) |
| 91 | LDSR\* | Load Switch Register (write SWR) |
| 93 | LDFN\* | Load Function Register (write FN) |

**Key observation:** HD2REG and REG2HD are the master write/read direction
strobes. These correspond to APDIR\* on the 280B -- HD2REG is active during
DOx cycles (host writes), REG2HD is active during DIx cycles (host reads).

## Archival Leads

The **Charles Babbage Institute (CBI)** at the University of Minnesota
(https://cse.umn.edu/cbi/archives-special-collections) collects computing
history records. It is unconfirmed whether they hold FPS-specific materials,
but an inquiry to cbi@umn.edu is worth trying.

Other potential sources:
- **archive.org / bitsavers** -- has FPS-100 and AP-120B docs including
  the GE AP-CT Nova E wire list found above
- **Computer History Museum** -- has FPS-164 spec, may have more
- **John Gustafson** -- former FPS employee, author of "Programming the
  FPS T Series" (http://www.johngustafson.net/pubs/pubt1986.2/FPS.pdf)
- GE CT scanner archives (the GE CT9800 used Nova 4/X + AP-120B)
- Lawrence Livermore, Los Alamos, Naval Research Lab technical reports
- University of Washington (near FPS headquarters in Beaverton, OR)
- MIT Lincoln Laboratory, Stanford/SLAC, UIUC (all heavy Nova+AP users)
- classiccmp.org mailing list, forum.vcfed.org, system-cfg.com forums

## Tools

- `dgasm/` -- DG Nova assembler (modified fork of
  https://github.com/CWood1/dgasm). See `dgasm/CHANGES.md` for modifications.
- https://github.com/Quantx/dgnsdk -- DG Nova SDK (dgnasm assembler, compiler,
  debugger). Used as reference implementation to verify dgasm instruction
  encodings. Not included in this repository.

## Files In This Repository

- `860-7259-003_procHbkFeb79_ocr.pdf` -- AP-120B Processor Handbook (OCR'd,
  searchable). Contains FN command encoding, CTL bit layout, loading procedure.
- `4448_APIF_netlist.txt` -- FPS-100 AP Interface (Nova version) netlist
- `4421_PDPIF_netlist.txt` -- FPS-100 PDP-11 Interface netlist (comparison)
- `4429_FMT_netlist.txt` -- Formatter board netlist (shared)
- `AP-120B_Nova_E_31Card_Wirelist_198204.pdf` -- GE AP-CT Nova E wire list
- `DAPEX.MAC` -- PDP-11 RSX-11M host-dependent driver (to be rewritten)
- `DRIVER.MAC` -- PDP-11 RSX-11M device driver
- `FDAPEX.FTN` -- FORTRAN driver layer (mostly portable)
- `ADUTIL.MAC` -- PDP-11 host utility functions (bit manipulation)
- `fps_probe.asm` -- DG Nova test program to discover register mapping
- `dgasm/` -- Modified DG Nova assembler

## External Sources

- 280B Nova Eclipse I/O Adapter schematics (512-3280-00A, 5 pages TIF)
  from Myron White via Nakazoto/FloatingPointSystems github
- 4448 AP I/F schematics (APIF.pdf, 18 pages, poor quality)
  from Nakazoto/FloatingPointSystems github, GE Schematics directory
- FPS-100 Nova I/F schematics (419-0, 10 pages TIF)
- FPS-100 Formatter Nova schematics (429-0, 9 pages TIF)
