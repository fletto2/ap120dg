"
"****** RTCDUM = DUMMY DATA SECTION FOR RTCTEST = REL 1.0  , NOV 79 ***********
"
        $TITLE RTCDUM
"
"
"   DEFINE TIME-INTERVAL MESSAGES
"
        $INTEGER  MSG1,MSG2,MSG3
"
        $COMMON /TESTC/ MSG1(10.),MSG2(10.),MSG3(10.)
"
"   DEFINE MESSAGES
"
        $DATA  MSG1 (1.)  1       "MESSAGE NUMBER
        $DATA  MSG1 (2.)  0       "MESSAGE COUNT
        $DATA  MSG1 (3.)  MSG1+2  "RLINK
        $DATA  MSG1 (4.)  MSG1+2  "LLINK
        $DATA  MSG1 (5.)  0       "STATUS
        $DATA  MSG1 (6.)  100.    "TICK COUNT
        $DATA  MSG1 (7.)  0       "COUNT DOWN
        $DATA  MSG1 (8.)  1       "REPEAT
        $DATA  MSG1 (9.)  12.     "RATE
        $DATA  MSG1 (10.)  -1      "REPEAT COUNT
"
        $DATA  MSG2 (1.)  2       "MESSAGE NUMBER
        $DATA  MSG2 (2.)  0       "MESSAGE COUNT
        $DATA  MSG2 (3.)  MSG2+2  "RLINK
        $DATA  MSG2 (4.)  MSG2+2  "LLINK
        $DATA  MSG2 (5.)  0       "STATUS
        $DATA  MSG2 (6.)  100.    "TICK COUNT
        $DATA  MSG2 (7.)  0       "COUNT DOWN
        $DATA  MSG2 (8.)  1       "REPEAT
        $DATA  MSG2 (9.)  11.     "RATE
        $DATA  MSG2 (10.)  -1      "REPEAT COUNT
"
        $DATA  MSG3 (1.)  3       "MESSAGE NUMBER
        $DATA  MSG3 (2.)  0       "MESSAGE COUNT
        $DATA  MSG3 (3.)  MSG3+2  "RLINK
        $DATA  MSG3 (4.)  MSG3+2  "LLINK
        $DATA  MSG3 (5.)  0       "STATUS
        $DATA  MSG3 (6.)  50.     "TICK COUNT
        $DATA  MSG3 (7.)  0       "COUNT DOWN
        $DATA  MSG3 (8.)  1       "REPEAT
        $DATA  MSG3 (9.)  12.     "RATE
        $DATA  MSG3 (10.)  -1      "REPEAT COUNT
"
"
        $END
