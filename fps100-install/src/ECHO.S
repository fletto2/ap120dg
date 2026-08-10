"****** ECHO = PROGRAM TO TEST THE HOST INTERFACE ROUTINES = REL 1.0, MAY 79
"
        $TASK 1
        $TITLE ECHO
        $ENTRY ECHO
        $EXT FPUT,FGET,FTST,SENDER
"
"
"  LOCAL VARIABLES
"
        R0    $EQU 0            "
        R1    $EQU 1            "
        R2    $EQU 2            "
        R3    $EQU 3            "
        R4    $EQU 4            "
        R5    $EQU 5            "
        X0    $EQU 0            "
        X1    $EQU 1            "
"
        ONE     = 1             "
"
ECHO:   LDSPI R1;DB=ONE         "R1 = 1, WAIT FOR MESSAGE(1)
        JSR FGET                "WAIT FOR MESSAGE
"
        MOV R2,R2               "TEST FOR VALID MESSAGE
        BEQ CONT                "YES, THEN CONTINUE
"
" ERROR!
"
        HALT                    "STOP ON ERROR
"
CONT:   CLR R1                  "R1 = 0, SET FOR ANY MESSAGE
        JSR FTST                "GET ANY MESSAGE AVAILABLE
"
        MOV R2,R2               "TEST FOR VALID MESSAGE
        BNE CONT                "NO, THEN KEEP LOOKING
"
"  VALID MESSAGE, SO ECHO IT
"
        MOV R3,R2               "R2 = DATUM
        JSR FPUT                "ECHO DATUM BACK TO THE SAME EXCHANGE
        DPX(1)<DPX
        DPX<ZERO;
         JSR SENDER             "TEST OTHER PATH TOO
        BR CONT                 "CONTINUE LOOPING
"
"
        $END
