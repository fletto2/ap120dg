# FPS AP-120B / FPS-100 Microcode Reference

## Overview

The AP-120B and FPS-100 execute 64-bit horizontal microinstructions from
Program Store (PS) memory at 6 MHz (167ns per cycle). Each instruction
controls all functional units simultaneously:

- S-pad ALU (integer address/loop operations)
- Floating-point adder (38-bit pipeline, 2-stage)
- Floating-point multiplier (38-bit pipeline, 3-stage)
- Data Pad X and Y memories (register files)
- Main Data memory access
- Table Memory ROM access
- Branch/jump control
- Address register updates

This document is derived from the AP-120B Processor Handbook (860-7259-003),
the FORTRAN simulator (SIM100.FTN, specifically the SPLIT subroutine), and
verified against decoded .APO microcode objects.

## 64-Bit Instruction Word Layout

Bit 0 = MSB (leftmost). The instruction is stored as four 16-bit words
in Program Store and in .APO/.HSR files.

```
Bit(s)  Width  Field   Description
------  -----  ------  -----------
0       1      DF      Data Flow: 0=normal, 1=bit-reverse addressing + extended ops
1-3     3      SOP     S-pad operation
4-5     2      SH      Shift control
6-9     4      SPS     S-pad source register (0-15) OR SPEC code when SOP=1
10-13   4      SPD     S-pad destination register (0-15) OR SPEC subfield
14-16   3      FADD    Floating adder operation
17-19   3      A1      Adder input 1 select
20-22   3      A2      Adder input 2 select
23-26   4      COND    Branch condition
27-31   5      DISP    Branch displacement (signed, -16 to +15)
32-33   2      DPX     Data Pad X write enable + source
34-35   2      DPY     Data Pad Y write enable + source
36-38   3      DPBS    Data Pad Bus select (DB bus source)
39-41   3      XR      DPX read index offset (-4 to +3 from DPA)
42-44   3      YR      DPY read index offset (-4 to +3 from DPA)
45-47   3      XW      DPX write index offset (-4 to +3 from DPA)
48-50   3      YW      DPY write index offset (disabled when VALUE active)
51      1      FM      Start floating multiply (0=no, 1=yes)
52-53   2      M1      Multiplier input 1 select
54-55   2      M2      Multiplier input 2 select
56-57   2      MI      Memory input (write to MD) select
58-59   2      MA      Memory Address register operation
60-61   2      DPA     Data Pad Address register operation
62-63   2      TMA     Table Memory Address register operation
------  -----  ------  -----------
Total: 64 bits
```

When `DPBS=2` (VALUE) or `SOP=1, SPS=14` (LDSPI), bits 48-63 are
repurposed as a 16-bit immediate constant. Fields YW, FM, M1, M2, MI,
MA, DPA, TMA are disabled.

## Field Encodings

### SOP (S-pad Operation, 3 bits)

| Code | Mnemonic | Operation |
|------|----------|-----------|
| 0 | NOP | No s-pad operation |
| 1 | SPEC | Special operation (see SPS subfield) |
| 2 | ADD | SPD = SPD + SPS |
| 3 | SUB | SPD = SPD - SPS |
| 4 | MOV | SPD = SPS |
| 5 | AND | SPD = SPD & SPS |
| 6 | OR | SPD = SPD | SPS (logical OR via De Morgan's) |
| 7 | EQV | SPD = ~(SPD ^ SPS) (equivalence / XNOR) |

### SPS when SOP=1 (SPEC Operations)

| Code | Mnemonic | Description |
|------|----------|-------------|
| 0 | STEST | Test s-pad condition (see COND=1 below) |
| 1 | HOSTPNL | Host panel operations (SWDB, etc.) |
| 2 | SETPSA | Set PSA from s-pad value |
| 3 | (reserved) | |
| 4 | SPECINT | Interrupt operations |
| 5 | HALT | Stop AP execution |
| 6-7 | (reserved) | |
| 8 | CLR | SPD = 0 |
| 9 | INC | SPD = SPD + 1 |
| 10 | DEC | SPD = SPD - 1 |
| 11 | COM | SPD = ~SPD (complement) |
| 12 | LDSPE | Load s-pad from expression |
| 13 | (reserved) | |
| 14 | LDSPI | SPD = VALUE (16-bit immediate) |
| 15 | LDSPT | Load s-pad from table |

### SPS=8 with SOP=1 (JMP/JSR)

The SPD field encodes the jump mode:
- SPD bit 0: 0=JMP, 1=JSR (saves return address on stack)
- SPD bits 1-2: target address mode:
  - 0: VALUE (absolute address from bits 48-63)
  - 1: PC+VALUE (relative)
  - 2: TMA (from Table Memory Address register)
  - 3: SWR (from host Switch Register)

### SH (Shift, 2 bits)

| Code | Mnemonic | Operation |
|------|----------|-----------|
| 0 | NOP | No shift |
| 1 | L | Rotate left 1 bit (16-bit, through carry) |
| 2 | RR | Rotate right 1 bit |
| 3 | R | Logical right shift 1 bit |

### FADD (Floating Adder Operation, 3 bits)

| Code | Mnemonic | Operation |
|------|----------|-----------|
| 0 | NOP | No adder operation |
| 1 | FSUBR | FA = A2 - A1 (reverse subtract) |
| 2 | FSUB | FA = A1 - A2 |
| 3 | FADD | FA = A1 + A2 |
| 4 | FEQV | FA = ~(A1 ^ A2) (bitwise equivalence) |
| 5 | FAND | FA = A1 & A2 (bitwise AND) |
| 6 | FOR | FA = A1 | A2 (bitwise OR) |
| 7 | I/O | I/O group operations (see A1/A2 for subcode) |

### A1, A2 (Adder Input Select, 3 bits each)

| Code | A1 source | A2 source |
|------|-----------|-----------|
| 0 | NOP | NOP |
| 1 | FA (previous result) | FA (previous result) |
| 2 | DPX | DPX |
| 3 | DPY | DPY |
| 4 | MD (main data) | MD |
| 5 | ZERO | ZERO |
| 6 | ZERO | MDPX |
| 7 | ZERO | EDPX |

### COND (Branch Condition, 4 bits)

| Code | Mnemonic | Condition |
|------|----------|-----------|
| 0 | NOP | No branch |
| 1 | STEST | Test s-pad status (condition in SPD field) |
| 2 | BR | Unconditional branch |
| 3 | BINTRQ | Branch if interrupt request |
| 4 | BION | Branch if I/O ready |
| 5 | BIOZ | Branch if I/O not ready |
| 6 | BFPE | Branch if float error |
| 7 | RETURN | Return from subroutine (pop SRS) |
| 8 | BFEQ | Branch if float result = 0 |
| 9 | BFNE | Branch if float result != 0 |
| 10 | BFGE | Branch if float result >= 0 |
| 11 | BFGT | Branch if float result > 0 |
| 12 | BEQ | Branch if s-pad result = 0 |
| 13 | BNE | Branch if s-pad result != 0 |
| 14 | BGE | Branch if s-pad result >= 0 |
| 15 | BGT | Branch if s-pad result > 0 |

Branch target = PSA + 1 + signed(DISP), where DISP is a signed 5-bit
value (range -16 to +15).

### DPBS (Data Pad Bus Select, 3 bits)

| Code | Source | Description |
|------|--------|-------------|
| 0 | NOP | No bus operation |
| 1 | INBS | Input bus (from I/O device) |
| 2 | VALUE | 16-bit immediate constant (bits 48-63) |
| 3 | DPX | Data Pad X read value |
| 4 | DPY | Data Pad Y read value |
| 5 | MD | Main Data memory |
| 6 | SPFN | S-pad function output (last s-pad result) |
| 7 | TM | Table Memory ROM |

### DPX, DPY (Data Pad Write, 2 bits each)

| Code | Source | Description |
|------|--------|-------------|
| 0 | NOP | No write |
| 1 | DB | Data pad bus (DPBS source) |
| 2 | FA | Floating adder result |
| 3 | FM | Floating multiplier result |

### M1, M2 (Multiplier Inputs, 2 bits each)

| Code | M1 source | M2 source |
|------|-----------|-----------|
| 0 | NOP | NOP |
| 1 | FM (prev) | FM (prev) |
| 2 | DPX | DPX |
| 3 | DPY | TM (table memory) |

### MI (Memory Input / Write Select, 2 bits)

| Code | Source | Description |
|------|--------|-------------|
| 0 | NOP | No memory write |
| 1 | INBS | Input bus |
| 2 | VALUE | 16-bit immediate |
| 3 | DPBS | Data pad bus value |

### MA, DPA, TMA (Address Register Operations, 2 bits each)

| Code | Operation |
|------|-----------|
| 0 | NOP |
| 1 | INC (increment by 1) |
| 2 | DEC (decrement by 1) |
| 3 | SET (load from s-pad destination register) |

## 38-Bit Floating Point Format

| Bits | Width | Field |
|------|-------|-------|
| 37-28 | 10 | Exponent (biased by 512) |
| 27-0 | 28 | Mantissa (2's complement) |

- Range: approximately 2^-512 to 2^511
- Precision: 28 bits mantissa ~ 8.4 decimal digits
- Zero is represented as all-zeros
- Mantissa is normalized: 0.25 <= |mantissa| < 0.5
- Negative numbers use 2's complement mantissa

## Pipeline Timing

The AP has pipelined execution. Results are NOT available immediately:

| Unit | Pipeline depth | Latency |
|------|---------------|---------|
| S-pad ALU | 1 | Same cycle (combinational) |
| Floating adder | 2 stages | Result available 2 cycles later |
| Floating multiplier | 3 stages | Result available 3 cycles later |
| Main Data memory | 2-3 stages | Read result 2-3 cycles later |
| Table Memory | 2 stages | Read result 2 cycles later |

Programs must account for pipeline latency. For example, after starting
FADD with inputs from DPX and DPY, the FA result cannot be read until
2 instructions later.

## .APO File Format

The .APO (AP Object) file is a text format containing assembled microcode:

```
     3      ***TITLE
ROUTINENAME
    12      7      ***FPB        (Function Parameter Block)
... (parameter descriptions)
    13      1      ***AENTRY     (Assembly entry point)
ROUTINENAME  addr  nargs  nwords
     4      1      ***ENTRY      (Callable entry point)
FNAME        addr  nargs  nwords
     0     N      0      ***CODE  (Microcode section)
loadaddr  0  pssize  mdsize      (header: load address, 0, PS words needed, MD words needed)
*  reloc_info                     (relocation records, start with *)
w0  w1  w2  w3                   (four octal 16-bit words = one 64-bit PS word)
...
     5      N      ***EXT        (External references)
EXTNAME
     1      ***END
```

The four octal words are: bits 0-15, bits 16-31, bits 32-47, bits 48-63,
where bit 0 is the MSB.

Lines starting with `*` (but not `***`) are relocation records and should
be skipped when loading microcode.

## .HSR File Format

The .HSR (Host Subroutine) files embed the same microcode as PDP-11
MACRO-11 assembly data:

```
CODE:       N.                    ; N microinstructions
        040000,000000,000000,000060   ; 4 comma-separated octal 16-bit words
        000000,000000,000000,000020   ; same encoding as .APO CODE section
        ...
```

## Memory Map

| Memory | Size | Word Width | Description |
|--------|------|-----------|-------------|
| Program Store (PS) | 1K or 4K | 64 bits | Microcode instructions |
| Main Data (MD) | 8K-64K | 38 bits | Data arrays for processing |
| Table Memory (TM) | 2.5K | 38 bits | ROM: sin, cos, FFT twiddle factors |
| Scratch Pad (SP) | 16 | 16 bits | Integer registers for loop control |
| Data Pad X (DPX) | 32 | 38 bits | Register file (pipeline source/dest) |
| Data Pad Y (DPY) | 32 | 38 bits | Register file (pipeline source/dest) |
| Subroutine Return Stack (SRS) | 16 | 12 bits | Return addresses for JSR/RET |

## Execution Example: VADD

The VADD (vector add) routine from BAALIB.APO adds two vectors:

```
PS[0]:  040674 000000 000000 000000   ; MOV R6,R15 (save loop count)
PS[1]:  040000 000431 000000 000060   ; MOV R0,R0; loop setup
PS[2]:  040210 000000 000000 000060   ; MOV R2,R2; setup
PS[3]:  030520 000000 000000 000000   ; SUB R5,R4; decrement counter
PS[4]:  020100 000000 045004 000060   ; ADD R1,R0; INCMA; read MD
PS[5]:  020310 142000 015500 100060   ; ADD R3,R2; FSUBR; DPX+DPY; INCMA
PS[6]:  000001 123000 000440 000000   ; FADD; DPX<FA; pipeline fill
PS[7]:  020100 000000 045004 000060   ; ADD R1,R0; INCMA; read MD
PS[8]:  020310 141000 015000 100060   ; ADD R3,R2; FSUB; INCMA; loop body
PS[9]:  020521 123556 000440 000160   ; ADD R5,R4; FADD; DPX<FA; write MD; BNE loop
PS[10]: 000000 000340 000000 000000   ; RET (return from subroutine)
```

This loop processes one vector element per cycle after pipeline fill,
achieving peak throughput of 6 MFLOPS (one FADD per 167ns cycle).

## References

- AP-120B Processor Handbook (860-7259-003), Feb 1979
- FPS-100 Assembler Reference Manual (800-7428-001)
- SIM100.FTN (FORTRAN simulator, SPLIT subroutine for decode)
- Programmers Reference Manual Parts 1 & 2 (FPS-7319)
