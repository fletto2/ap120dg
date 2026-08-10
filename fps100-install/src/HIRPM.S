"/****** HIRPM = HOST INTERRUPT SVC (RTS100) = REL 1.0  , NOV 79 **************
"
"               CHANGED  79-AUG-30    13:15
"
"       FOR USE WITH FPS-100 SUPERVISOR
"         JOSEPH E. RAMUS        MAY 79
"
"       TAB STOP SETTINGS FOR EDITOR:    9   33  60
"
"         SPAD REGISTER NAMES DEFINED IN MINDEF
"           R0 R1 R2 R3 R4 R5 R6 R7
"
"         INDEXES FOR DATA PAD X DEFINED IN MINDEF
"           X0 X1 X2 X3
"
"       VDATM    IS STORAGE FOR DATUM VALUES
"
$ISR 7
$TITLE  HIRP
$ENTRY  HIRP,0
$EXT WATSWR
"
"             $INSERT MINDEF
$NOLIST
$INSERT MINDEF
$LIST
"
"
$INTEGER  VDATM
$COMMON   /FHOSTC/  VDATM(7)
"
$DATA  VDATM(1.)  0
$DATA  VDATM(2.)  0
$DATA  VDATM(3.)  0
$DATA  VDATM(4.)  0
$DATA  VDATM(5.)  0
$DATA  VDATM(6.)  0
$DATA  VDATM(7.)  0
"
"
"
"
"
"/****** HIRP = HOST INTERRUPT SERVICE ROUTINE = REL 1.0  , NOV 79 ************
"
"         HOST INTERRUPT SERVICE ROUTINE
"
"           THIS ROUTINE IS CALLED WHEN AN INTERRUPT IS
"             RECEIVED FROM THE HOST.
"
"         NOTE:  CLEAR R0 WHEN RETURNING TO RE-ENABLE THE HOST IRP.
"
HIRP:   ION                     "ENABLE INTERRUPTS
        JSR APXMT               "READ SWR
        MOV R1,R0
"/****** DATUM = PROCESS DATUM VALUE FROM HOST = REL 1.0  , NOV 79 ************
"         R0 & R1 HAVE DATUM VALUE
"         DPX(X1) ALSO HAS DATUM VALUE
DATUM:  LDSPI R2; DB=7          "MASK FOR INDEX FIELD
        AND R2,R0               "LEAVE 3 BIT INDEX
        LDSPI R3; DB=VDATM-1      "SET BASE ADDRESS
         IOFF                   "TURN OFF IRPS
        ADD R3,R0; SETMA;       "ADD OFFSET,
          MI<DPX(X1)              "STORE NEW DATUM
"                  PROVIDE TIME FOR MEMORY TO CYCLE
        CLR R0                  "TO RE-ENABLE HOST IRP
        RETURN                  "BACK TO SUPERVISOR
"
"
"/****** APXMT = GET VALUE FROM HOST INTERFACE = REL 1.0  , NOV 79 ************
"
"       REGISTER USAGE:
"         R0  DATA MANIPULATION
"         R1  RETURNS 16 BIT VALUE
"         R2  NOT USED
"         R3 R4 R5 R6 R7 ARE NOT CHANGED
"         X0  NOT USED
"         X1  16 BIT VALUE
"         X2  NOT USED
"         X3  NOT USED
"
"       ALGORITHM:
"       1.  WAIT FOR HOST TO WRITE SWR
"       2.  READ SWR
"       3.  PUT VALUE IN R1 & DPX(X1)
"       4.  RETURN
"
"
APXMT:  JSR WATSWR              "WAIT FOR HOST TO WRITE SWR
        SWDB;                   "READ SWR TO DB
          DPX(X1)<DB               "THEN TO DPX
        DB=DPX(X1);
          LDSPI R1;             "R1 GETS VALUE FROM SWR
          RETURN                   "SWR VALUE IN R1 & DPX(X1)
"
$END
