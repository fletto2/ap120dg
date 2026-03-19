# 280B Nova Eclipse I/O Adapter — Schematic Trace Notes

Drawing: 512-3280-004, Rev B, 5 sheets
Title: SCHEMATIC, ECB, 280B, NOVA ECLIPSE I/O ADAPTER
Engineer: Ed Miller, 8-28-78
Checked: O. Gonzalowski, 5/22/78
Prod. Release: R. Adam 5/31
Approved: 10/3/79, Frank Wittse 3-17-80

### Revision History
| Rev | Auth | Description |
|-----|------|-------------|
| 01 | — | Level 2 Release |
| A | ECO 79540 | Redrawn mylar and Level 3 release |
| B | ECO 80051 | Change power down detector |

## Sheet 1 of 5 — Main I/O Decode Logic

### Bus Input Signals (top edge, active-low from DG backplane)

| Signal | Connector | Description |
|--------|-----------|-------------|
| DS5\*, DS4\*, DS3\* | A64, A62, A46 | Device select high bits |
| DS2\*, DS1\*, DS0\* | A66, A68, A72 | Device select low bits |
| DHMACLKQ | A58 | DMA clock qualified |
| DATOA | A56 | Data Out A strobe |
| DATOB | A48 | Data Out B strobe |
| DATOC | (nearby) | Data Out C strobe |
| DATTA | A44 | Data In A strobe (DIA) |
| DATTB | A42 | Data In B strobe (DIB) |
| DATTC | A54 | Data In C strobe (DIC) |

### Device Select Decode (top-left)

Two **7442** BCD-to-decimal decoders (C9, C10) decode DS0\*-DS5\* through
**7414** Schmitt trigger inverters (D10, D12, D13). The 7442 outputs are active-low
decoded lines E00-E20 that go to the backplane edge connector.

A **7440** dual 4-input NAND (C8) combines four signals AP0\*, AP1\*, AP2\*, AP3\*
into the device-selected signal. These AP bits come from the 7442 outputs
and represent the unit select — i.e., which FPS device (device code 055).

### DOA/DOB/DOC Qualify Gates (middle)

Three **7410** triple 3-input NAND gates (C6, C1) combine:
- The DATOx/DATIx strobe
- The device-select signal
- Additional timing/flag signals

Each section of C6 and C1 produces a qualified strobe for one specific
DOx or DIx instruction variant. The 7410 at C6 has three gates, the
7410 at C1 has three gates — 6 qualified strobes from these two chips.

Additional 7410 gates (at least 2 more instances visible) provide
more qualified combinations.

### Flag Flip-Flops (middle-right)

Two **74S74** dual D flip-flops:
- **C7** (74S74): captures DOA flag state
- **C5** (74S74): captures additional flag/timing state

These latch the Start/Clear/Pulse flag from the I/O instruction and
hold it stable while the register strobe propagates.

### Register Strobe Generation (bottom)

The bottom of the sheet shows the final output stage. **74S02** NOR gates
(D6, D8, D5) and **74S00** NAND gates (D4, D5, D7, D1, D2, D3, D4) combine
the qualified DOx/DIx signals with flag states to generate individual
register clock/strobe signals.

#### Output Strobes (active-low, bottom edge, left to right):

| Signal | Connector | Description |
|--------|-----------|-------------|
| HWCCLK\* | A77 | Host Word Count Clock (write WC) |
| LDSR\* | A86 | Load Switch Register (write SWR) |
| HADRCLK\* | A84 | Host Address Register Clock (write APMA) |
| HDMACLK\* | A85 | Host DMA Clock |
| HMACLK\* | A75 | Host Memory Address Clock (write HMA) |
| LDFN\* | A76 | Load Function Register (write FN) |
| B0CLK\* | A78 | Board 0 Clock (purpose TBD) |
| HCTLCLK\* | A71 | Host Control Clock (write CTRL) |
| INTCLK\* | (A71 area) | Interrupt Clock |
| B2CLK\* | A73 | Board 2 Clock (purpose TBD) |

#### Read-back / Direction Strobes (bottom-right):

| Signal | Connector | Description |
|--------|-----------|-------------|
| BUS2HD | A47 | Bus to Host Data |
| SR2HD | A47 | Switch Register to Host Data (read SWR) |
| HD2REG | A83 | Host Data to Register (write direction) |
| FN2HD | A49 | Function Register to Host Data (read FN) |
| LT2HD | A57 | Lights to Host Data (read LITES) |
| BH2HD\* | A59 | Buffer High to Host Data (read FMTH?) |
| BL2HD\* | A61 | Buffer Low to Host Data (read FMTL?) |
| HOSTRS0 | A63 | Host Register Select bit 0 |
| HOSTRS1 | A65 | Host Register Select bit 1 |
| HADR2HD\* | A69 | Host Address to Host Data (read APMA) |
| REG2HD | A67 | Register to Host Data (read direction) |
| HD2BUS\* | (far right) | Host Data to Bus (write direction) |

### Observation: HOSTRS0/HOSTRS1

These two register select bits (2 bits = 4 values) appear alongside
the read-back strobes. This suggests a **4-way read multiplexer** on
the host data bus, controlled by HOSTRS0/HOSTRS1:

| HOSTRS1 | HOSTRS0 | Source (probable) |
|---------|---------|-------------------|
| 0 | 0 | FN (via FN2HD) |
| 0 | 1 | SWR (via SR2HD) |
| 1 | 0 | LITES (via LT2HD) |
| 1 | 1 | HADR/APMA (via HADR2HD\*) |

The individual \*2HD strobes may be the actual enable gates that
HOSTRS decodes into. Or HOSTRS may be generated from DOx/DIx decode
and routed to the 4448/backplane, where the 4448 uses it.

## Sheet 2 of 5 — Interrupt, DMA Request, Power Monitor

### Bus Input Signals (top edge):

| Signal | Connector | Description |
|--------|-----------|-------------|
| INTCLK\* | A70 | Interrupt clock |
| IORST | (bus) | I/O Reset (DG master clear) |
| RQENB\* | B41 | Request Enable (DG interrupt priority) |
| APINTR | (internal) | AP Interrupt Request |
| CLINTR\* | (internal) | Clear Interrupt |
| MSKO\* | A38 | Mask Out (DG interrupt mask) |
| DATA01\*-DATA07\* | (bus) | Data bus bits 1-7 (active-low, from DG) |
| INTA | A96 | Interrupt Acknowledge (from DG priority chain) |
| INTPIN\* | A40 | Interrupt Pin (active-low) |
| AP0, IOPLS | A74 | AP0 address bit, I/O Pulse |
| DCHPIN\* | A94 | DCH (Data Channel = DMA) Pin |

### Top-right signals:

| Signal | Connector | Description |
|--------|-----------|-------------|
| HREQ\* | A89 | Host Request (DMA request to DG) |
| DCHA\* | A92, A60 | DMA Channel Acknowledge |
| WC=0\* | A90 | Word Count Zero (DMA complete) |
| SETREQ\*/DMABUSY | A88 | Set DMA Request / DMA Busy |
| DCHO | B33 | DCH Out |
| DCHI | B37 | DCH In |

### Interrupt Priority Chain

**C11** (74S74, two sections) form the interrupt enable and pending
flip-flops. Cleared by IORST\*. Section 1 (pins 2-6): interrupt
pending. Section 2 (pins 10-12): interrupt enable.

**B9** (7410) triple 3-input NAND gates the interrupt acknowledge
with the priority chain.

**A10** (74S74) captures the request enable (RQENB) state. This
feeds into the priority daisy-chain. Cleared by SYRT\*A.

**C8** (7440) dual 4-input NAND combines priority signals.
**B8** (7438) open-collector NAND drives SELB\*/SELD\* for
skip-on-busy/done tests.

### Interrupt Signal Conditioning

- **B11** (7400) NAND gates combine interrupt conditions
- **B16** (74132) Schmitt trigger NAND — debounces/conditions signals
- **B16R1** (1K), **B16CR1** (1N914), **B16C1** (100pF) — RC filter
  on interrupt input
- **B11R1** (1K), **B11C1** (100pF) — RC filter on INTCLK\*
- **A11R1** (1K, +5V) — pull-up on MSKO\* data lines

### Interrupt Mask Decode

DATA01\*-DATA07\* (7 active-low data bus lines) enter through
jumper positions E21-E29. These connect to the interrupt mask
register decode. The jumper at E29 selects which data bit
corresponds to this device's mask bit.

### DMA Channel Logic

**C7** (74S74) DMA control flip-flop, conditioned by:
- **B6** (7414) Schmitt trigger on WC=0\* and SETREQ\*/DMABUSY
- **D8** (74S00) NAND gate combining DMA signals
- **B12R1** (1K), **B12CR1** (1N914), **B12C1** (SEL) — selector/filter

**B15** (74S74) DMA handshake flip-flop:
- Section 1 (pins 2-6): controls DCHO/DCHI timing
- Section 2 (pins 10-12): DMA direction/state

**B14** (7400) NAND gates (3 sections used) qualify DMA signals.

**A15** (74S74) additional DMA state flip-flops.
**A13** (74S74) two more DMA/interrupt state flip-flops.

DMA signals:
- **DCHO** (B33) and **DCHI** (B37) are the DCH Out/In signals
  that tell the DG Nova the FPS wants a DMA word transfer
- **DCHA\*** (A92, A60) is DMA channel acknowledge from the Nova
- **WC=0\*** (A90) signals DMA transfer complete
- **SETREQ\*/DMABUSY** (A88) controls the DMA request flip-flop
- **D8R1** (1K, +5V) — pull-up on DMA control

### Device Code Jumper Area (bottom-left)

"JUMPER FOR DEVICE CODE AP0" label at bottom.

7417 open-collector buffers (C13, C16) drive the following signals
to the backplane edge connector:

| Signal | Connector | Description |
|--------|-----------|-------------|
| INTPOUT\* | A95 | Interrupt priority out |
| INTR\* | B29 | Interrupt request (active-low) |
| SYRT\*A | (internal) | System Reset A |
| DATA10\*-DATA15\* | (bus) | Data bus bits 10-15 (active-low) |
| SYRT\* | A91 | System Reset |
| AD2BUS | (internal) | Address to Bus |

An **LM311** comparator (C15) with 3.3V zener (C15CR1) and
resistor divider (B9R1=200, B9R2=240) monitors a voltage level —
likely power-fail detection.

### Bottom-right signals:

| Signal | Connector | Description |
|--------|-----------|-------------|
| AD2BUS\* | B06 | Address to Bus |
| DCHM0\* | B17 | DCH Memory cycle 0 |
| DCHPOUT\* | A93 | DCH Priority Out |
| DCHR\* | B35 | DCH Request |
| REQ\* | B11 | Request |
| DHC2BUS\* | (nearby) | DCH to Bus |
| DMACLKC | (internal) | DMA Clock C |
| DBUS2HD | (nearby) | DMA Bus to Host Data |
| DCHIN | B13 | DCH In |
| DCHOUT\* | B15 | DCH Out |

## Sheet 3 of 5 — 16-Bit Data Bus Transceivers

This sheet contains the bidirectional data bus interface between
the DG Nova data bus and the FPS host data bus.

### DG Data Bus Signals (top edge, active-low)

| Signal | Connector | Signal | Connector |
|--------|-----------|--------|-----------|
| DATA00\* | B62 | DATA08\* | B60 |
| DATA01\* | B65 | DATA09\* | B63 |
| DATA02\* | B82 | DATA10\* | B75 |
| DATA03\* | B73 | DATA11\* | B58 |
| DATA04\* | B61 | DATA12\* | B59 |
| DATA05\* | B57 | DATA13\* | B64 |
| DATA06\* | B95 | DATA14\* | B56 |
| DATA07\* | B55 | DATA15\* | B66 |

### FPS Host Data Bus Outputs (bottom edge, active-high)

| Signal | Connector | Signal | Connector |
|--------|-----------|--------|-----------|
| HD00 | B19 | HD08 | B40 |
| HD01 | B23 | HD09 | B49 |
| HD02 | B25 | HD10 | B52 |
| HD03 | B27 | HD11-HD15 | (continue on BR tile) |
| HD04 | B31 | | |
| HD05 | B34 | | |
| HD06 | B36 | | |
| HD07 | B38 | | |

### Architecture

The transceivers use **8640** bidirectional bus transceivers paired
with **74S38** open-collector NAND buffers, arranged in four groups:

**PIO Data Path (top half):**
- **D13** (8640) + **D14** (74S38) — bits 0-7
- **D15** (8640) + **D16** (74S38) — bits 8-15

**DMA Data Path (bottom half):**
- **D11** (8640) + **D12** (74S38) — bits 0-7
- **D17** (8640) + **D18** (74S38) — bits 8-15

### Direction Control

- **A16** (74S02) NOR gates combine direction signals:
  - BUS2HD\* / HD2BUS\* — PIO direction
  - DBUS2HD\* / DHD2BUS\* — DMA direction
  - AD2BUS — address to bus
- **B10** (74S08) AND gates and **B17** (74S37) buffers provide
  additional direction qualification

### Read-back Buffers

Three **74365** hex tri-state buffers provide the read path:
- **C14** (74365) — PIO read-back, 6 bits
- **C12** (74365) — PIO read-back, additional bits
- **C17** (74365) — DMA read-back, 6 bits

Each 74365 has two active-low enable pins (G1, G2) and 6
non-inverting tri-state outputs. These gate the FPS register
data onto the DG data bus during DI instructions.

### Pull-up Resistor Packs

- **C13R1** (1K, +5V) — pull-ups for DMA bus lines
- **C15R1** (1K, +5V) — pull-ups for PIO bus lines
- **C18R1** (1K, +5V) — pull-ups for DMA high byte

## Sheet 4 of 5 — Flag Flip-Flops and CTRL Decode

### Bus Input Signals (top edge):

| Signal | Connector | Description |
|--------|-----------|-------------|
| CLR | A50 | Clear flag (from I/O instruction) |
| STRT | A52 | Start flag (from I/O instruction) |
| US | (bus) | User-mode flag |
| SYRT\*A | (internal) | System Reset |
| AP2\*, AP1\*, AP0\* | (bus) | AP subdevice address bits |
| CTLSINTR\* | A81 | CTRL/S Interrupt |
| REQ\* | A81 area | Request |
| RUN | A79 | AP Run signal (from FPS backplane) |

### I/O Instruction Decode

**C3** (74S10) triple 3-input NAND gates decode combinations of
CLR (A50), STRT (A52), US, and device-selected signals:
- Section 1 (pins 9,10,11→8): qualified clear signal
- Section 2 (pins 1,2,13→12): qualified start signal
- Signal conditioning: C3R1 (1K) + C3C1 (100pF) on CLR,
  C4R1 (1K) + C4C1 (100pF) on STRT

**B5** (74S11) triple 3-input AND gate further qualifies with
subdevice address bits.

**B4** (7402) quad NOR gates and **B3** (7402) generate the
per-subdevice flag control signals. **A5** (7402) provides
additional NOR combinations:

| Signal | Generated by | Description |
|--------|-------------|-------------|
| NIOCAP0 | A3 (7404) pin 13→12 inversion | NIO-Clear for subdevice 0 |
| NIOSAP0 | A3 (7404) pin 13→12 + A4 (7427) | NIO-Start for subdevice 0 |
| NIOCAP1 | A5 (7402) pin 5,6→4 | NIO-Clear for subdevice 1 |
| NIOSAP1 | A3 (7404) pin 11→10 inversion | NIO-Start for subdevice 1 |
| NICSAP2 | A3 (7404) pin 9→8 inversion | NIO-Clear/Start for subdevice 2 |
| NIOCAP2 | A5 (7402) pin 8,9→10 | NIO-Clear for subdevice 2 |

**A3** (7404) inverters (3 sections used, 1 spare).
**A4** (7427) triple 3-input NOR gates:
- Section 1 (pins 1,2,13→12): NIOSAP0 generation
- Section 2 (pins 3,4,5→6): NIOSAP1 generation
- Section 3 (pins 9,10,11→8): NICSAP2 generation

### Three Sets of DONE/BUSY Flip-Flops

This is a critical finding. The 280B has **three independent pairs** of
DONE/BUSY flip-flops, each a **7474** dual D flip-flop:

#### RUN DONE / RUN BUSY (A6, 7474)

- **RUN DONE** (pin 5, Q output): Set when the AP halts (RUN goes low)
  - Pin 2 (D): RUN\* signal (conditioned)
  - Pin 3 (CLK): from NIOSAP0
  - Pin 4 (PRE): tied high via A6R1 (1K, +5V pull-up)
  - Pin 1 (CLR): NIOCAP0
- **RUN BUSY** (pin 9, Q output): Set when Start issued
  - Pin 12 (D): tied to conditions
  - Pin 11 (CLK): from NIOSAP0
  - Pin 10 (PRE): tied high
  - Pin 13 (CLR): NIOCAP0
- **A9** (7400) pin 2,3→1: combines RUN DONE with subdevice select
- RUN signal (A79) conditioned through **B6** (7414) Schmitt trigger:
  - Pin 11→10: inverted RUN
  - Pin 13→12: double-inverted (restored polarity)
  - **B7R1** (120Ω), **B7R2** (120Ω): damping resistors on RUN signal

#### DMA DONE / DMA BUSY (A7, 7474)

- **DMA DONE** (pin 5, Q output): Set when DMA completes (WC=0)
  - Pin 2 (D), Pin 3 (CLK): from DMA complete logic
  - Pin 4 (PRE): from NIOSAP1
  - Pin 1 (CLR): NIOCAP1 + SYRT
- **DMA BUSY** (pin 9, Q output): Set when DMA started
  - Pin 12 (D), Pin 11 (CLK): from DMA start logic
  - Pin 10 (PRE): tied high
  - Pin 13 (CLR): NIOCAP1 + SYRT
- **A9** (7400) pin 5,4→6: combines DMA DONE with subdevice select

#### CTL05 DONE / CTL05 BUSY (A8, 7474)

- **CTL05 DONE** (pin 5, Q output): Set by CTL bit 5 interrupt condition
  - Pin 2 (D), Pin 3 (CLK): from CTL5INTR\* (A81) logic
  - Pin 1 (CLR): NIOCAP2 + SYRT
- **CTL05 BUSY** (pin 9, Q output): Set when waiting for CTL05 event
  - Pin 12 (D), Pin 11 (CLK): from NICSAP2
  - Pin 13 (CLR): NIOCAP2 + SYRT
- **A9** (7400) pin 9,8→10: combines CTL05 DONE with subdevice select
- **D9** (7404) pin 9→8: inverts CLINT\* signal → CLINTR\* (A87)

### Subdevice Address Decode for Flags

The flag operations are decoded per-subdevice using AP0, AP1, AP2.
**7438** open-collector NAND gates (B7, B8) combine the subdevice
address with the DONE/BUSY flip-flop outputs, generating:

| Signal | Connector | Description |
|--------|-----------|-------------|
| SELB\* | A82 | Select Busy (for skip-on-busy test) |
| SELD\* | A80 | Select Done (for skip-on-done test) |
| DMABUSY | (internal) | DMA Busy status |

A **7410** (B9) gates AP2/AP1/AP0 with the CTL05 flip-flop output.

### Additional Signals (bottom):

| Signal | Connector | Description |
|--------|-----------|-------------|
| CLINT\* | A87 | Clear Interrupt |
| APINTR | (to sheet 2) | AP Interrupt to host |

### Implication: Three Subdevices

The presence of **three independent DONE/BUSY pairs** mapped to
three different subdevice addresses (AP0/AP1/AP2 decode) means the
FPS appears to the DG as **effectively three logical subdevices**:

| Subdevice | AP2:AP1:AP0 | Function |
|-----------|-------------|----------|
| 0 | 0:0:0 | RUN control (AP start/stop/halt status) |
| 1 | 0:0:1 | DMA control (transfer start/complete status) |
| 2 | 0:1:0 | CTL05 / programmed interrupt |

This is a standard DG pattern — the DG I/O system supports
multiple subdevice addresses per device code. The SKPBN/SKPBZ/SKPDN/SKPDZ
instructions can test each subdevice's DONE/BUSY independently.

However, DOA/DOB/DOC data transfer instructions may or may not
be affected by the subdevice address. The flag (S/C/P) is the
primary selector for which register gets written/read.

## Sheet 5 of 5 — Spare Logic and Bypass Caps

### Power Bus Connections

Two power rails with redundant connections:

| Rail | Connector Pins |
|------|---------------|
| +5V (or VCC) | A03, A04, A97, A98, B03, B04, B97, B98 |
| GND | A01, A02, A99, A100, B01, B02, B99, B100 |

### Bypass Capacitors

Every IC position has a bypass capacitor to ground. Labeled by
IC position (e.g., A4C1, A7C1, A10C1, B3C1, B6C1, etc.).

Two bulk filter caps: **E1C1** (6.8µF, 35V) and **E9C1** (6.8µF, 35V).

"1. UNLESS OTHERWISE SPECIFIED ALL CAPACITORS ARE 0.01, 50 VOLTS."

### Spare Logic Grid (unused gate sections)

| Chip | Type | Spare Pins | Chip | Type | Spare Pins |
|------|------|-----------|------|------|-----------|
| A9 | 7400 | 12,13→11 | C12 | 74365 | 2→3, 14→13 |
| B3 | 7402 | 5,6→4; 2,3→1 | B17 | 74S37 | 1,2→3; 9,10→8; 12,13→11 |
| C2 | 7404 | 11→10; 9→8 | B16 | 74132 | 1,2→3; 12,13→11 |
| B11 | 7400 | 1,2→3; 12,13→11 | D1 | 74S00 | 1,2→3 |
| A16 | 74S02 | 8,9→10; 11,12→13 | A3 | 7404 | 1→2; 3→4 |
| B12 | 74S04 | 3→4 | B13 | 74S04 | 1→2; 3→4; 13→12 |
| A5 | 7402 | 11,12→13 | C13 | 7417 | 9→8 |
| B2 | 7474 | section 1 (pins 2-6) | | | |

## Key Findings Summary

1. **The 280B is a direct-decode architecture.** Each DOx+flag combination
   produces a unique register strobe through combinational logic (7410 NANDs
   -> 74S02 NORs -> named strobe). There is no microprocessor, no sequencer,
   no latched REGSEL address on this board.

2. **Three independent DONE/BUSY flag pairs** exist for RUN, DMA, and CTL05.
   These are addressed by AP0/AP1/AP2 subdevice bits in the I/O instruction.

3. **HOSTRS0/HOSTRS1** provide a 2-bit register select for the read-back path,
   separate from the write strobes. This selects which register drives the
   host data bus during a DI instruction.

4. **The write strobes are individually decoded:** LDSR\*, LDFN\*, HWCCLK\*,
   HMACLK\*, HADRCLK\*, HDMACLK\*, HCTLCLK\*, INTCLK\*, B0CLK\*, B2CLK\*.
   Each one fires for exactly one DOx+flag combination.

5. **The read-back strobes are individually decoded:** FN2HD, SR2HD, LT2HD,
   BH2HD\*, BL2HD\*, HADR2HD\*, REG2HD. These determine which register's
   output drives the host data bus.

6. **Direction control** is via HD2REG (write: Nova->FPS), REG2HD (read:
   FPS->Nova), and HD2BUS\*/BUS2HD for the bus interface.

7. **DMA uses the standard DG DCH (Data Channel) protocol** — DCHO/DCHI
   handshake, DCHA\* acknowledge, separate from PIO register access.

## Inferred Register Mapping

By counting write strobes (10) against available DOx+flag combinations
(3 channels × 4 flags = 12), and grouping by strobe name semantics,
the mapping can be inferred as a **4 + 4 + 2** split across DOA/DOB/DOC.

### Write Mapping (DOA/DOB/DOC → Register Strobes)

**DOA — Command/Control Registers (4 flag variants used):**

| Flag | CLR | STRT | Strobe | Register | DG Instruction |
|------|-----|------|--------|----------|----------------|
| none | 0 | 0 | LDSR\* | SWR | `DOA ac,FPS` |
| S | 0 | 1 | LDFN\* | FN | `DOAS ac,FPS` |
| C | 1 | 0 | HCTLCLK\* | CTRL | `DOAC ac,FPS` |
| P | 1 | 1 | INTCLK\* | INT/APIRT | `DOAP ac,FPS` |

DOA handles the entire command/control interface: data via SWR (none),
commands via FN (Start), configuration via CTRL (Clear), AP interrupt
via INTCLK (Pulse). LITES has no write strobe — it is read-only.

Rationale: none=SWR is the most frequent write (every APEX word).
S=FN allows fast SWR/FN handshake by alternating `DOA` and `DOAS`.
P=INT is a one-shot action (Pulse semantics). C=CTRL for configuration.

**DOB — DMA Registers (4 flag variants used):**

| Flag | CLR | STRT | Strobe | Register | DG Instruction |
|------|-----|------|--------|----------|----------------|
| none | 0 | 0 | HWCCLK\* | WC | `DOB ac,FPS` |
| S | 0 | 1 | HMACLK\* | HMA | `DOBS ac,FPS` |
| C | 1 | 0 | HADRCLK\* | APMA | `DOBC ac,FPS` |
| P | 1 | 1 | HDMACLK\* | DMA start | `DOBP ac,FPS` |

DMA setup sequence: write WC (none), write HMA (Start), write APMA
(Clear), then Pulse to start the DMA transfer via HDMACLK\*.

**DOC — Formatter Registers (2 flag variants used, 2 unused):**

| Flag | Strobe | Register | Rationale |
|------|--------|----------|-----------|
| none | 0 | 0 | B0CLK\* | FMTH | `DOC ac,FPS` |
| S | 0 | 1 | B2CLK\* | FMTL | `DOCS ac,FPS` |
| C | 1 | 0 | — | (unused) | |
| P | 1 | 1 | — | (unused) | |

The decode gates require CLR=0, so only none and S produce strobes.
B0CLK\*/B2CLK\* are clock signals for the formatter board (4429).
The formatter converts between 38-bit FPS float and 16-bit host
words, requiring two 16-bit writes (high and low halves).

### Read Mapping (DIA/DIB/DIC → Register Read-back)

**DIA — Primary status/register reads via HOSTRS mux (4 sources):**

| HOSTRS1:0 | Flag | CLR | STRT | Source strobe | Register | DG Instruction |
|-----------|------|-----|------|--------------|----------|----------------|
| 00 | none | 0 | 0 | FN2HD | FN status | `DIA ac,FPS` |
| 01 | S | 0 | 1 | SR2HD | SWR readback | `DIAS ac,FPS` |
| 10 | C | 1 | 0 | LT2HD | LITES | `DIAC ac,FPS` |
| 11 | P | 1 | 1 | HADR2HD\* | APMA readback | `DIAP ac,FPS` |

HOSTRS0/HOSTRS1 are generated by Sheet 1 decode logic from the
DIA flag variant. The 2-bit mux selects which register drives
the host data bus.

**DIB — Formatter high read:**

| Source strobe | Register |
|--------------|----------|
| BH2HD\* | FMTH (Buffer High → Host Data) |

**DIC — Formatter low read:**

| Source strobe | Register |
|--------------|----------|
| BL2HD\* | FMTL (Buffer Low → Host Data) |

BH2HD\* and BL2HD\* bypass the HOSTRS mux — they are directly
gated by the DIB/DIC strobe. This makes sense: the formatter
read-back path is separate from the main register read path.

### Confidence Assessment

- **High confidence (from strobe names + circuit topology):**
  - DOA = Command/Control (SWR, FN, CTRL, INT)
  - DOB = DMA (WC, HMA, APMA, DMA start)
  - DOC = Formatter (FMTH, FMTL)
  - DIA = status reads (FN, SWR, LITES, APMA) via HOSTRS mux
  - DIB = FMTH, DIC = FMTL
  - Three subdevice DONE/BUSY pairs

- **High confidence (from netlist analysis + DG conventions + DeepSeek
  cross-check):** Flag assignment follows standard 2-to-4 NAND decode
  of latched CLR/STRT bits:
  - none (00) = primary register (SWR, WC, FMTH, FN-read)
  - S (01) = secondary register (FN, HMA, FMTL, SWR-read)
  - C (10) = configuration (CTRL, APMA, —, LITES-read)
  - P (11) = action/pulse (INT, DMA start, —, APMA-read)

- **To verify on hardware:** Run fps_probe.asm Phase 3 (SWR/FN pair
  test) as a quick sanity check. If `DOA` + `DOAS` produces the
  DEP/EXAM handshake, the full mapping is confirmed.

### Subdevice Flag Mapping (from Sheet 4)

The I/O flag variants (Start/Clear/Pulse) on NIOC/NIOS/NIOP
instructions control the three DONE/BUSY flip-flop pairs:

| Subdevice | AP2:1:0 | DONE/BUSY | Clear by | Set by |
|-----------|---------|-----------|----------|--------|
| 0 | 000 | RUN | NIOC dev,0 | NIOS dev,0 |
| 1 | 001 | DMA | NIOC dev,1 | NIOS dev,1 |
| 2 | 010 | CTL05 | NIOC dev,2 | NICS dev,2 |

These are independent of the DOA/DOB/DOC register mapping.
The skip instructions (SKPBN/SKPBZ/SKPDN/SKPDZ) test these
flags using the subdevice address field.

## What Remains To Verify

The complete flag-to-register mapping has been derived from netlist
analysis and DG Nova conventions, cross-checked with DeepSeek reasoner.
The mapping follows a standard 2-to-4 NAND decode of latched CLR/STRT.

**Hardware verification**: A single quick test confirms or refutes the
entire mapping: write 0xA5A5 via `DOA 0,FPS` (should write SWR), then
issue `DOAS 0,FPS` with a DEP-into-PSA command (should write FN). If
EXAM-PSA returns 0xA5A5, the DOA none=SWR / S=FN assignment is correct,
and by extension the entire decode pattern (same gates, same topology)
is confirmed for all channels.

## Complete Chip Inventory

### Sheet 1 — I/O Decode Logic

| Ref | Type | Function |
|-----|------|----------|
| C9 | 7442 | BCD-to-decimal decoder (device select low) |
| C10 | 7442 | BCD-to-decimal decoder (device select high) |
| D10, D12, D13 | 7414 | Schmitt trigger inverters (bus signal conditioning) |
| C8 | 7440 | Dual 4-input NAND (device-selected combine) |
| C6 | 7410 | Triple 3-input NAND (DOx/DIx qualify) |
| C1 | 7410 | Triple 3-input NAND (DOx/DIx qualify) |
| C7 | 74S74 | Dual D flip-flop (flag latch) |
| C5 | 74S74 | Dual D flip-flop (flag/timing latch) |
| D6 | 74S02 | Quad NOR (strobe generation) |
| D8 | 74S02 | Quad NOR (strobe generation) |
| D5 | 74S02 | Quad NOR (strobe generation) |
| D1-D4, D7 | 74S00 | Quad NAND (strobe generation) |
| D3 | 74S00 | Quad NAND (HOSTRS0/HOSTRS1 generation) |

### Sheet 2 — Interrupt, DMA, Power Monitor

| Ref | Type | Function |
|-----|------|----------|
| C11 | 74S74 | Dual D flip-flop (interrupt enable/pending) |
| A10 | 74S74 | Dual D flip-flop (RQENB capture) |
| C7 | 74S74 | Dual D flip-flop (DMA control) |
| B15 | 74S74 | Dual D flip-flop (DMA handshake) |
| A13 | 74S74 | Dual D flip-flop (DMA/interrupt state) |
| A15 | 74S74 | Dual D flip-flop (DMA state) |
| B9 | 7410 | Triple 3-input NAND (interrupt qualify) |
| A11 | 74S10 | Triple 3-input NAND (DMA/interrupt qualify) |
| A12 | 74S10 | Triple 3-input NAND (SYRT\*A qualify) |
| B10 | 74S08 | Quad AND (priority chain) |
| B11 | 7400 | Quad NAND (interrupt combine) |
| B14 | 7400 | Quad NAND (DMA qualify) |
| B16 | 74132 | Quad Schmitt NAND (debounce) |
| B12 | 74S04 | Hex inverter |
| B13 | 74S04 | Hex inverter |
| A14 | 7414 | Hex Schmitt inverter (DMA signal condition) |
| B6 | 7414 | Hex Schmitt inverter (WC=0, DMABUSY condition) |
| C2 | 7404 | Hex inverter |
| C13 | 7417 | Hex open-collector buffer (bus drive) |
| C16 | 7417 | Hex open-collector buffer (device code jumpers) |
| D8 | 74S00 | Quad NAND (DMA combine) |
| C15 | LM311 | Comparator (power-fail detection) |
| C15CR1 | 3.3V Zener | Reference for power monitor |
| C8 | 7440 | Dual 4-input NAND |
| B8 | 7438 | Quad OC NAND (SELB\*/SELD\* drive) |

### Sheet 3 — Data Bus Transceivers

| Ref | Type | Function |
|-----|------|----------|
| D13 | 8640 | Bus transceiver (PIO bits 0-7) |
| D14 | 74S38 | Quad OC NAND (PIO bits 0-7 drive) |
| D15 | 8640 | Bus transceiver (PIO bits 8-15) |
| D16 | 74S38 | Quad OC NAND (PIO bits 8-15 drive) |
| D11 | 8640 | Bus transceiver (DMA bits 0-7) |
| D12 | 74S38 | Quad OC NAND (DMA bits 0-7 drive) |
| D17 | 8640 | Bus transceiver (DMA bits 8-15) |
| D18 | 74S38 | Quad OC NAND (DMA bits 8-15 drive) |
| C14 | 74365 | Hex tri-state buffer (PIO read path) |
| C12 | 74365 | Hex tri-state buffer (PIO read path) |
| C17 | 74365 | Hex tri-state buffer (DMA read path) |
| A16 | 74S02 | Quad NOR (direction control) |
| B10 | 74S08 | Quad AND (direction qualify) |
| B17 | 74S37 | Quad NAND buffer (bus drive) |

### Sheet 4 — Flag Flip-Flops and CTRL Decode

| Ref | Type | Function |
|-----|------|----------|
| A6 | 7474 | Dual D flip-flop (RUN DONE / RUN BUSY) |
| A7 | 7474 | Dual D flip-flop (DMA DONE / DMA BUSY) |
| A8 | 7474 | Dual D flip-flop (CTL05 DONE / CTL05 BUSY) |
| C3 | 74S10 | Triple 3-input NAND (CLR/STRT decode) |
| B5 | 74S11 | Triple 3-input AND (subdevice qualify) |
| B4 | 7402 | Quad NOR (flag signal generation) |
| B3 | 7402 | Quad NOR (flag signal generation) |
| A5 | 7402 | Quad NOR (NIOCAP1/NIOCAP2) |
| A3 | 7404 | Hex inverter (NIOCAP/NIOSAP inversion) |
| A4 | 7427 | Triple 3-input NOR (NIOSAP0/1, NICSAP2) |
| A9 | 7400 | Quad NAND (DONE + subdevice select combine) |
| B6 | 7414 | Hex Schmitt inverter (RUN signal condition) |
| B7, B8 | 7438 | Quad OC NAND (SELB\*/SELD\* combine) |
| B9 | 7410 | Triple 3-input NAND (CTL05 + subdevice) |
| D9 | 7404 | Hex inverter (CLINTR\* inversion) |
| B2 | 7474 | Dual D flip-flop (1 section spare) |
