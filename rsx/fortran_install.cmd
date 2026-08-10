;
; Complete the FORTRAN install: the FORTRAN IV V2.2 RK05 kit does NOT ship
; the virtual-array module $VINIT, which defines $VIRIN.  Without it NO
; FORTRAN program links on a freshly generated V4.0 system.  Taken from
; the V3.1 pack's SYSLIB, where FORTRAN works.
;
INS $PIP
INS $TKB
INS $LBR
PIP [1,24]/NV=DL3:[11,41]*.*
PIP [1,24]/NV=DL3:[11,42]*.*
SET /UIC=[1,24]
TKB @[1,24]FOR11M.CMD
LBR LB:[1,1]SYSLIB/IN=[1,24]FOROTS.OBJ
LBR LB:[1,1]SYSLIB/IN=[1,24]FOREIS.OBJ
PIP [1,24]VINIT.OBJ=DL2:[200,200]VINIT.OBJ
LBR LB:[1,1]SYSLIB/IN=[1,24]VINIT.OBJ
;
SET /UIC=[200,200]
INS $FOR
PIP HELLO.FTN=DL2:[200,200]HELLO.FTN
FOR HELLO,HELLO=HELLO/-I4/-SN/-VA
TKB HELLO=HELLO
;
; FORTRAN COMPLETE
;
