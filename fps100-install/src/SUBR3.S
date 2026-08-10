"****** SUBR3 = FOR BASIC MECH MINI TEST 1 = REL 1.0  , NOV 79 ****************
"
$TITLE SUBR3
$ENTRY SUBR3,2
"
"
SUBR3:  LDMA; DB=17700
        INCMA; MOV 0,0; MI<SPFN
        INCMA; MOV 1,1; MI<SPFN
        INCMA; ADD 0,1; MI<SPFN;
         RETURN
$END
