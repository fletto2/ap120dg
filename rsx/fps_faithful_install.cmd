;
; Faithful FPS installation, using FPS's own command files.
;
INS $PIP
INS $MAC
INS $LBR
INS $TKB
REM FOR
INS $FOR/INC=44000
;
; The install expects the sources in the work UIC [100,100].
;
MOU DM0:USAGI0
SET /UIC=[100,100]
UFD DM0:[100,100]
PIP DM0:[100,100]/NV=DM0:[200,200]*.*
PIP DM0:[100,100]/NV=DL2:[200,200]SETUP.CMD
PIP DM0:[100,100]/NV=DL2:[200,200]TREAD.CMD
PIP DM0:[100,100]DEVTABLE.MAC=DL2:[200,200]DEVTABLE.MAC
SET /UIC=[100,100]
ASN DM0:=SY:
;
; INSTALL AP DRIVER -- FPS's own DRV100.CMD
;
@DRV100
;
; DRIVER STEP DONE
;
;
; $LBDSK is now DM0:, so the library UIC [1,1] must exist there.
; A UFD must be OWNED by the UIC it serves, so create it under [1,1].
;
SET /UIC=[1,1]
UFD DM0:[1,1]
SET /UIC=[100,100]
PIP LB:/FR
PIP DM0:/FR
;
; INSTALL HSR LIBRARY (MATHLIB) -- FPS's own HSR100.CMD
;
@HSR100
;
; HSR STEP DONE
;
; INSTALL AP LIBRARY (APLIB) -- FPS's own APL100.CMD.
; Needs APEEL, which HSR100 built and installed as ...APE.
; LIB100 and PDS100 are skipped: LIB100.CMD is one of the nine files
; missing from the tape, and PDS100 needs it.
;
@APL100
;
; APL STEP DONE
;
