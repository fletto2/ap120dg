# APFSRC -- routine reference

**Reconstructed from `[327,010]APFSRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [RESLVE](#reslve) | RESLVE | - | 10 |
| [FUNSAV](#funsav) | FUNSAV | - | 0 |
| [FUNRES](#funres) | FUNRES | - | 0 |
| [SAVE](#save) | SAVE | - | 0 |
| [XSAV](#xsav) | XSAV00 | - | 0 |
| [XRST](#xrst) | XRST00 | - | 0 |
| [MAXMIN](#maxmin) | AMAX1 | - | 0 |
| [SPDIV](#spdiv) | SPDIV | - | 4 |
| [SPMUL](#spmul) | SPMUL | - | 4 |
| [SQRT](#sqrt) | SQRT | - | 5 |
| [SINCOS](#sincos) | SIN | - | 8 |
| [ATAN](#atan) | ATAN | - | 5 |
| [IABS](#iabs) | IABS | - | 1 |
| [ABS](#abs) | ABS | - | 1 |
| [IDIM](#idim) | IDIM | - | 2 |
| [DIM](#dim) | DIM | - | 2 |
| [ISIGN](#isign) | ISIGN | - | 2 |
| [SIGN](#sign) | SIGN | - | 2 |
| [MOD](#mod) | MOD | - | 4 |
| [AMOD](#amod) | AMOD | - | 5 |
| [AINT](#aint) | AINT | - | 3 |
| [TANH](#tanh) | TANH | - | 0 |
| [COSH](#cosh) | COSH | - | 6 |
| [SINH](#sinh) | SINH | - | 8 |
| [IEXPI](#iexpi) | IEXPI | - | 3 |
| [REXPI](#rexpi) | REXPI | - | 3 |
| [REXPR](#rexpr) | REXPR | - | 5 |
| [LOG](#log) | LOG | - | 8 |
| [EXP](#exp) | EXP | - | 6 |
| [IFIX](#ifix) | INT | - | 2 |
| [FLOAT](#float) | FLOAT | - | 2 |
| [FAPUT](#faput) | FAPUT | - | 1 |
| [FAPUSH](#fapush) | FAPUSH | - | 0 |
| [DIVIDE](#divide) | DIV | - | 0 |

34 routines.


## RESLVE

`$ENTRY RESLVE`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BA` |  |
| 0 | `MASK` |  |
| 0 | `PATTERN` |  |
| 1 | `ADR` |  |
| 1 | `CO` |  |
| 1 | `NN` |  |
| 14 | `C27` |  |
| 15 | `EXP` |  |
| 15 | `MAP` |  |
| 15 | `NM` |  |


    AND THE ADDRESS AND SIZE OF THE BLOCK ARE PLACED IN SP(0) AND SP(1)
    EQUIPMENT:    AP-120 B
    SIZE:         27. LOCATIONS
    ---SCRATCH---
    CALL WITH SPAD-17 SET WITH A BIT MAP INDICATING WHICH S-PAD REGISTERS
    THE VECTOR ADD ROUTINE IS CALLED WITH A CALL OF:
    CALL VADD(A,I,B,J,C,K,N)
    --- SCRATCH ---


## FUNSAV

`$ENTRY FUNSAV`


_No `$EQU` parameter block found._


_The header states no formula, size or abstract._


## FUNRES

`$ENTRY FUNRES`


_No `$EQU` parameter block found._


_The header states no formula, size or abstract._


## SAVE

`$ENTRY SAVE`


_No `$EQU` parameter block found._


    AS SCRATCH SPACE.
    SCRATCH:   THE OTHER REGISTERS USED BY THE BASIC EXTERNAL FUNCTIONS
    USED FOR SCRATCH.
    SINCE APFTN USES SP(17) AND DPX(3) ONLY AS SCRATCH, THE
    INTEGRITY OF SP(17) DOES NOT NEED TO BE GUARANTEED, AND DPX(3)
    6   SCRATCH                       SCRATCH
    7   SCRATCH                       SCRATCH


## XSAV

`$ENTRY XSAV00`


_No `$EQU` parameter block found._


_The header states no formula, size or abstract._


## XRST

`$ENTRY XRST00`


_No `$EQU` parameter block found._


    RESTORES GLOBAL REGISTERS AFTER APFTN CALL FOR FAST MEMORY


## MAXMIN

`$ENTRY AMAX1`


_No `$EQU` parameter block found._


_The header states no formula, size or abstract._


## SPDIV

`$ENTRY SPDIV`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `C` |  |
| 0 | `N27` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  15 WORDS + SCALAR DIVIDE
    --- SCRATCH ---
    SCRATCH: DPX(DPA),DPY(DPA), PLUS DIV


## SPMUL

`$ENTRY SPMUL`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `C` |  |
| 0 | `N27` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  14 WORDS
    --- SCRATCH ---
    SCRATCH: DPX(DPA), I.E. DPX(0) RELATIVE TO DPA


## SQRT

`$ENTRY SQRT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `EXP` |  |
| 0 | `X` |  |
| 1 | `TEMP` |  |
| 1 | `TWO` |  |


    --- ABSTRACT ---
    DOES  DPX(DPA) = SQRT( DPX(DPA) )
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             28 PROGRAM LOCATIONS
    SCRATCH:          SP: 12.,13.,14.,15.;  DPX: 0,1; DPY: 0,1 (REL TO DPA)
    DOES SQRT(X)
    ARE SCRATCHED IN AND THE PREVIOUS CONTENTS LOST
    DOES THE SQUARE ROOT VIA AN INTERPOLATED TABLE LOOPUP
    THE MULTIPLY OF .5A*2.0 DOESN'T COST US ANYTHING, AS WE AREN'T


## SINCOS

`$ENTRY SIN`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AF` |  |
| 0 | `C` |  |
| 0 | `X` |  |
| 1 | `F` |  |
| 1 | `F2` |  |
| 1 | `F3` |  |
| 1 | `TEMPX` |  |
| 2 | `I` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    REV 2.2:      H. WILLIAMS -- FIXED LOSS OF ACCURACY FOR SMALL ARGUMENTS
    REV 2.3:      H. SEDINGER -- FIXED LOSS OF ACCURACY FOR NEGATIVE
    SCRATCH:       DPX(0,1), DPY(0,2)
    (NOTE:  TO FIX LOSS OF ACCURACY FOR SMALL ARGS,         (5/78)


## ATAN

`$ENTRY ATAN`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` |  |
| 0 | `Y` |  |
| 0 | `YTEMP` |  |
| 1 | `ONE` |  |
| 1 | `XTEMP` |  |


    --- ABSTRACT ---
    ALSO, DOES ATN2(X,Y) = ATAN(Y/X)
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SCRATCH:       SP (12-17), DPX(0-2), DPY(0-1)
    Y = 1.0 - 2/(1+X), K=PI/4
    Y = 1.0 / X,  K=-PI/2


## IABS

`$ENTRY IABS`


| s-pad | name | meaning |
|---|---|---|
| 0 | `I` | I, IABS(I) |


    FORMULA:  IABS(I) =  I IF I.GE.0
    = -I IF I.LT.0
    SIZE:  4. LOCATIONS
    SCRATCH:  SP(0)


## ABS

`$ENTRY ABS`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, ABS(X) |


    FORMULA:  ABS(X) =  X IF X.GE.0.0
    = -X IF X.LT.0.0
    SIZE:  1. LOCATIONS
    SCRATCH:  DPX(0), FA


## IDIM

`$ENTRY IDIM`


| s-pad | name | meaning |
|---|---|---|
| 0 | `I` | I, IDIM(I,J) |
| 1 | `J` | J |


    FORMULA:  IDIM(I,J) = I-J IF I-J.GE.0
    = 0   IF I-J.LT.0
    SIZE:  4. LOCATIONS
    SCRATCH:  SP(0,1)


## DIM

`$ENTRY DIM`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, DIM(X,Y) |
| 0 | `Y` | Y |


    FORMULA:  DIM(X,Y) = X-Y IF X-Y.GE.0.0
    = 0.0 IF X-Y.LT.0.0
    SIZE:  4. LOCATIONS
    SCRATCH:  DPX(0), DPY(0), FA


## ISIGN

`$ENTRY ISIGN`


| s-pad | name | meaning |
|---|---|---|
| 0 | `I` | I, ISIGN(I,J) |
| 1 | `J` | J |


    FORMULA:  ISIGN(I,J) =  ABS(I) IF J.GE.0
    = -ABS(I) IF J.LT.0
    SIZE:  4. LOCATIONS
    SCRATCH:  SP(0,1)


## SIGN

`$ENTRY SIGN`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, SIGN(X,Y) |
| 0 | `Y` | Y |


    FORMULA:  SIGN(X,Y) =  ABS(X) IF Y.GE.0.0
    = -ABS(X) IF Y.LT.0.0
    SIZE:  4. LOCATIONS.
    SCRATCH:  DPX(0), DPY(0), FA


## MOD

`$ENTRY MOD`


| s-pad | name | meaning |
|---|---|---|
| 0 | `FLOATI` | FLOAT(I) |
| 0 | `FLOATJ` | FLOAT(J) |
| 0 | `I` | I, MOD(I,J) |
| 1 | `J` | J |


    FORMULA:  MOD(I,J) = IFIX(AMOD(FLOAT(I),FLOAT(J)))
    SIZE:  5. LOCATIONS
    SCRATCH:  SP(0,1,14-17), DPX(0-2), DPY(0,1), FA, FM, TM


## AMOD

`$ENTRY AMOD`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, AMOD(Y,X) |
| 0 | `Y` | Y |
| 1 | `SAVEX` | SAVE X |
| 2 | `SAVEY` | SAVE Y |
| 12 | `CNT` |  |


    FORMULA:  AMOD(Y,X) = Y-AINT(Y/X)*X
    ARITHMETIC INACCURACY
    SIZE:  12. LOCATIONS
    SCRATCH:  SP(14-17), DPX(0-2), DPY(0,1), FA, FM, TM


## AINT

`$ENTRY AINT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, AINT(X) |
| 14 | `EXPX` | EXPONENT OF X |
| 15 | `CONS` | CONSTANT |


    FORMULA:  AINT(X) = INTEGER PART OF X
    SIZE:  6. LOCATIONS
    SCRATCH:  SP(16,17), DPX(0), FA


## TANH

`$ENTRY TANH`


_No `$EQU` parameter block found._


    FORMULA:  TANH(X) = SINH(X)/COSH(X)
    SIZE:  2. LOCATIONS
    SCRATCH:  SP(15-17), DPX(0,1), DPY(0-2), FA, FM, TM


## COSH

`$ENTRY COSH`


| s-pad | name | meaning |
|---|---|---|
| 0 | `EXPX` | EXP(X) |
| 0 | `SINHX` | SINH(X) |
| 0 | `X` | X, COSH(X) |
| 1 | `SAVEDX` | SAVED X |
| 2 | `SAVESH` | SAVE SINH(X) |
| 14 | `EXPN` | EXPONENT OF X |


    FORMULA:  COSH(X) = EXP(X)-SINH(X)
    REL 3.1: R. COLYAR, APR 79   FORMULA TO CALCULATE COSH(X) CORRECTED, AND
    SIZE:  7. LOCATIONS
    SCRATCH:  SP(16,17), DPX(0,1), DPY(0-2), FA, FM, TM


## SINH

`$ENTRY SINH`


| s-pad | name | meaning |
|---|---|---|
| 0 | `COEF` | A0, A1, A2, A3 |
| 0 | `EXPX` | EXP(X) |
| 0 | `X` | X, SINH(X) |
| 1 | `SAVEX` | SAVE X |
| 1 | `XSQ` | X**2 |
| 2 | `SAVEXP` | SAVE EXP(-X) |
| 14 | `EXPN` | EXPONENT OF X |
| 15 | `CNT` | LOOP COUNT |


    FORMULA:  SINH(X) = X*(A0+A1*X**2+A2*X**4+A3*X**6) IF ABS(X).LT.0.5
    = (EXP(X)-EXP(-X))/2             IF ABS(X).GE.0.5
    SIZE:  24. LOCATIONS
    SCRATCH:  SP(16,17), DPX(0,1), DPY(0-2), FA, FM, TM
    THAT LOSS OF SIGNIFICANCE DUE TO CANCELATION DOES NOT OCCUR WHEN X IS CLOSE


## IEXPI

`$ENTRY IEXPI`


| s-pad | name | meaning |
|---|---|---|
| 0 | `I` | I, I**J |
| 0 | `X` | X |
| 1 | `J` | J |


    FORMULA:  I**J = FIX(EXP(LN(FLOAT(I))*FLOAT(J)))
    SIZE:  6. LOCATIONS
    SCRATCH:  SP(0,1,13-17), DPX(0-2), DPY(0,1), FA, FM, TM


## REXPI

`$ENTRY REXPI`


| s-pad | name | meaning |
|---|---|---|
| 0 | `FLOATI` | FLOAT(I) |
| 0 | `X` | X, X**I |
| 1 | `SAVEX` | SAVE X |


    FORMULA:  X**I = EXP(LN(X)*FLOAT(I))
    SIZE:  3. LOCATIONS
    SCRATCH:  SP(0,13-17), DPX(0-2), DPY(0,1), FA, FM, TM


## REXPR

`$ENTRY REXPR`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X, X**Y |
| 0 | `Y` | Y |
| 2 | `SAVEY` | SAVE Y |
| 11 | `J` |  |
| 12 | `F` |  |


    FORMULA:  X**Y = EXP(LN(X)*Y)
    SIZE:  18. LOCATIONS
    SCRATCH:  SP(13-17), DPX(0-2), DPY(0-2), FA, FM, TM


## LOG

`$ENTRY LOG`


| s-pad | name | meaning |
|---|---|---|
| 0 | `U` |  |
| 0 | `V` |  |
| 0 | `V2` |  |
| 0 | `X` |  |
| 1 | `LN2` |  |
| 1 | `XTEMP` |  |
| 1 | `YTEMP` |  |
| 2 | `S` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP 120 B WITH EITHER MEMORY
    SAMPLE CALL    JSR LN  OR JSR LOG
    SCRATCH:       SP(15-17); DPX(0-2),DPY(0-1),


## EXP

`$ENTRY EXP`


| s-pad | name | meaning |
|---|---|---|
| 0 | `F` |  |
| 0 | `TEMPY` |  |
| 0 | `X` |  |
| 0 | `Y` |  |
| 1 | `F2` |  |
| 1 | `SCALE` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY


## IFIX

`$ENTRY INT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `INTX` | INT(X), IFIX(X) |
| 0 | `X` | X |


    FORMULA:  IFIX(X) = INT(X) = LOW-ORDER 16 BITS OF INTEGER PART OF X
    SIZE:  3. LOCATIONS
    SCRATCH:  SP(0), DPX(0), FA


## FLOAT

`$ENTRY FLOAT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `FLOATI` | FLOAT(I) |
| 0 | `I` | I |


    FORMULA:  FLOAT(I) = 2**E*M
    SIZE:  3. LOCATIONS
    SCRATCH:  SP(0), DPX(0), FA


## FAPUT

`$ENTRY FAPUT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `X` | X |


    FORMULA:  FAPUT() = PUT RESULT OF PREVIOUS ADDER OPERATION INTO FA AND DPX(0)
    SIZE:  2. LOCATIONS
    SCRATCH:  DPX(0), FA


## FAPUSH

`$ENTRY FAPUSH`


_No `$EQU` parameter block found._


    FORMULA:  FAPUSH() = PUT RESULT OF PREVIOUS ADDER OPERATION INTO FA
    SIZE:  1. LOCATION
    SCRATCH:  FA


## DIVIDE

`$ENTRY DIV`


_No `$EQU` parameter block found._


    DIVIDE SUBROUTINE:    DOES DPY/DPX
    --- ABSTRACT ---
    DOES:   DPX(DPA) = DPY(DPA) / DPX(DPA)
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             28 PROGRAM LOCATIONS
    SCRATCH:          SP: 13.-15.;  DPX: 0,1;  DPY: 0  (REL TO DPA)
    DOES THE INVERSE VIA AN INTERPOLATED TABLE LOOKUP

