; LOD10.CMD - INSTALL LOD100 COMMAND FILE
; RSX11M FPS100 FEB 80
; LOD100.FTN
; LIB100 MUST BE BUILT AND IN PLACE
;
 .ENABLE GLOBAL
 .ENABLE SUBSTITUTION
 .IFDF $MAST .GOTO 10
; SETUP
 @SETUP
;
 .10:
;
; COMPILE LOD100
;
 .IFINS FOR FOR LOD100=LOD100'$FOR2'
 .IFINS F4P F4P LOD100=LOD100'$F4P2'
;
; CREATE LOD100 LIBRARY
;
 LBR LOD100/CR=LOD100
;
; TASK BUILD LOD100
;
    .OPEN  LOD100.CMD
   .DATA  LOD100/CP,LOD100=LOD100/MP
   .DATA UNITS=17
   .DATA ACTFIL=8
   .DATA //
   .CLOSE
;
; ADAPTED.  The original generates FPS's own overlay descriptor here,
; naming THEIR module decomposition (APLDBD, LMSRC2, RDREC, OUTSCN,
; LOAD1, SRCN, APMDIO, ...).  The reconstruction has a different set of
; program units, so its own LOD100.ODL is used instead.  Everything
; else in this file -- including UNITS=17 and ACTFIL=8 -- is verbatim
; from INSTAL.TXT section 9.14.
;
 TKB @LOD100
 PIP LOD100.TSK/PU
;
; DELETE INTERMEDIATE FILES
;
 PIP LOD100.OLB;*,LOD100.OBJ;*,LOD100.CMD;*,LOD100.ODL;*/DE
 .EXIT
