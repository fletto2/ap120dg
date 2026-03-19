; DAPEX_DG.ASM -- FPS AP-120B / FPS-100 Host Driver for Data General Nova
;
; Port of DAPEX.MAC (PDP-11 RSX-11M) to DG Nova assembly.
; Register mapping from 280B schematic 512-3280-004 Rev B.
;
; DG Nova addressing: LDA/STA use 8-bit signed displacement from
; page zero (mode 0) or PC (mode 1). All scratch/constants on page zero.
;
; Assembled with dgasm: dgasm/build/dgasm -o dapex_dg.bin dapex_dg.asm

    dev FPS = 055

; ============================================================
; Page-zero variables and constants (000-077)
; ============================================================

    org 000

; --- Saved return addresses ---
rdwret:
    dw 0
sndret:
    dw 0
ainret:
    dw 0
aotret:
    dw 0
rdmret:
    dw 0
awdret:
    dw 0
wrnret:
    dw 0
arsret:
    dw 0
rapret:
    dw 0
exmret:
    dw 0

; --- State variables ---
runfg:
    dw 0
savctl:
    dw 0
fpswr:
    dw 0
fpfnr:
    dw 0
fplit:
    dw 0
dmafg:
    dw 0
savhma:
    dw 0
savwc:
    dw 0

; --- APEX message block ---
fpopt:
    dw 0
fpsct:
    dw 0
fpsw2:
    dw 0
fpfn2:
    dw 0

; --- RUNDMA temporaries ---
rdmha:
    dw 0
rdmap:
    dw 0
rdmwc:
    dw 0
rdmcl:
    dw 0

; --- Scratch ---
aoutv:
    dw 0
rapcmd:
    dw 0

; --- Constants ---
c1:
    dw 1
cm1:
    dw -1
cm4:
    dw -4
cm9:
    dw -9

    org 040

cm10:
    dw -10
ackbit:
    dw 040000
rdwtmo:
    dw -32768
cihwc:
    dw 004000
cihhlt:
    dw 010000
cdepps:
    dw 001000
cexam:
    dw 002000
cpar:
    dw 000400
cstk:
    dw 000200
c2:
    dw 2
pfpopt:
    dw fpopt
; --- Subroutine address pointers (for indirect JSR/JMP) ---
prdwt:
    dw RDWAIT
papwd:
    dw APWD
paperr:
    dw APERR

; ============================================================
; Code at 0200
; ============================================================

    org 0200

; --- RDWAIT: wait for AP SWR acknowledge ---
; Call: JSR 3,RDWAIT
RDWAIT:
    STA 3, rdwret, 0
    LDA 1, rdwtmo, 0
rdwlp:
    DIA 0, FPS
    LDA 2, ackbit, 0
    AND 0, 2
    MOV 2, 2, SNR
    JMP rdnoa
    JMP @rdwret, 0
rdnoa:
    MOVL 0, 0, SNC
    JMP rdcnt
    JMP @paperr, 0
rdcnt:
    INC 1, 1, SZR
    JMP rdwlp
    JMP @paperr, 0

; --- SENDER: send datum or APEX message ---
; AC0 != 0: single datum. AC0 == 0: 5-word APEX.
; Call: JSR 3,SENDER
SENDER:
    STA 3, sndret, 0
    MOV 0, 0, SNR
    JMP sndapx
    JSR @prdwt, 0
    DOA 0, FPS
    DOAP 0, FPS
    JMP @sndret, 0
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
    LDA 0, c1, 0
    STA 0, runfg, 0
    JMP @sndret, 0

; --- APIN: read register ---
; AC0=NUM(1-9). Returns AC0=value. Call: JSR 3,APIN
APIN:
    STA 3, ainret, 0
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain2
    DIAS 0, FPS
    JMP @ainret, 0
ain2:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain3
    DIA 0, FPS
    JMP @ainret, 0
ain3:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain4
    DIAC 0, FPS
    JMP @ainret, 0
ain4:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain5
    DIAP 0, FPS
    JMP @ainret, 0
ain5:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain6
    LDA 0, savhma, 0
    JMP @ainret, 0
ain6:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain7
    LDA 0, savwc, 0
    JMP @ainret, 0
ain7:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain8
    LDA 0, savctl, 0
    JMP @ainret, 0
ain8:
    LDA 1, cm1, 0
    ADD 1, 0
    MOV 0, 0, SZR
    JMP ain9
    DIB 0, FPS
    JMP @ainret, 0
ain9:
    DIC 0, FPS
    JMP @ainret, 0

; --- APOUT: write register ---
; AC0=NUM(1-10), AC1=value. Call: JSR 3,APOUT
APOUT:
    STA 3, aotret, 0
    STA 1, aoutv, 0
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot2
    LDA 0, aoutv, 0
    DOA 0, FPS
    STA 0, fpswr, 0
    JMP @aotret, 0
aot2:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot3
    LDA 0, aoutv, 0
    DOAS 0, FPS
    STA 0, fpfnr, 0
    JMP @aotret, 0
aot3:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot4
    JMP @aotret, 0
aot4:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot5
    LDA 0, aoutv, 0
    DOBC 0, FPS
    JMP @aotret, 0
aot5:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot6
    LDA 0, aoutv, 0
    DOBS 0, FPS
    STA 0, savhma, 0
    JMP @aotret, 0
aot6:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot7
    LDA 0, aoutv, 0
    DOB 0, FPS
    STA 0, savwc, 0
    JMP @aotret, 0
aot7:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot8
    LDA 0, aoutv, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    JMP @aotret, 0
aot8:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot9
    LDA 0, aoutv, 0
    DOC 0, FPS
    JMP @aotret, 0
aot9:
    LDA 2, cm1, 0
    ADD 2, 0
    MOV 0, 0, SZR
    JMP aot10
    LDA 0, aoutv, 0
    DOCS 0, FPS
    JMP @aotret, 0
aot10:
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    STA 0, savctl, 0
    STA 0, fpswr, 0
    STA 0, fpfnr, 0
    STA 0, fplit, 0
    JMP @aotret, 0

; --- RUNDMA: start DMA ---
; AC0=host addr, AC1=APMA, AC2=WC. Store CTRL at rdmcl first.
; Call: JSR 3,RUNDMA
RUNDMA:
    STA 3, rdmret, 0
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
    LDA 1, cihwc, 0
    COM 0, 0
    COM 1, 2
    AND 2, 0
    COM 0, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    ; Start DMA
    LDA 0, c1, 0
    STA 0, dmafg, 0
    DOBP 0, FPS
    JMP @rdmret, 0

; --- APWD: wait for DMA complete ---
; Call: JSR 3,APWD
APWD:
    STA 3, awdret, 0
    LDA 0, dmafg, 0
    MOV 0, 0, SNR
    JMP @awdret, 0
awdlp:
    SKPDN FPS+1
    JMP awdlp
    NIOC FPS+1
    SUB 0, 0
    STA 0, dmafg, 0
    JMP @awdret, 0

; --- TSTDMA: test DMA. AC0=1(done) or 0(busy). ---
TSTDMA:
    LDA 0, dmafg, 0
    MOV 0, 0, SNR
    JMP tstd1
    SUB 0, 0
    JMP 0, 3
tstd1:
    LDA 0, c1, 0
    JMP 0, 3

; --- TSTRUN: test AP halted. AC0=1(halted) or 0(running). ---
TSTRUN:
    DIA 0, FPS
    MOVL 0, 0, SNC
    JMP tstr1
    LDA 0, c1, 0
    JMP 0, 3
tstr1:
    SUB 0, 0
    JMP 0, 3

; --- WTRUN: wait for AP halt. AC0=error code. ---
; Call: JSR 3,WTRUN
WTRUN:
    STA 3, wrnret, 0
wrnlp:
    SKPDN FPS
    JMP wrnlp
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    DIAC 0, FPS
    STA 0, fplit, 0
    LDA 1, cpar, 0
    AND 0, 1
    MOV 1, 1, SNR
    JMP wrn1
    LDA 0, c1, 0
    JMP @wrnret, 0
wrn1:
    LDA 1, cstk, 0
    AND 0, 1
    MOV 1, 1, SNR
    JMP wrn2
    LDA 0, c2, 0
    JMP @wrnret, 0
wrn2:
    SUB 0, 0
    JMP @wrnret, 0

; --- APRSET: hardware reset ---
; Call: JSR 3,APRSET
APRSET:
    STA 3, arsret, 0
    NIOC FPS
    SUB 0, 0
    STA 0, runfg, 0
    STA 0, savctl, 0
    STA 0, fpswr, 0
    STA 0, fpfnr, 0
    STA 0, fplit, 0
    STA 0, dmafg, 0
    JMP @arsret, 0

; --- RUNAP: start AP execution ---
; AC0=PSA, AC1=FN command. Call: JSR 3,RUNAP
RUNAP:
    STA 3, rapret, 0
    STA 1, rapcmd, 0
    DOA 0, FPS
    LDA 0, cdepps, 0
    DOAS 0, FPS
    LDA 0, rapcmd, 0
    DOAS 0, FPS
    ; Enable IHHALT (DeMorgan OR)
    LDA 0, savctl, 0
    LDA 1, cihhlt, 0
    COM 0, 0
    COM 1, 2
    AND 2, 0
    COM 0, 0
    DOAC 0, FPS
    STA 0, savctl, 0
    LDA 0, c1, 0
    STA 0, runfg, 0
    JMP @rapret, 0

; --- APEXAM: examine AP register ---
; AC0=REGSEL(0-15), AC1=WORD(0-3). Returns AC0=value.
; Call: JSR 3,APEXAM
APEXAM:
    STA 3, exmret, 0
    LDA 2, cexam, 0
    ADD 0, 2
    MOVL 1, 1
    MOVL 1, 1
    MOVL 1, 1
    MOVL 1, 1
    ADD 1, 2
    MOV 2, 0
    DOAS 0, FPS
    DIAS 0, FPS
    JMP @exmret, 0

; --- APERR: error handler ---
APERR:
    DIAC 0, FPS
    STA 0, fplit, 0
    SUB 0, 0
    STA 0, runfg, 0
    HALT

; end of dapex_dg.asm
