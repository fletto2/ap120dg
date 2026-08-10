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
;
; The system pack was migrated from a disk the install had already run
; against, so it carries that run's products.  DRV100 does
;   .OPEN LB:[1,2]UPAP.CMD;1
; at an EXPLICIT version, which fails with "Data file error, Code -16"
; when the file is already there -- and that reads as a privilege
; problem, not a leftover.  Clear the install's own outputs from the
; system disk for the same reason the work UIC is cleared.
;
SET /UIC=[1,2]
PIP LB:[1,2]UPAP.CMD;*/DE
SET /UIC=[1,1]
PIP LB:[1,1]APDEV.TSK;*,APDEV.STB;*/DE
SET /UIC=[1,54]
PIP LB:[1,54]APDRV.TSK;*,APDRV.STB;*/DE
SET /UIC=[100,100]
MOU DM1:USAGI0
SET /UIC=[100,100]
UFD DM1:[100,100]
;
; Clear the work area first.  Re-running over a previous install
; leaves FPSMC.MAC behind, and DRV100's .OPEN of it then fails
; with 'Data file error, Code -16'.
;
PIP DM1:[100,100]*.*;*/DE
PIP DM1:[100,100]/NV=DM1:[200,200]*.*
PIP DM1:[100,100]/NV=DL2:[200,200]SETUP.CMD
PIP DM1:[100,100]/NV=DL2:[200,200]TREAD.CMD
;
; LIB100.CMD is one of the nine files missing from the tape, but
; INSTAL.TXT section 9.6 reproduces it VERBATIM -- as 9.13 and 9.14
; do for LNK10 and LOD10.  It is recovered, not invented.
; FDUTIL.FTN is also missing (LIB100.CMD itself deletes it); the
; validated reconstruction stands in.
;
;
; PDS100 needs LNK10.CMD and LOD10.CMD -- two more of the nine missing
; files, both reproduced verbatim by INSTAL.TXT 9.13 and 9.14 -- and the
; LNK100.FTN / LOD100.FTN sources, which are genuinely gone.  The
; reconstructions stand in.  LOD100.ODL is the reconstruction's own.
;
SET /UIC=[100,100]
PIP LB:[1,1]*.*/LI/TB
;
; DRV100.CMD line 103 assembles the device table against
;   LB:[1,1]EXEMC/ML,[11,10]RSXMC/PA:1
; and [11,10]RSXMC carries NO device prefix, so it resolves on SY: --
; the work disk -- while [11,10] is a system UIC.  At the original site
; SY: was DL1:, their work disk, so RSXMC must have been there too.
; Reproduce that layout rather than edit FPS's command file: give the
; work volume a [11,10] holding RSXMC.
;
SET /UIC=[11,10]
UFD DM1:[11,10]
PIP DM1:[11,10]RSXMC.MAC=LB:[11,10]RSXMC.MAC
SET /UIC=[100,100]
ASN DM1:=SY:
PIP LB:[1,1]*.*/LI/TB
;
;
; INSTALL AP DRIVER -- FPS's own DRV100.CMD
;
;
@DRV100
;
; DRIVER STEP DONE
;
;
; $LBDSK is now DM0:, so the library UIC [1,1] must exist there.
; A UFD must be OWNED by the UIC it serves, so create it under [1,1].
;
PIP LB:/FR
PIP DM1:/FR
;
; INSTALL HSR LIBRARY (MATHLIB) -- FPS's own HSR100.CMD
;
@HSR100
;
; HSR STEP DONE
;
; INSTALL LIB100 -- recovered LIB100.CMD, which calls the tape's own
; APX10.CMD and UTL10.CMD.  MASTER.CMD runs this before APL100.
;
@LIB100
;
; LIB STEP DONE
;
; The PDS command files task-build against LB:'$LUIC'LIB100/LB, a
; hardcoded path.  $LBDSK is the RK07 here because the RL02 system disk
; cannot hold MATHLIB and APLIB, so LIB100 has to be copied to LB: as
; well or every TKB dies with "Lookup failure on file LIB100.OLB".
;
;
; INSTALL PDS -- the tape's own PDS100.CMD.  Builds APCOM into LIB100,
; then ASM100, SIM100, DBG100, LNK100, LOD100, LED100, VFC100.
;
@PDS100
;
; PDS STEP DONE
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
