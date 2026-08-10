;
; Build LNK100 (the reconstruction) against the LIB100 already on DK1:,
; then link the DGNOBJ.APO this pipeline assembled.
;
SET /UIC=[200,200]
INS $MAC
INS $LBR
INS $TKB
REM FOR
INS $FOR/INC=44000
ASN DK2:=SY:
PIP LIB100.OLB=DK1:LIB100.OLB
PIP DGNOBJ.APO=DK1:DGNOBJ.APO
FOR LNK100=LNK100/-I4/-SN/-VA
TKB @LNK100
;
; LNK100 BUILT -- install it and use the command line, which avoids the
; two-line console dialogue entirely (APEEL is driven the same way).
;
INS LNK100.TSK/TASK=...LNK
LNK DGNLNK.LM=DGNOBJ.APO
;
; LINK DONE
;
