;======================================================================
; FPS-100 / AP-120B  Data General Nova  Register Probe Test  v3
;======================================================================
;
; PURPOSE
; -------
; Systematically probes the FPS array processor interface at DG Nova
; device code 055 (octal) to determine which DOA/DOB/DOC instruction
; accesses which FPS register, then verifies the FN command protocol
; documented in the AP-120B Processor Handbook (860-7259-003).
;
; BACKGROUND
; ----------
; The FPS host interface is fundamentally a TWO-REGISTER COMMAND
; PROTOCOL. From the Processor Handbook, section 4.7:
;
;   1. Host writes DATA to SWR (Switch Register)
;   2. Host writes COMMANDS to FN (Function Register)
;   3. Host reads STATUS from FN
;
; The FN register has dual function:
;   WRITE: triggers panel operations (DEP, EXAM, START, STOP, etc.)
;   READ:  returns AP status (bit 0/MSB = halted, bit 1 = SWR ack)
;
; FN command word format (bit 0 = MSB):
;   Bit 0:     STOP/HALTED
;   Bit 1:     START (at address in SWR)
;   Bit 2:     CONT (continue from PSA)
;   Bit 3:     STEP
;   Bit 4:     RESET
;   Bit 5:     EXAM (examine register per REG SELECT)
;   Bit 6:     DEP  (deposit SWR into register per REG SELECT)
;   Bit 7:     BREAK
;   Bits 8-9:  INC  (0=none, 1=MA, 2=DPA, 3=TMA)
;   Bits 10-11: WORD (which 16-bit portion of wide register, 0-3)
;   Bits 12-15: REG SELECT (which register, 0-17 octal)
;
; REG SELECT: 0=PSA, 1=SPD, 2=MA, 3=TMA, 4=DPA, 5=SPFN, 6=STATUS,
;   7=DA, 10=PS(by TMA), 15=MD(by MA)
;
; The DMA registers (CTL, WC, HMA, APMA) must also be directly
; writable for DMA setup. These likely use additional DOx instructions.
;
; PHASES
; ------
; Phase 1: Find FN read channel.
;          NIOC + read all 12 DI variants. The one returning non-zero
;          (AP halted bit in MSB) reads FN status.
;
; Phase 2: Find SWR write and FN write channels.
;          Write 0xFFFF to all 12 DO variants, then read the FN channel
;          found in Phase 1. If FN shows SWR-ack (bit 1), that DO
;          writes SWR. Also watch LITES LEDs on FPS front panel.
;
; Phase 3: Verify FN command protocol.
;          Using the SWR and FN channels found in Phases 1-2, execute
;          the Processor Handbook loading sequence:
;          - Deposit a known value into PSA via SWR+FN
;          - Examine PSA back via FN EXAM command
;          - Verify the value matches
;
; Phase 4: Find DMA registers (CTL, WC, HMA, APMA).
;          Write distinctive patterns to remaining DO variants,
;          then read back via remaining DI variants.
;
; Phase 5: DONE/BUSY flag behavior.
;
; HOW TO USE
; ----------
; 1. Load at address 0100, start execution at 0100
; 2. At each HALT, examine AC0 (and AC1/AC2/AC3 where noted)
; 3. Record ALL values on paper -- you need the complete picture
; 4. Press CONTINUE to advance
;
; IMPORTANT: The test assumes the AP is halted (power-on state).
; NIOC resets the interface flags, not the AP itself.
;
; RESULTS MEMORY MAP (zero page 050-063)
; ----------------------------------------
; 050=DIA  051=DIAS 052=DIAC 053=DIAP  (buffer A reads)
; 054=DIB  055=DIBS 056=DIBC 057=DIBP  (buffer B reads)
; 060=DIC  061=DICS 062=DICC 063=DICP  (buffer C reads)
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
    dw 0xFFFF               ; 040: all bits
zpat_8000:
    dw 0x8000               ; 041: MSB only (= FN STOP bit)
zpat_a5:
    dw 0xA5A5               ; 042: distinctive readback pattern
zstart:
    dw 64                   ; 043: address of phase1 (0100 octal)
zone:
    dw 1                    ; 044: constant 1
ztwo:
    dw 2                    ; 045: constant 2

; FN command words (from Processor Handbook encoding)
; DEP = bit 6 = 0x0200
; EXAM = bit 5 = 0x0400
; REG SELECT in bits 12-15 (lowest 4 bits)
; WORD in bits 10-11
zfn_dep_psa:
    dw 0x0200               ; 046: DEP into PSA (REGSEL=0)
zfn_exam_psa:
    dw 0x0400               ; 047: EXAM PSA (REGSEL=0)

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
; PHASE 1: Read all 12 DI variants to find which one reads FN status
;          After reset, AP should be halted -> FN bit 0 (MSB) set
;          NIOC before each to ensure clean interface state
;======================================================================

phase1:
    ; --- Buffer A ---
    NIOC FPS
    DIA  0, FPS
    STA  0, 050, 0
    HALT                    ; AC0 = DIA result

    NIOC FPS
    DIAS 0, FPS
    STA  0, 051, 0
    HALT

    NIOC FPS
    DIAC 0, FPS
    STA  0, 052, 0
    HALT

    NIOC FPS
    DIAP 0, FPS
    STA  0, 053, 0
    HALT

    ; --- Buffer B ---
    NIOC FPS
    DIB  0, FPS
    STA  0, 054, 0
    HALT

    NIOC FPS
    DIBS 0, FPS
    STA  0, 055, 0
    HALT

    NIOC FPS
    DIBC 0, FPS
    STA  0, 056, 0
    HALT

    NIOC FPS
    DIBP 0, FPS
    STA  0, 057, 0
    HALT

    ; --- Buffer C ---
    NIOC FPS
    DIC  0, FPS
    STA  0, 060, 0
    HALT

    NIOC FPS
    DICS 0, FPS
    STA  0, 061, 0
    HALT

    NIOC FPS
    DICC 0, FPS
    STA  0, 062, 0
    HALT

    NIOC FPS
    DICP 0, FPS
    STA  0, 063, 0
    HALT

;======================================================================
; PHASE 2: Write 0xFFFF to each DO variant, read back with ALL three
;          DI base instructions. Observe:
;          - Which DO changes the LITES LEDs? -> writes LITES
;          - Which DI returns a changed value? -> reads that register
;          - AC1=DIA, AC2=DIB, AC3=DIC after each write
;======================================================================

phase2:
    ; --- Buffer A writes ---
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOA  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOA(no flag): AC1=DIA, AC2=DIB, AC3=DIC

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOA+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAC 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOA+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOAP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOA+Pulse

    ; --- Buffer B writes ---
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOB  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOB(no flag)

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOB+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBC 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOB+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOBP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOB+Pulse

    ; --- Buffer C writes ---
    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOC  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOC(no flag)

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOC+Start

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCC 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOC+Clear

    NIOC FPS
    LDA  0, zpat_ffff, 0
    DOCP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOC+Pulse

;======================================================================
; PHASE 3: FN command protocol verification
;
; By this point the operator should know from Phase 1 and Phase 2:
;   - Which DI reads FN (Phase 1: the one with MSB set)
;   - Which DO writes SWR and which DO writes FN
;
; This phase tests ALL 9 DO-pair combinations for the SWR+FN protocol:
;   DOA+DOA, DOA+DOB, DOA+DOC, DOB+DOA, DOB+DOB, DOB+DOC, etc.
;
; For each pair: first DO = write 0xA5A5 to SWR candidate,
;                second DO = write DEP-into-PSA command to FN candidate,
;                then read all three DI to see if the deposit happened
;                (PSA should now contain 0xA5A5, visible via EXAM)
;
; After DEP, we write EXAM-PSA command and read back. If the value
; in LITES (or wherever EXAM output goes) = 0xA5A5, this DO pair
; is correct: first DO = SWR, second DO = FN.
;======================================================================

phase3:
    ; --- Test: DOA=SWR, DOB=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0     ; 0xA5A5
    DOA  0, FPS             ; Candidate SWR write
    LDA  0, zfn_dep_psa, 0 ; DEP into PSA command (0x0200)
    DOB  0, FPS             ; Candidate FN write
    ; Now examine PSA back
    LDA  0, zfn_exam_psa, 0 ; EXAM PSA command (0x0400)
    DOB  0, FPS             ; Write EXAM command
    ; Read all three channels to find the EXAM result
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; If any AC = 0xA5A5, DOA=SWR DOB=FN works!

    ; --- Test: DOA=SWR, DOC=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOA  0, FPS
    LDA  0, zfn_dep_psa, 0
    DOC  0, FPS
    LDA  0, zfn_exam_psa, 0
    DOC  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; If 0xA5A5 found, DOA=SWR DOC=FN

    ; --- Test: DOB=SWR, DOA=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOB  0, FPS
    LDA  0, zfn_dep_psa, 0
    DOA  0, FPS
    LDA  0, zfn_exam_psa, 0
    DOA  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; If 0xA5A5 found, DOB=SWR DOA=FN

    ; --- Test: DOB=SWR, DOC=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOB  0, FPS
    LDA  0, zfn_dep_psa, 0
    DOC  0, FPS
    LDA  0, zfn_exam_psa, 0
    DOC  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT

    ; --- Test: DOC=SWR, DOA=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOC  0, FPS
    LDA  0, zfn_dep_psa, 0
    DOA  0, FPS
    LDA  0, zfn_exam_psa, 0
    DOA  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT

    ; --- Test: DOC=SWR, DOB=FN ---
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOC  0, FPS
    LDA  0, zfn_dep_psa, 0
    DOB  0, FPS
    LDA  0, zfn_exam_psa, 0
    DOB  0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT

;======================================================================
; PHASE 4: DMA register discovery
;          After Phase 3 identifies SWR and FN channels, the remaining
;          DOx channel(s) likely access CTL and/or DMA registers.
;          Write distinct patterns and read back to find them.
;
;          Also test flag variants of the SWR/FN channels, which may
;          map to CTL, WC, HMA, APMA.
;======================================================================

phase4:
    ; Write 0x0001 (= CTL HDMA start bit) to each DO variant
    ; Then read all DI -- CTL is readable and bit 15 (HDMA) should
    ; latch or reflect. BE CAREFUL: this might start a DMA transfer
    ; if it actually hits CTL with the start bit!
    ;
    ; Safer: write 0x0008 (= CTL IHHALT bit only, no DMA start)

    NIOC FPS
    SUB  0, 0
    INC  0, 0               ; AC0 = 1... no, INC makes it 1
    ; Actually we want 0x0008 = IHHALT bit (bit 3 from MSB = bit 12 from LSB)
    ; 0x0008 = 8 decimal
    ; Use a smarter approach: just write each DOx with a flag variant
    ; and see if CTL status changes when read

    ; Use 0xA5A5 (safe pattern -- no HDMA start bit) with flag variants
    ; to find which DOx+flag accesses DMA registers.
    ; Read back all DI channels after each write.

    ; DOA+Start
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOAS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOAS 0xA5A5: which DI shows it?

    ; DOB+Start
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOBS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOBS 0xA5A5: which DI shows it?

    ; DOC+Start
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOCS 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOCS 0xA5A5: which DI shows it?

    ; Also try Pulse variants
    ; DOA+Pulse
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOAP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOAP 0xA5A5

    ; DOB+Pulse
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOBP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOBP 0xA5A5

    ; DOC+Pulse
    NIOC FPS
    LDA  0, zpat_a5, 0
    DOCP 0, FPS
    DIA  1, FPS
    DIB  2, FPS
    DIC  3, FPS
    HALT                    ; DOCP 0xA5A5

;======================================================================
; PHASE 5: DONE/BUSY flag behavior
;======================================================================

phase5:
    ; After NIOC: expect BUSY=0, DONE=0 -> AC0=0
    NIOC FPS
    SUB  0, 0
    SKPBN FPS
    JMP  p5a
    LDA  0, zone, 0
p5a:
    SKPDN FPS
    JMP  p5b
    LDA  1, ztwo, 0
    ADD  1, 0
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
    HALT

    ; After NIOP: device-specific
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
    HALT

;======================================================================
; END
;======================================================================

    JMP  @zstart, 0
