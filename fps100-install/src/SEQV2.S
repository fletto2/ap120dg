"****** SEQV2 = ASM100 TEST ROUTINE FOR GLOBAL TEST = REL 0.0, AUG 79
"
        $TITLE SEQV2
        $ENTRY SEQV2,0
"
"  --- ABSTRACT ---
"
"  THIS ROUTINE BUILDS AN INTEGER VECTOR OUT OF SEQUENTIAL NUMBERS.
"
"  DEFINE PARAMETERS
"
        SARRAY = 0              "STARTING ADDRESS FOR VECTOR
        R0     = 0              "DEFINE SPAD
"
SEQV2:  LDMA;DB=SARRAY+32.      "MA = LAST ELEMENT+1 OF SARRAY
        LDSPI R0;DB=32.         "R0 = 32.
"
LOOP:   MOV R0,R0;DECMA;MI<DB;  "WRITE R0 VALUE INTO SARRAY
        DB=SPFN                 "
        DEC R0                  "R0 = R0-1
        BNE LOOP                "IF NOT 0, CONTINUE LOOPING
"
        RETURN                  "DONE
"
        $END
