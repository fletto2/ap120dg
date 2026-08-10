"****** RTCISR = RTC INTERRUPT HANDLER = REL 1.0  , NOV 79 ********************
"
        $ISR 5.         "RTC
        $TITLE RTCISR
        $ENTRY RTCISR
        $EXT INSERT,DELETE
"
$NOLIST
$INSERT MINDEF
$LIST
"       RTC QUEUE DEFINITIONS
"
        $INTEGER RTCQ,RTCRQ
"
        $COMMON /RTCCOM/ RTCQ(2),RTCRQ(2)
"
"  DEFINE RTCTASK INTERNAL QUEUES
"
        $DATA   RTCQ (1) RTCQ "RT LINK OF QUEUE 1
        $DATA   RTCQ (2) RTCQ "LEFT LINK
"
        $DATA   RTCRQ (1) RTCRQ "RT LINK OF QUEUE 2
        $DATA   RTCRQ (2) RTCRQ "LEFT LINK
"
"
"   DEFINE PARAMETERS
"
        BITMSK = 001
        RATMSK = 017
        RUN    = 401
"
"
"  R0 = INTERRUPT BIT MASK
"
RTCISR: ION                     "ENABLE INTERRUPTS
        LDSPI R4;DB=RTCQ;       "GET RTC QUEUE ADDR
        LDMA                    "FETCH VALUE
        STATMA                  "WAIT FOR MD
        STATMA;MOV R0,R6        "SAVE R0 IN R6
"
        DPX(X3)<MD              "DPX(3) = ELEMENT TO BE DELETED
        JSR DELETE              "REMOVE FIRST MESSAGE FROM QUEUE
"
                                "R1 = ADDR OF NEXT MESSAGE IN QUEUE
"
        LDDA;DB=RTCCTL          "SETUP TO STOP RTC
        OUT;DB=ZERO             "STOP RTC
        LDDA;DB=RTCCTR          "SETUP TO FETCH COUNT
        LDSPI R5;IN;DB=INBS     "R5 = CURRENT COUNT
"
        SUB# R1,R4              "TEST FOR QUEUE EMPTY
        BNE START               "
        LDDA;DB=RTCCST          "SETUP DEVICE ADDR
        OUT;DB=ZERO             "CLEAR RTC COUNT
        JMP DONE                "YES, SEND ANSWER
"
START:  LDSPI R3;DB=3           "R3 = RTC TICK FIELD OFFSET
        LDDA;DB=RTCCST          "SETUP DEVICE ADDR
        ADD R1,R3;SETMA         "FETCH RTC TICK COUNT
        INCMA                   "FETCH DIRECTION
        INCMA                   "FETCH MODE
        OUT;DB=MD;INCMA         "SET TICKS, FETCH RATE
"
        LDSPI R1;DB=MD;STATMA   "R1 = DIRECTION
        LDSPI R2;DB=MD;STATMA   "R2 = MODE
        LDSPI R3;DB=MD          "R3 = RATE
        LDSPI R0;DB=BITMSK      "R0 = BIT MASK
"
        ANDL R0,R1              "MASK DIRECTION BIT
        AND R0,R2               "MASK MODE BIT
        LDSPI R0;DB=RATMSK      "R0 = RATE MASK
        AND R0,R3               "MASK RATE
        ORL R2,R1               "BUILD CONTROL VALUE
        MOVL R1,R1;INCMA        "MAKE ROOM FOR RATE
        MOVL R1,R1;STATMA       "FETCH REPEAT COUNT
        MOVL R1,R1;STATMA       "
        ORL R3,R1               "ADD IN RATE
        LDSPI R0;DB=RUN         "R0 = RUN BITS
        LDDA;DB=RTCCTL          "SETUP DEVICE ADDR
        OR R0,R1;OUT;DB=SPFN    "START CLOCK
        LDDA;DB=RTCCST          "SETUP DEVICE ADDR
        OUT;DB=MD               "SET REPEAT COUNT
"
        CLR R6                  "ENABLE NEXT INTERRUPT
"
"
DONE:   IOFF                    "DISABLE INTERRUPTS
        LDSPI R0;DB=DPX(X3)     "R0 = MESSAGE ADDRESS
"
        LDSPI R1;DB=2           "R1 = STATUS FIELD OFFSET
        ADD R1,R0;SETMA         "MA POINTS TO STATUS FIELD
        MOV R5,R5;STATMA;MI<DB; "SET STATUS WITH CURRENT COUNT
        DB=SPFN                 "
"
                                "R1 = RETURN QUEUE OFFSET
        ADD R4,R1;DPX(X2)<SPFN  "DPX(2) = RETURN QUEUE ADDRESS
        JSR INSERT              "RETURN BUFFER
        MOV R6,R0;RETURN        "RESTORE R0 AND RETURN
"
"
        $END
