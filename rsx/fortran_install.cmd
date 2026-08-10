;
; Install FORTRAN IV V2.2 on the generated RSX-11M V4.0 system, copying
; straight from the DEC distribution volume mounted on DL3:.
;
INS $PIP
INS $TKB
INS $LBR
PIP [1,24]/NV=DL3:[11,41]*.*
PIP [1,24]/NV=DL3:[11,42]*.*
SET /UIC=[1,24]
TKB @[1,24]FOR11M.CMD
;
; FORTRAN INSTALLED
;
