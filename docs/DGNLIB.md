# DGNSRC -- routine reference

**Reconstructed from `[327,010]DGNSRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [SCFIFT](#scfift) | SCFIFT | 4 | 5 |
| [SLFCHK](#slfchk) | FGRN | - | 12 |
| [RMTST](#rmtst) | RMTST | 3 | 11 |
| [BITS](#bits) | BITS | 5 | 8 |
| [BCHK](#bchk) | BCHK | 5 | 14 |
| [RGEN](#rgen) | RGEN | - | 4 |
| [BADD](#badd) | BADD | 2 | 8 |
| [ACHK](#achk) | ACHK | 2 | 14 |
| [ZMDFT](#zmdft) | ZMDFT | 0 | 0 |
| [ZMD](#zmd) | ZMD | 0 | 11 |
| [APFET](#apfet) | APFET | 0 | 9 |

11 routines.


## SCFIFT

`$ENTRY SCFIFT, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` | BASE ADDRESS OF ARRAY |
| 1 | `N` | NUMBER OF COMPLEX POINTS |
| 2 | `IX` | RANDOM NUMBER SEEDS |
| 3 | `IY` |  |
| 3 | `M` | M=LOG2(N) |


    --- ABSTRACT ---
    SIZE: 19 + SLFCHK (54) + CFFT (186 FAST, 184 SLOW)
    S-PAD PARAMETERS:


## SLFCHK

`$ENTRY FGRN`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` |  |
| 1 | `SIZE` |  |
| 2 | `L2N` |  |
| 4 | `BB` |  |
| 8 | `TMP` |  |
| 9 | `CNTR` |  |
| 10 | `EXP1` |  |
| 11 | `EXP2` |  |
| 12 | `M` |  |
| 13 | `XN` |  |
| 14 | `YN` |  |
| 15 | `ERRFLG` |  |


    EQUIPMENT:  AP120B WITH EITHER MEMORY
    SIZE:  54 LOCATIONS
    SP(1)   = SIZE
    SCRATCH VARIABLES:
    DPY(-3) = SCRATCH
    GRN DOES A DEC CNTR FOR THE CALLING


## RMTST

`$ENTRY RMTST, 3`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CT` | ITERATION COUNT |
| 1 | `CA` | CURRENT ADDRESS |
| 2 | `EX` | EXPONENT |
| 2 | `RPAR` | RANDOM NUMBER PARAMETER (TEMP FOR CALL) |
| 3 | `HM` | HI MANTISSA |
| 4 | `LM` | LO MANTISSA |
| 5 | `REX` | RECEIVED EXPONENT |
| 6 | `RHM` | RECEIVED HI MANTISSA |
| 7 | `RLM` | RECEIVED LO MANTISSA |
| 8 | `RND` | RANDOM NUMBER SEED |
| 15 | `ERRS` | ERROR SWITCH |


    GET RANDOM NUMBER FM FORTRAN CALL INTO 'RND'


## BITS

`$ENTRY BITS, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CT` | ITERATION COUNT |
| 1 | `CA` | CURRENT ADDRESS |
| 2 | `EX` | EXPONENT |
| 3 | `HM` | HI MANTISSA |
| 4 | `LM` | LO MANTISSA |
| 12 | `T1` | TEMPORARY REGISTER |
| 13 | `M15` | 15 BIT MASK |
| 14 | `N12` | NUMBER 12 |


_The header states no formula, size or abstract._


## BCHK

`$ENTRY BCHK, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CT` | ITERATION COUNT |
| 1 | `CA` | CURRENT ADDRESS |
| 2 | `EX` | EXPONENT |
| 3 | `HM` | HI MANTISSA |
| 4 | `LM` | LO MANTISSA |
| 5 | `REX` | RECEIVED EXPONENT |
| 6 | `RHM` | RECEIVED HI MANTISSA |
| 7 | `RLM` | RECEIVED LO MANTISSA |
| 10 | `T1` | TEMPORARY REGISTER |
| 11 | `T2` | TEMPORARY REGISTER |
| 12 | `M10` | 10 BIT MASK |
| 13 | `M12` | 12 BIT MASK |
| 14 | `N17` | NUMBER 17 |
| 15 | `ERRS` | ERROR SWITCH |


_The header states no formula, size or abstract._


## RGEN

`$ENTRY RGEN`


| s-pad | name | meaning |
|---|---|---|
| 2 | `T1` | TEMPORARY REGISTER |
| 3 | `T2` | TEMPORARY REGISTER |
| 4 | `N1` | NUMBER 1 |
| 8 | `RND` | RANDOM NUMBER SEED |


_The header states no formula, size or abstract._


## BADD

`$ENTRY BADD, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CT` | ITERATION COUNT |
| 1 | `CA` | CURRENT ADDRESS |
| 2 | `EX` | EXPONENT |
| 3 | `HM` | HI MANTISSA |
| 4 | `LM` | LO MANTISSA |
| 12 | `T1` | TEMPORARY REGISTER |
| 13 | `M15` | 15 BIT MASK |
| 14 | `N12` | NUMBER 12 |


_The header states no formula, size or abstract._


## ACHK

`$ENTRY ACHK, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CT` | ITERATION COUNT |
| 1 | `CA` | CURRENT ADDRESS |
| 2 | `EX` | EXPONENT |
| 3 | `HM` | HI MANTISSA |
| 4 | `LM` | LO MANTISSA |
| 5 | `REX` | RECEIVED EXPONENT |
| 6 | `RHM` | RECEIVED HI MANTISSA |
| 7 | `RLM` | RECEIVED LO MANTISSA |
| 10 | `T1` | TEMPORARY REGISTER |
| 11 | `T2` | TEMPORARY REGISTER |
| 12 | `M10` | 10 BIT MASK |
| 13 | `M12` | 12 BIT MASK |
| 14 | `N17` | NUMBER 17 |
| 15 | `ERRS` | ERROR SWITCH |


_The header states no formula, size or abstract._


## ZMDFT

`$ENTRY ZMDFT, 0`


_No `$EQU` parameter block found._


    --- ABSTRACT ---
    OR FAST -- 1 CYCLE), TMROM SIZE (2.5K OR 4.5K), TMRAM STARTING ADDRESS
    TMROM SIZE.  COMPARISON IS MADE OF MD TYPE AND TMROM SIZE DETERMINED
    14            ROMERR   0 = ROM SIZE SAME AS EXPECTED BY SW
    1 = ROM SIZE DIFFERS FROM EXPECTED SIZE
    SIZE: 2 + APFET (64) + ZMD (29) = 95 PS WORDS
    FORTRAN CALL:  CALL ZMDFT
    SCRATCH:       SP(0-17),DPX(0,1),DPY(0),TM,MD,DA


## ZMD

`$ENTRY ZMD, 0`


| s-pad | name | meaning |
|---|---|---|
| 0 | `PAGE` | CURRENT PAGE NUMBER |
| 1 | `SIZE` | SIZE OF THE CURRENT PAGE |
| 2 | `MEMINC` | MEMORY INCREMENT |
| 3 | `TEST` | TEST VALUE |
| 4 | `TEMP` | TEST RESULT |
| 5 | `COUNT` | INCREMENT COUNTER |
| 7 | `TVAL` | TEST VALUE |
| 8 | `MODCNT` | NUMBER OF MEMORY MODULES |
| 15 | `MAXPAG` | MAXIMUM PAGE NUMBER |
| 24 | `MAE` | MA EXTENSION DEVICE ADDRESS |
| 8192 | `MINVAL` | MEMORY MODULE INCREMENT |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH FAST OR SLOW MAIN DATA MEMORY
    SIZE:          29 LOCATIONS
    -------LOOP TO SIZE THE PAGE
    ZERO, EXCEPT WHEN THE SIZE WAS ZERO, IN WHICH CASE LOCATION


## APFET

`$ENTRY APFET, 0`


| s-pad | name | meaning |
|---|---|---|
| 1 | `EXMD` |  |
| 6 | `RAMFWA` |  |
| 7 | `ERRMT` |  |
| 8 | `MDTYPE` |  |
| 9 | `ACTMT` |  |
| 10 | `RAM` |  |
| 11 | `APTYPE` |  |
| 12 | `ROM` |  |
| 13 | `EXPMT` |  |


    --- ABSTRACT ---
    OR FAST -- 1 CYCLE), TMROM SIZE (2.5K OR 4.5K), TMRAM STARTING ADDRESS
    TMROM SIZE.  COMPARISON IS MADE OF MD TYPE AND TMROM SIZE DETERMINED
    14            ROMERR   0 = ROM SIZE SAME AS EXPECTED BY SW
    1 = ROM SIZE DIFFERS FROM EXPECTED SIZE
    SIZE: 64 WORDS
    FORTRAN CALL:  CALL APFET
    SCRATCH:       SP(6-17),DPX(0,1),DPY(0),TM,MD,DA
    INSTRUCTION CHANGES SPFN.  THE 120/190 DOES, THE 100 DOESNT.
    TEST FOR TMROM SIZE (2.5K OR 4.5K) BY EXAMINING TMROM LOCATION
    COMPARE MD TYPE AND TMROM SIZE TO VERSIONS EXPECTED BY THIS ROUTINE.

