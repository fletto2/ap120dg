.ENABLE SUBSTITUTION
.ENABLE GLOBAL
.SETS $MM "MT:"       .; no magtape on this system; TREAD is stubbed
.SETS $MM0 "MT0:"
.SETS $BPI "1"
.SETS $LBDSK "LB:"

.SETS $WKDSK "DM1:"   .; adapted: the package lives on the RK07
.SETS $LUIC "[1,1]"
.SETS $WUIC "[100,100]"
.SETN $BASLB 0
.SETN $SIG 0
.SETN $IPR 0
.SETN $AML 0
.SETN $PDS 0
.SETN $SUP10 0
.SETN $MIN10 0
 SET /BUF=TI:80.
.;
.; GET A TASK BUILDER...
.;
.IFINS TKB .GOTO 100
INS $BIGTKB/INC=10000/TASK=...TKB
.IFINS TKB .GOTO 100
INS $TKB/INC=10000/TASK=...TKB
.IFINS TKB .GOTO 100
; BIGTKB OR TKB CANNOT BE FOUND !!!  INSTALL ONE BEFORE RESUMING.
.PAUSE
.;
.; GET AN ASSEMBLER...
.;
.100: .IFINS MAC .GOTO 110
INS $BIGMAC/INC=10000/TASK=...MAC
.IFINS MAC .GOTO 110
INS $MAC/INC=10000/TASK=...MAC
.IFINS MAC .GOTO 110
; BIGMAC OR MAC CANNOT BE FOUND !!!  INSTALL ONE BEFORE RESUMING.
.PAUSE
.;
.; GET A FORTRAN COMPILER. F4P WILL BE USED IF INSTALLED.
.; FORCE RE-INSTALLATION WITH LOTS OF MEMORY
.;
.110: .IFINS F4P .GOTO 120
.IFINS FOR REM FOR
.; ADAPTED: 37000 was the value at the original site and is not enough
.; for ASM100 here -- the compile dies with DYNAMIC MEMORY OVERFLOW
.; partway through, and TKB then reports 'Module OPTAB not in library'.
.; The comment must sit on its OWN line: this one is passed to MCR
.; verbatim, and a trailing .; gives 'INS -- Syntax error'.
INS $FOR/INC=44000
.IFINS FOR  .GOTO 130
.120: .IFINS F4P  REM F4P
INS $F4P/INC=20000
.IFINS F4P  .GOTO 130
; F4P OR FOR CANNOT BE FOUND !!!  INSTALL ONE BEFORE RESUMING.
.PAUSE
.;
.; GET THE LIBRARIAN, PIP, AND AN EDITOR.
.; (EDT WILL BE USED IF IT IS INSTALLED)
.;
.130: .IFINS LBR .GOTO 150
INS $LBR/TASK=...LBR
.IFINS LBR .GOTO 150
; LBR CANNOT BE FOUND !!! INSTALL IT BEFORE RESUMING.
.PAUSE
.150: .IFINS PIP .GOTO 160
INS $PIP
.IFINS PIP .GOTO 160
; PIP CANNOT BE FOUND !!! INSTALL IT BEFORE RESUMING.
.PAUSE
.160: .IFINS EDI .GOTO 170
.IFINS EDT .GOTO 170
INS $EDI/INC=40000/TASK=...EDI
.170:
.;
.; SET UP THE SWITCHES FOR COMPILING.
.;
.SETS $F4P0 ""
.SETS $F4P2 "/CO:99./-TR/-I4"
.SETS $F4P1 $F4P2
.;
.SETS $FOR2 "/-I4/-SN"
.SETS $FOR1 $FOR2+"/-VA"
.;
.SETS $COM "N"   .; DO NOT SAVE FORTRAN COMMENTS ON MAGTAP READS.
.SETN $NOAP 1   .; ONE AP IS BEING CONNECTED.
.; ADAPTED: the original site had its system disk on DL0:.  Here the
.; system is on the RK07, so LB: must follow it -- otherwise LB: names
.; a device that does not exist and every MAC carrying LB:[1,1]EXEMC
.; fails with 'Open failure on input file', which MAC does not
.; attribute to LB:.  PIP probes run BEFORE this assignment succeed,
.; which is what made it look like a privilege difference.
ASN DM0:=LB:
.IFNLOA MT:  LOA MT:
.; ADAPTED: the tape has 'ASN DL1:=SY:' -- DL1: was the site's WORK
.; disk -- so SY: must follow the work disk, which here is DM1:.
.; DM0: is the SYSTEM pack and is what LB: follows, above.
.;
.; THE COMMENT MUST BE ON ITS OWN LINE.  A trailing '.;' is NOT
.; stripped from a command line: 'ASN DM0:=SY:   .; ...' gave
.; 'ASN -- Syntax error', so the assignment never took and SY: kept
.; whatever it already held.  The install had been relying on that
.; by accident, and with SY: left on the system pack every
.; unqualified 'FOR ASM100=ASM100' would resolve on the wrong device.
ASN DM1:=SY:
SET /UIC=[100,100]
;
; *** THE LAST NUMBER IN THE RESPONSE HERE SHOULD BE AT LEAST 400.
SET /POOL
; *** (IF NOT, MAY DIE.)
; END SETUP
.EXIT
