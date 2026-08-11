;
; REINSTALL_TOOLS.CMD -- refresh FDUTIL on the work pack and rebuild
; LIB100 and every PDS tool against it, using FPS's own command files.
;
; WHY THIS EXISTS.  FDUTIL has FOUR copies, not the three the notes long
; recorded:
;
;   1  ap120dg/reconstructed/FDUTIL.FTN        the source
;   2  ap120dg/fps100-install/src/FDUTIL.FTN   the package (make_package.py)
;   3  LB:[1,1]LIB100.OLB                      the installed object
;   4  DM1:[100,100]FDUTIL.FTN                 THE WORK PACK'S OWN SOURCE
;
; and beyond those, every built .TSK links FDUTIL STATICALLY.  The pack's
; copy was once 451 lines against the source's 752, so a "faithful
; install re-run" rebuilt every tool from a stale source and the tools
; silently lacked INFILE's .DAT default extension -- which shows up only
; as ERROR 29, NO SUCH FILE on any source using $INSERT.
;
; Run with the current FDUTIL.FTN on a transfer volume in [200,200].
;
; INS $PIP FIRST.  PIP is NOT installed on a fresh boot, and "PIP -- Task
; not in system" contains no ERROR/FATAL/OPEN FAILURE, so a log grep
; passes it and the rebuild proceeds against the OLD source with zero
; errors reported.
;
INS $PIP
SET /UIC=[100,100]
PIP DM1:[100,100]FDUTIL.FTN/NV=DL1:[200,200]FDUTIL.FTN
PIP DM1:[100,100]SETUP.CMD/NV=DL1:[200,200]SETUP.CMD
;
; Confirm the transfer: the new file must appear as a HIGHER VERSION and
; a bigger block count than the one already there.  FORTRAN compiles the
; highest version.
;
PIP DM1:[100,100]FDUTIL.FTN;*/LI
;
; SY: must follow the WORK disk.  SETUP does this too, but only after
; its own copy is corrected -- see fps_setup_adapted.cmd.
;
ASN DM1:=SY:
@DM1:[100,100]LIB100
@DM1:[100,100]PDS100
;
; REINSTALL DONE
;
; Verify by assembling a source that uses $INSERT, with ONLY the .DAT
; file present (no bare-name copy):
;    RUN DM1:[100,100]ASM100   ->  TABLES.S / TAB.APO / TAB.LST / N
; It must report "0 ERROR(S)" and "ASSEMBLY COMPLETED".
;
