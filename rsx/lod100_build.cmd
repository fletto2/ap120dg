;
; Build LOD100 (the reconstruction) under its own overlay descriptor and
; run the flat DGNLIB+SYMLIB job.  $FOR2 -- note: no /-VA for LOD100.
;
SET /UIC=[200,200]
INS $MAC
INS $LBR
INS $TKB
REM FOR
INS $FOR/INC=44000
ASN DK2:=SY:
PIP LIB100.OLB=DK1:LIB100.OLB
FOR LOD100=LOD100/-I4/-SN
LBR LOD100/CR:1000:256:256
LBR LOD100/IN=LOD100
TKB @LOD100C
;
; LOD100 BUILT -- drive it with @file, the same extension LNK100 has.
;
INS LOD100.TSK/TASK=...LOD
LOD
;
; LOAD DONE
;
