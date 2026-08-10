;
; Build ASM100 (the ORIGINAL, from the tape) against a LIB100 carrying
; the reconstructed FDUTIL.  Run as "@DK1:BUILD".
;
; V3.1's STARTUP installs only $EDI, $PIP and $FOR, so MAC, LBR and TKB
; must be installed or every one of them reports TASK NOT IN SYSTEM.
;
INS $MAC
INS $LBR
INS $TKB
;
; The compiler needs more dynamic memory or it reports DYNAMIC MEMORY
; OVERFLOW and suppresses the real diagnostics behind it (FIRST.CMD).
;
REM FOR
INS $FOR/INC=44000
;
; Build on DK1:, not the system pack -- the 4800-block pack has RSX on it
; and runs out mid-compile ("ERROR WRITING OBJECT FILE").  Redirect SY:
; and leave LB: alone: ASN DK1:=LB: would break INS, which looks in LB:.
;
SET /UIC=[200,200]
ASN DK1:=SY:
;
FOR ASM100=ASM100/-I4/-SN/-VA
FOR IUTIL=IUTIL/-I4/-SN/-VA
FOR FDUTIL=FDUTIL/-I4/-SN/-VA
MAC ADUTIL=ADUTIL
LBR LIB100/CR:1000:256:256
LBR LIB100/IN=IUTIL,FDUTIL,ADUTIL
LBR ASM100/CR:1000:256:256
LBR ASM100/IN=ASM100
TKB @ASM100
;
; BUILD COMPLETE -- now assemble a source that shipped on the tape and
; compare the object with the one that shipped beside it.
; ASM100 prompts: SOURCE FILE= / OBJECT FILE= / LIST AND ERROR FILE= /
; LISTING? (Y/N)   (from ASM100.FTN lines 900, 975, 1100, 1300)
;
RUN ASM100
;
; ASSEMBLY DONE
;
