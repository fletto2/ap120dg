;======================================================================
; FPS-100 / AP-120B  Data General Nova  Register Probe Test  v2
;======================================================================
;
; PURPOSE
; -------
; Systematically probes the FPS array processor interface at DG Nova
; device code 055 (octal) to determine which DOA/DOB/DOC instruction
; (with which S/C/P flag variant) accesses which FPS register.
;
; The exact DOx-to-register mapping is currently unknown. This test
; discovers it empirically by exercising all 24 I/O instruction
; variants and observing the results.
;
; BACKGROUND
; ----------
; On the PDP-11, the FPS uses 10 memory-mapped registers. On the DG
; Nova, these must be accessed through 3 I/O buffers (A, B, C) x
; 4 flag variants (none, S, C, P) = 12 write + 12 read = 24 total
; instruction variants.
;
; WHAT WE EXPECT AFTER RESET
; ---------------------------
; After NIOC (I/O Clear), the interface BUSY and DONE flags are
; cleared. The AP processor itself should be halted (power-on state).
; The FN register should have a non-zero value indicating halted
; status -- on PDP-11 this is bit 15 (MSB), which corresponds to
; the MSB of the 16-bit word on the DG data bus (>= 0x8000).
; However, we check for ANY non-zero value as a fallback since
; the bit position may differ on the physical DG interface.
;
; IMPORTANT: NIOC resets the INTERFACE (BUSY/DONE flags), not the
; AP processor itself. The AP halt state is set by the AP hardware
; at power-on or by writing APIRT to the CTRL register.
;
; PHASES
; ------
; Phase 1: Read all 12 DI variants after reset (find FN register).
;          NIOC is issued before EACH read to ensure clean state,
;          since DI+Start would set BUSY as a side effect.
;
; Phase 2: Write test patterns to DO variants (find LITES register).
;          NIOC is issued before EACH write. Watch FPS front panel
;          LEDs after each HALT. Two sub-passes:
;            Pass A: 0xFFFF (all bits) to all 12 DO variants
;            Pass B: 0x8000 (MSB only) to DOA/DOB/DOC base variants
;
; Phase 3: Write-readback test. For each DO variant, write a unique
;          pattern, then read all 3 DI base variants (DIA/DIB/DIC)
;          to find which DO/DI pairs access the same register.
;
; Phase 4: Two-step REGSEL test. Write an address value via DOA,
;          then read/write data via DOB/DOC. Tests whether the
;          FPS-100 uses a two-step register-select mechanism.
;
; Phase 5: DONE/BUSY flag behavior test.
;
; HOW TO USE
; ----------
; 1. Load at address 0100, start execution at 0100
; 2. At each HALT, examine AC0 (and AC1/AC2/AC3 where noted)
; 3. Press CONTINUE to proceed
; 4. Record all values -- the mapping will be clear from the data
;
; RESULTS MEMORY MAP (zero page)
; --------------------------------
; 050-063: Phase 1 read results (12 words, one per DI variant)
;   050=DIA  051=DIAS 052=DIAC 053=DIAP
;   054=DIB  055=DIBS 056=DIBC 057=DIBP
;   060=DIC  061=DICS 062=DICC 063=DICP
;
; NOTE ON DG BIT NUMBERING
; -------------------------
; DG bit 0 = MSB (leftmost). PDP-11 bit 0 = LSB (rightmost).
; A 16-bit value 0x8000 has DG bit 0 set (= PDP-11 bit 15).
;
; ASSEMBLER (from repository root):
;   cd dgasm && mkdir build && cd build && cmake .. && make && cd ../..
;   ./dgasm/build/dgasm -o fps_probe.bin fps_probe.asm
;======================================================================

;----------------------------------------------------------------------
; Zero-page data (addresses 040-067)
;----------------------------------------------------------------------

    org 040

zpat_ffff:
    dw 0xFFFF               ; 040: all bits set
zpat_0001:
    dw 0x0001               ; 041: LSB only
zpat_8000:
    dw 0x8000               ; 042: MSB only
zpat_a5:
    dw 0xA5A5               ; 043: distinctive pattern for readback
zstart:
    dw 64                   ; 044: address of phase1 (0100 octal = 64 decimal)
zone:
    dw 1                    ; 045: constant 1
ztwo:
    dw 2                    ; 046: constant 2
zthree:
    dw 3                    ; 047: constant 3

    org 050
    dw 0    ; 050: DIA result
    dw 0    ; 051: DIAS
    dw 0    ; 052: DIAC
    dw 0    ; 053: DIAP
    dw 0    ; 054: DIB
    dw 0    ; 055: DIBS
    dw 0    ; 056: DIBC
    dw 0    ; 057: DIBP
    dw 0    ; 060: DIC
    dw 0    ; 061: DICS
    dw 0    ; 062: DICC
    dw 0    ; 063: DICP

;----------------------------------------------------------------------
; Code (starts at address 0100)
;----------------------------------------------------------------------

    org 0100
    dev FPS = 055

;======================================================================
; PHASE 1: Read all 12 DI variants to find FN register
;          NIOC before each read to ensure clean interface state
;======================================================================

phase1:
    ; Buffer A -- no flag
    NIOC FPS
    DIA  0, FPS
    STA  0, 050, 0
    HALT                    ; AC0 = DIA result

    ; Buffer A -- Start
    NIOC FPS
    DIAS 0, FPS
    STA  0, 051, 0
    HALT

    ; Buffer A -- Clear
    NIOC FPS
    DIAC 0, FPS
    STA  0, 052, 0
    HALT

    ; Buffer A -- Pulse
    NIOC FPS
    DIAP 0, FPS
    STA  0, 053, 0
    HALT

    ; Buffer B -- no flag
    NIOC FPS
    DIB  0, FPS
    STA  0, 054, 0
    HALT

    ; Buffer B -- Start
    NIOC FPS
    DIBS 0, FPS
    STA  0, 055, 0
    HALT

    ; Buffer B -- Clear
    NIOC FPS
    DIBC 0, FPS
    STA  0, 056, 0
    HALT

    ; Buffer B -- Pulse
    NIOC FPS
    DIBP 0, FPS
    STA  0, 057, 0
    HALT

    ; Buffer C -- no flag
    NIOC FPS
    DIC  0, FPS
    STA  0, 060, 0
    HALT

    ; Buffer C -- Start
    NIOC FPS
    DICS 0, FPS
    STA  0, 061, 0
    HALT

    ; Buffer C -- Clear
    NIOC FPS
    DICC 0, FPS
    STA  0, 062, 0
    HALT

    ; Buffer C -- Pulse
    NIOC FPS
    DICP 0, FPS
    STA  0, 063, 0
    HALT

;======================================================================
; PHASE 2: Write patterns, watch LITES LEDs on FPS front panel
;          NIOC before each write. Three passes with different patterns.
;======================================================================

phase2:
    ; --- Pass A: all bits (0xFFFF) ---
    ; Buffer A writes
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOA  0, FPS
    HALT                    ; Watch LEDs -- DOA, no flag, 0xFFFF

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAS 0, FPS
    HALT                    ; DOA+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAC 0, FPS
    HALT                    ; DOA+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAP 0, FPS
    HALT                    ; DOA+Pulse

    ; Buffer B writes
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOB  0, FPS
    HALT                    ; DOB, no flag

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBS 0, FPS
    HALT                    ; DOB+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBC 0, FPS
    HALT                    ; DOB+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBP 0, FPS
    HALT                    ; DOB+Pulse

    ; Buffer C writes
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOC  0, FPS
    HALT                    ; DOC, no flag

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCS 0, FPS
    HALT                    ; DOC+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCC 0, FPS
    HALT                    ; DOC+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCP 0, FPS
    HALT                    ; DOC+Pulse

    ; --- Pass B: MSB only (0x8000) -- which LITES instruction lights MSB? ---
    NIOC FPS
    LDA  0, zpat_8000, 0
    DOA  0, FPS
    HALT                    ; DOA 0x8000

    NIOC FPS
    LDA  0, zpat_8000, 0
    DOB  0, FPS
    HALT                    ; DOB 0x8000

    NIOC FPS
    LDA  0, zpat_8000, 0
    DOC  0, FPS
    HALT                    ; DOC 0x8000

;======================================================================
; PHASE 3: Write-readback matrix
;          Write 0xA5A5 via each base DO (no flag), then read DIA/DIB/DIC
;          to find which DO/DI pairs access the same register
;          AC1=DIA result, AC2=DIB result, AC3=DIC result
;======================================================================

phase3:
    ; Write via DOA, read back all three
    NIOC FPS
    LDA  0, zpat_a5, 0     ; 0xA5A5
    DOA  0, FPS
    DIA  1, FPS             ; Read buffer A
    DIB  2, FPS             ; Read buffer B
    DIC  3, FPS             ; Read buffer C
    HALT                    ; Which AC has 0xA5A5 back?

    ; Write via DOB, read back all three
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOB  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT

    ; Write via DOC, read back all three
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOC  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT

;======================================================================
; PHASE 4: Two-step REGSEL test (for FPS-100 with 4448 board)
;          Write address N via DOA, then read/write data via DOB
;          If two-step works, DOB should access different registers
;          depending on the DOA value
;======================================================================

phase4:
    ; Address 0 via DOA, then read DOB
    NIOC FPS
    SUB  0, 0               ; AC0 = 0 (register address 0)
    DOA  0, FPS             ; Set REGSEL = 0
    DIB  1, FPS             ; Read register 0
    HALT                    ; AC1 = register 0 contents

    ; Address 1 via DOA, then read DOB
    NIOC FPS
    LDA  0, zone, 0         ; AC0 = 1
    DOA  0, FPS             ; Set REGSEL = 1
    DIB  1, FPS             ; Read register 1
    HALT                    ; AC1 = register 1 contents

    ; Address 2 via DOA, then read DOB
    NIOC FPS
    LDA  0, ztwo, 0         ; AC0 = 2
    DOA  0, FPS
    DIB  1, FPS
    HALT

    ; Address 3 via DOA, then read DOB
    NIOC FPS
    LDA  0, zthree, 0       ; AC0 = 3
    DOA  0, FPS
    DIB  1, FPS
    HALT

    ; If these four halts show DIFFERENT values in AC1,
    ; then DOA sets a register address and DOB reads data.
    ; If they show the SAME value, two-step is not used.

    ; Also test DOA-then-DOC (in case DOC is the data port)
    NIOC FPS
    SUB  0, 0
    DOA  0, FPS
    DIC  1, FPS
    HALT                    ; AC1 = register 0 via DIC

    NIOC FPS
    LDA  0, zone, 0
    DOA  0, FPS
    DIC  1, FPS
    HALT                    ; AC1 = register 1 via DIC

;======================================================================
; PHASE 5: DONE/BUSY flag behavior
;======================================================================

phase5:
    ; After NIOC: expect BUSY=0, DONE=0 -> AC0=0
    NIOC FPS
    SUB  0, 0
    SKPBN FPS
    JMP  p5a
    LDA  0, zone, 0         ; Bit 0: BUSY is set
p5a:
    SKPDN FPS
    JMP  p5b
    LDA  1, ztwo, 0
    ADD  1, 0               ; Bit 1: DONE is set
p5b:
    HALT                    ; AC0: 0=both clear, 1=BUSY, 2=DONE, 3=both

    ; After NIOS: expect BUSY=1, DONE=0 -> AC0=1
    NIOS FPS
    SUB  0, 0
    SKPBN FPS
    JMP  p5c
    LDA  0, zone, 0
p5c:
    SKPDN FPS
    JMP  p5d
    LDA  1, ztwo, 0
    ADD  1, 0
p5d:
    HALT                    ; AC0: expect 1 (BUSY only)

    ; After NIOP: device-specific, unknown
    NIOP FPS
    SUB  0, 0
    SKPBN FPS
    JMP  p5e
    LDA  0, zone, 0
p5e:
    SKPDN FPS
    JMP  p5f
    LDA  1, ztwo, 0
    ADD  1, 0
p5f:
    HALT                    ; AC0: what did Pulse do?

;======================================================================
; END -- loop back for another run
;======================================================================

    JMP  @zstart, 0          ; Indirect jump through zero page -> phase1
