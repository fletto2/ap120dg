; DAPEX_DG.ASM -- FPS AP-120B / FPS-100 Host Driver for Data General Nova
;
; Port of DAPEX.MAC (PDP-11 RSX-11M) to DG Nova assembly.
; Register mapping from 280B schematic 512-3280-004 Rev B.
;
; Page-zero optimization: uses a software return stack at 030-037
; (auto-decrement locations) instead of per-routine save words.
; Constant deduplication: values that happen to be equal share one word.
;
; Assembled with dgasm: dgasm/build/dgasm -o dapex_dg.bin dapex_dg.asm

    dev FPS = 055

; ============================================================
; Page-zero layout (000-0177)
; ============================================================

    org 000

; --- Interrupt vectors (reserved by hardware) ---
intvec:
    dw 0                ; 000: interrupt save PC
intadr:
    dw 0                ; 001: interrupt handler address

; --- Return stack ---
; Uses auto-decrement locations 030-037 for pop.
; rsp points to next free slot. Push: STA val,@rsp / ISZ rsp
; Pop: use DSZ + JMP@ through auto-dec location.
; Simpler approach: just use rsp as index, manual inc/dec.
    org 002
rsp:
    dw rstk             ; 002: return stack pointer (init = rstk)
rsptmp:
    dw 0                ; 003: temp for stack ops

    org 010
; --- Return stack storage (8 deep, addresses 010-017) ---
rstk:
    dw 0                ; 010
    dw 0                ; 011
    dw 0                ; 012
    dw 0                ; 013
    dw 0                ; 014
    dw 0                ; 015
    dw 0                ; 016
    dw 0                ; 017

; --- State variables ---
runfg:
    dw 0                ; 020
savctl:
    dw 0                ; 021
fpswr:
    dw 0                ; 022
fpfnr:
    dw 0                ; 023
fplit:
    dw 0                ; 024
dmafg:
    dw 0                ; 025
savhma:
    dw 0                ; 026
savwc:
    dw 0                ; 027

; --- Auto-decrement locations 030-037 (used by hardware) ---
; We avoid these for general storage.
    org 040

; --- APEX message block ---
fpopt:
    dw 0                ; 040
fpsct:
    dw 0                ; 041
fpsw2:
    dw 0                ; 042
fpfn2:
    dw 0                ; 043

; --- Supervisor datum storage (8 words) ---
fpdat:
    dw 0                ; 044
    dw 0                ; 045
    dw 0                ; 046
    dw 0                ; 047
    dw 0                ; 050
    dw 0                ; 051
    dw 0                ; 052
    dw 0                ; 053
supvr:
    dw 0                ; 054
fperf:
    dw 0                ; 055
ercode:
    dw 0                ; 056

; --- Temporaries ---
aoutv:
    dw 0                ; 057
rdmha:
    dw 0                ; 060
rdmap:
    dw 0                ; 061
rdmwc:
    dw 0                ; 062
rdmcl:
    dw 0                ; 063
rapcmd:
    dw 0                ; 064
spltmp:
    dw 0                ; 065
splcnt:
    dw 0                ; 066
splpsa:
    dw 0                ; 067

; --- Constants (deduplicated) ---
cm1:
    dw -1               ; 070
cm4:
    dw -4               ; 071
cm8:
    dw -8               ; 072
rdwtmo:
    dw -32768           ; 073: RDWAIT timeout
; Shared constants (same value, multiple uses):
; 040000 = FN.ACK = FN.START
k40000:
    dw 040000           ; 074: ackbit / FN START
; 004000 = CTL.IHWC
k04000:
    dw 004000           ; 075: IHWC
; 010000 = CTL.IHHALT
k10000:
    dw 010000           ; 076: IHHALT
; 001000 = FN.DEP+PSA
k01000:
    dw 001000           ; 077: DEP into PSA

    org 0100
; 002000 = FN.EXAM = CTL.IHCB5 (same bit value!)
k02000:
    dw 002000           ; 0100: EXAM / IHCB5
; 000400 = LITES parity = CTL DLATE (same value!)
k00400:
    dw 000400           ; 0101: parity / DLATE
; 000200 = LITES stack overflow
k00200:
    dw 000200           ; 0102: stack overflow
; 001001 = FN DEP into SPD (REGSEL=1)
k01001:
    dw 001001           ; 0103: DEP SPD
pfpopt:
    dw fpopt            ; 0104: pointer to APEX block
pfpdat:
    dw fpdat            ; 0105: pointer to FPDAT array

; --- Subroutine pointers (only for cross-page indirect calls) ---
prdwt:
    dw RDWAIT           ; 0106
papwd:
    dw APWD             ; 0107
paperr:
    dw APERR            ; 0110
psndr:
    dw SENDER           ; 0111
pwtrun:
    dw WTRUN            ; 0112
prunap:
    dw RUNAP            ; 0113
preset:
    dw APRSET           ; 0114
phtst:
    dw HTST             ; 0115

; ============================================================
; Code at 0200
; ============================================================

    org 0200

; --- PUSH: save AC3 (return addr) onto stack ---
; Inline macro: STA 3, @rsp, 0 / ISZ rsp, 0
; --- POP+RET: pop return addr and jump to it ---
; Inline: DSZ rsp, 0 / JMP @@rsp, 0  (but double-indirect not available)
; Instead: DSZ rsp, 0 / LDA 3, @rsp, 0 / JMP 0, 3

; --- RDWAIT: wait for AP SWR acknowledge ---
; Call: JSR 3,RDWAIT (or JSR @prdwt, 0)
RDWAIT:
    STA 3, @rsp, 0             ; push return
    ISZ rsp, 0
    LDA 1, rdwtmo, 0
rdwlp:
    DIA 0, FPS
    LDA 2, k40000, 0          ; ackbit = 040000
    AND 0, 2
    MOV 2, 2, SNR
    JMP rdnoa
    ; ACK set — pop and return
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3
rdnoa:
    MOVL 0, 0, SNC            ; test HALTED bit
    JMP rdcnt
    JMP @paperr, 0            ; halted without ACK
rdcnt:
    INC 1, 1, SZR
    JMP rdwlp
    JMP @paperr, 0            ; timeout

; --- SENDER: send datum or APEX message ---
; AC0 != 0: single datum. AC0 == 0: 5-word APEX.
SENDER:
    STA 3, @rsp, 0
    ISZ rsp, 0
    MOV 0, 0, SNR
    JMP sndapx
    JSR @prdwt, 0
    DOA 0, FPS
    DOAP 0, FPS
    JMP sndpop                 ; pop and return
sndapx:
    JSR @prdwt, 0
    DOA 0, FPS
    DOAP 0, FPS
    LDA 1, cm4, 0
    LDA 2, pfpopt, 0
sndlp:
    JSR @prdwt, 0
    LDA 0, 0, 2
    DOA 0, FPS
    DOAP 0, FPS
    INC 2, 2
    INC 1, 1, SZR
    JMP sndlp
    SUB 0, 0
    INC 0, 0                  ; AC0 = 1
    STA 0, runfg, 0
sndpop:
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APIN: read register ---
; AC0=NUM(1-9). Returns AC0=value. Call: JSR 3,APIN
APIN:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain2
    DIAS 0, FPS
    JMP 0, 3
ain2:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain3
    DIA 0, FPS
    JMP 0, 3
ain3:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain4
    DIAC 0, FPS
    JMP 0, 3
ain4:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain5
    DIAP 0, FPS
    JMP 0, 3
ain5:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain6
    LDA 0, savhma, 0
    JMP 0, 3
ain6:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain7
    LDA 0, savwc, 0
    JMP 0, 3
ain7:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain8
    LDA 0, savctl, 0
    JMP 0, 3
ain8:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain9
    DIB 0, FPS
    JMP 0, 3
ain9:
    DIC 0, FPS
    JMP 0, 3

; --- APOUT: write register ---
; AC0=NUM(1-10), AC1=value. Call: JSR 3,APOUT
APOUT:
    STA 1, aoutv, 0
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot2
    LDA 0, aoutv, 0
    DOA 0, FPS
    STA 0, fpswr, 0
    JMP 0, 3
aot2:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot3
    LDA 0, aoutv, 0
    DOAS 0, FPS
    STA 0, fpfnr, 0
    JMP 0, 3
aot3:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot4
    JMP 0, 3                   ; LITES read-only
aot4:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot5
    LDA 0, aoutv, 0
    DOBC 0, FPS
    JMP 0, 3
aot5:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot6
    LDA 0, aoutv, 0
    DOBS 0, FPS
    STA 0, savhma, 0
    JMP 0, 3
aot6:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot7
    LDA 0, aoutv, 0
    DOB 0, FPS
    STA 0, savwc, 0
    JMP 0, 3
aot7:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot8
    LDA 0, aoutv, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    JMP 0, 3
aot8:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot9
    LDA 0, aoutv, 0
    DOC 0, FPS
    JMP 0, 3
aot9:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot10
    LDA 0, aoutv, 0
    DOCS 0, FPS
    JMP 0, 3
aot10:
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    STA 0, savctl, 0
    STA 0, fpswr, 0
    STA 0, fpfnr, 0
    STA 0, fplit, 0
    JMP 0, 3

; --- RUNDMA: start DMA ---
; AC0=host addr, AC1=APMA, AC2=WC. Store CTRL at rdmcl first.
RUNDMA:
    STA 3, @rsp, 0
    ISZ rsp, 0
    STA 0, rdmha, 0
    STA 1, rdmap, 0
    STA 2, rdmwc, 0
    JSR @papwd, 0
    LDA 0, rdmap, 0
    DOBC 0, FPS
    LDA 0, rdmwc, 0
    DOB 0, FPS
    STA 0, savwc, 0
    LDA 0, rdmha, 0
    DOBS 0, FPS
    STA 0, savhma, 0
    ; CTRL = caller | IHWC (DeMorgan OR)
    LDA 0, rdmcl, 0
    LDA 1, k04000, 0          ; IHWC
    COM 0, 0
    COM 1, 2
    AND 2, 0
    COM 0, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    ; Start DMA
    SUB 0, 0
    INC 0, 0                  ; AC0 = 1
    STA 0, dmafg, 0
    DOBP 0, FPS
    ; pop and return
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APWD: wait for DMA complete ---
APWD:
    STA 3, @rsp, 0
    ISZ rsp, 0
    LDA 0, dmafg, 0
    MOV 0, 0, SNR
    JMP awddn                  ; not active
awdlp:
    SKPDN FPS+1
    JMP awdlp
    NIOC FPS+1
    SUB 0, 0
    STA 0, dmafg, 0
awddn:
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- TSTDMA: test DMA. AC0=1(done) or 0(busy). ---
TSTDMA:
    LDA 0, dmafg, 0
    MOV 0, 0, SNR
    JMP tstd1
    SUB 0, 0
    JMP 0, 3
tstd1:
    SUB 0, 0
    INC 0, 0                  ; AC0 = 1
    JMP 0, 3

; --- TSTRUN: test AP halted. AC0=1(halted) or 0(running). ---
TSTRUN:
    DIA 0, FPS
    MOVL 0, 0, SNC
    JMP tstr1
    SUB 0, 0
    INC 0, 0
    JMP 0, 3
tstr1:
    SUB 0, 0
    JMP 0, 3

; --- WTRUN: wait for AP halt. AC0=error code. ---
WTRUN:
    STA 3, @rsp, 0
    ISZ rsp, 0
wrnlp:
    SKPDN FPS
    JMP wrnlp
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    DIAC 0, FPS
    STA 0, fplit, 0
    LDA 1, k00400, 0          ; parity bit
    AND 0, 1
    MOV 1, 1, SNR
    JMP wrn1
    SUB 0, 0
    INC 0, 0                  ; error 1 (parity)
    JMP wrnpop
wrn1:
    LDA 1, k00200, 0          ; stack overflow bit
    AND 0, 1
    MOV 1, 1, SNR
    JMP wrn2
    SUB 0, 0
    INC 0, 0
    INC 0, 0                  ; error 2 (stack)
    JMP wrnpop
wrn2:
    SUB 0, 0                  ; error 0 (ok)
wrnpop:
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APRSET: hardware reset ---
APRSET:
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    STA 0, savctl, 0
    STA 0, fpswr, 0
    STA 0, fpfnr, 0
    STA 0, fplit, 0
    STA 0, dmafg, 0
    ; Reset stack pointer
    LDA 1, prstk, 0
    STA 1, rsp, 0
    JMP 0, 3

; --- RUNAP: start AP execution ---
; AC0=PSA, AC1=FN command.
RUNAP:
    STA 3, @rsp, 0
    ISZ rsp, 0
    STA 1, rapcmd, 0
    DOA 0, FPS
    LDA 0, k01000, 0          ; DEP into PSA
    DOAS 0, FPS
    LDA 0, rapcmd, 0
    DOAS 0, FPS
    ; Enable IHHALT
    LDA 0, savctl, 0
    LDA 1, k10000, 0
    COM 0, 0
    COM 1, 2
    AND 2, 0
    COM 0, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    SUB 0, 0
    INC 0, 0
    STA 0, runfg, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APEXAM: examine AP register ---
; AC0=REGSEL(0-15), AC1=WORD(0-3). Returns AC0=value.
APEXAM:
    LDA 2, k02000, 0          ; EXAM
    ADD 0, 2
    MOVL 1, 1
    MOVL 1, 1
    MOVL 1, 1
    MOVL 1, 1
    ADD 1, 2
    MOV 2, 0
    DOAS 0, FPS
    DIAS 0, FPS
    JMP 0, 3

; --- SPLDGO: load s-pad and start ---
; AC0=list ptr, AC1=count, AC2=start addr.
SPLDGO:
    STA 3, @rsp, 0
    ISZ rsp, 0
    STA 0, spltmp, 0
    STA 1, splcnt, 0
    STA 2, splpsa, 0
    LDA 2, spltmp, 0
spllp:
    LDA 0, splcnt, 0
    MOV 0, 0, SZR
    JMP spldo
    JMP splrn
spldo:
    LDA 0, 0, 2
    DOA 0, FPS
    LDA 0, k01001, 0          ; DEP into SPD
    DOAS 0, FPS
    INC 2, 2
    LDA 0, splcnt, 0
    LDA 1, cm1, 0
    ADD 1, 0
    STA 0, splcnt, 0
    JMP spllp
splrn:
    LDA 0, splpsa, 0
    LDA 1, k40000, 0          ; FN START (040000)
    JSR @prunap, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- WTDMA: wait for DMA, return error ---
WTDMA:
    STA 3, @rsp, 0
    ISZ rsp, 0
    JSR @papwd, 0
    LDA 0, savctl, 0
    LDA 1, k00400, 0          ; DLATE bit (same as parity)
    AND 0, 1
    MOV 1, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APWR: wait for AP run, error handling ---
APWR:
    STA 3, @rsp, 0
    ISZ rsp, 0
    JSR @pwtrun, 0
    ; AC0 has error code from WTRUN
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APIENA: enable CTL5 interrupt ---
APIENA:
    LDA 0, savctl, 0
    LDA 1, k02000, 0          ; IHCB5 (= EXAM value, shared constant)
    COM 0, 0
    COM 1, 2
    AND 2, 0
    COM 0, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    JMP 0, 3

; --- APIDIS: disable CTL5 interrupt ---
APIDIS:
    LDA 0, savctl, 0
    LDA 1, k02000, 0
    COM 1, 1
    AND 1, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    JMP 0, 3

; --- APWI: wait for CTL5 interrupt ---
APWI:
apwilp:
    SKPDN FPS+2
    JMP apwilp
    NIOC FPS+2
    JMP 0, 3

; --- TSTINT: test CTL5 interrupt ---
; Returns AC0=1(set) or 0(clear).
TSTINT:
    SKPDN FPS+2
    JMP tsti0
    SUB 0, 0
    INC 0, 0
    JMP 0, 3
tsti0:
    SUB 0, 0
    JMP 0, 3

; --- APSUPV: set supervisor mode ---
; AC0=mode (0=off, nonzero=on)
APSUPV:
    STA 0, supvr, 0
    JMP 0, 3

; --- APASGN: assign FPS processor ---
; Returns AC0=1 (always succeeds, single device)
APASGN:
    STA 3, @rsp, 0
    ISZ rsp, 0
    JSR @preset, 0
    SUB 0, 0
    INC 0, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APRLSE: release FPS processor ---
APRLSE:
    STA 3, @rsp, 0
    ISZ rsp, 0
    JSR @papwd, 0
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    STA 0, dmafg, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- APSTOP: error stop ---
; AC0=error code. Stores and halts.
APSTOP:
    STA 0, ercode, 0
    HALT

; --- HPUT: send single datum ---
; AC0=datum.
HPUT:
    STA 3, @rsp, 0
    ISZ rsp, 0
    JSR @psndr, 0
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- HGET: wait for datum ---
; Returns AC0=datum.
HGET:
    STA 3, @rsp, 0
    ISZ rsp, 0
hgetlp:
    JSR @phtst, 0
    MOV 0, 0, SNR
    JMP hgetlp
    DSZ rsp, 0
    LDA 3, @rsp, 0
    JMP 0, 3

; --- HTST: test datum available ---
; Returns AC0=datum if found, 0 if not.
HTST:
    LDA 2, pfpdat, 0
    LDA 1, cm8, 0
htstlp:
    LDA 0, 0, 2
    MOV 0, 0, SNR
    JMP htstn
    ; Found: clear entry, return datum
    SUB 1, 1
    STA 1, 0, 2
    JMP 0, 3
htstn:
    INC 2, 2
    INC 1, 1, SZR
    JMP htstlp
    SUB 0, 0
    JMP 0, 3

; --- LOOKY: debug dump ---
; Returns AC0=FPSWR, AC1=RUNFG, AC2=FN status
; (AC3 used for return, CTRL available via savctl)
LOOKY:
    LDA 0, fpswr, 0
    LDA 1, runfg, 0
    DIA 2, FPS
    JMP 0, 3

; --- VIRP: debug interrupt status ---
; Returns AC0=SUPVR
VIRP:
    LDA 0, supvr, 0
    JMP 0, 3

; --- APERR: error handler ---
APERR:
    DIAC 0, FPS
    STA 0, fplit, 0
    SUB 0, 0
    STA 0, runfg, 0
    HALT

; --- Additional page-zero constant ---
    org 0116
prstk:
    dw rstk             ; pointer to stack base (for reset)

; end of dapex_dg.asm
