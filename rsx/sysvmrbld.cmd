; Phase II for an RK07-resident system.
;
; SYSGEN2.CMD line 252 is "ASN SY:=LB:" -- SYSGEN builds onto SY:, and
; there is no target-disk question.  So point BOTH SY: and LB: at the
; RK07 and run VMR against the FRESH Executive task image.  The earlier
; attempt failed because VMR opened the already-built RSX11M.SYS that
; was copied over, and SYSVMR cannot configure an image twice
; ("Partition already exists").  Delete it and let VMR rebuild it from
; RSX11M.TSK, which is what Phase II does.
;
INS $PIP
INS $VMR
MOU DM0:RSXBIG
SET /UIC=[1,54]
PIP DM0:[1,54]RSX11M.SYS;*/DE
; SYSGEN2.CMD line 499 builds the system image as a CONTIGUOUS copy of
; the Executive task image with an explicit allocation:
;   PIP RSX11M.SYS/CO/NV/BL:nnn.=RSX11M.TSK
; and line 481 sets that allocation to 258. blocks for a mapped system.
; VMR configures an existing .SYS -- it does not create one, which is
; why deleting the copy alone gave 'Open failure on file RSX11M.SYS'.
PIP DM0:[1,54]RSX11M.SYS/CO/NV/BL:258.=DM0:[1,54]RSX11M.TSK
ASN DM0:=LB:
ASN DM0:=SY:
VMR @DM0:[1,54]SYSVMR
;
; VMRBLD DONE
;
