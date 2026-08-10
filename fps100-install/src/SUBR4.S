"****** SUBR4 = FOR BASIC MECH MINI TEST 1 = REL 1.0  , NOV 79 ****************
"
$TITLE SUBR4
$ENTRY SUBR4,0
"
"
SUBR4:  RPSL COUNT; DPX<DB
        LDSPI 0; DB=DPX
        INC 0; DPX<SPFN
        LPSL COUNT; DB=DPX;
         RETURN
COUNT:  NOP
$END
