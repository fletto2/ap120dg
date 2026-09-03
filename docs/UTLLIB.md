# UTLSRC -- routine reference

**Reconstructed from `[327,010]UTLSRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [FLUSH](#flush) | FLUSH | - | 0 |
| [XRFFT](#xrfft) | XRFFT | 4 | 5 |
| [XCFFT](#xcfft) | XCFFT | 4 | 12 |
| [XBITRE](#xbitre) | XBITRE | - | 11 |
| [PCFFT](#pcfft) | PCFFT | 4 | 12 |
| [XFFT4](#xfft4) | XFFT4 | - | 28 |
| [XREALT](#xrealt) | XREALT | - | 18 |
| [RTOC](#rtoc) | RTOC | 4 | 18 |
| [CTOR](#ctor) | CTOR | 4 | 13 |
| [BITREV](#bitrev) | BITREV | - | 8 |
| [REALTR](#realtr) | REALTR | - | 17 |
| [FFT2B](#fft2b) | FFT2B | - | 14 |
| [FFT4B](#fft4b) | FFT4B | - | 16 |
| [FFT2](#fft2) | FFT2 | - | 12 |
| [FFT4](#fft4) | FFT4 | - | 28 |
| [STATUS](#status) | STSTAT | - | 0 |
| [ADV](#adv) | ADV4 | - | 4 |
| [SET24B](#set24b) | SET24B | - | 4 |
| [VFCL1](#vfcl1) | VFCL1 | - | 7 |
| [VFCL2](#vfcl2) | VFCL2 | - | 9 |
| [SPFLT](#spflt) | SPFLT | - | 3 |
| [SPUFLT](#spuflt) | SPUFLT | - | 2 |
| [SAVESP](#savesp) | SAVESP | - | 3 |
| [SAVSP0](#savsp0) | SAVSP0 | - | 2 |
| [SETSP](#setsp) | SETSP | - | 4 |
| [SPNEG](#spneg) | SPNEG | - | 1 |
| [SPNOT](#spnot) | SPNOT | - | 1 |
| [SPADD](#spadd) | SPADD | - | 2 |
| [SPSUB](#spsub) | SPSUB | - | 2 |
| [SPRS](#sprs) | SPRS | - | 2 |
| [SPLS](#spls) | SPLS | - | 2 |
| [SPAND](#spand) | SPAND | - | 2 |
| [SPOR](#spor) | SPOR | - | 2 |
| [SSDM](#ssdm) | SSDM | - | 13 |
| [DDDM](#dddm) | DDDM | - | 16 |
| [SSDA](#ssda) | SSDA | - | 5 |
| [SDDA](#sdda) | SDDA | - | 9 |
| [DDDA](#ddda) | DDDA | - | 14 |
| [APNOP](#apnop) | APNOP | 0 | 0 |

39 routines.


## FLUSH

`$ENTRY FLUSH`


_No `$EQU` parameter block found._


    ---ABSTRACT---
    EQUIPMENT:  AP WITH EITHER SPEED MEMORY
    SIZE:       4 PS WORDS
    SCRATCH:    DPX(0),FA,FM,SP(17)


## XRFFT

`$ENTRY XRFFT, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` |  |
| 1 | `N` |  |
| 2 | `DI` |  |
| 3 | `F` |  |
| 7 | `CSAVE` |  |


    --- ABSTRACT ---
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    C = 0
    N = 1
    F = 3
    SIZE:  17 PS LOCATIONS
    --- SCRATCH (OVERALL) ---
    DOES A REAL FFT:
    DIRECT:    DOES FIRST AN N/2 POINT COMPLEX FFT, AND THEN
    INVERSE:   DOES AN N POINT INVERSE REAL TRANSFORM PASS,


## XCFFT

`$ENTRY XCFFT, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF ARRAY |
| 1 | `N` | # OF COMPLEX POINTS TO BE TRANSFORMED (>1) |
| 2 | `DI` | MEMORY INCREMENT |
| 3 | `F` | DIRECTIONS:  1 = FORWARD,  -1 = INVERSE |
| 11 | `I` | TOP OF ARRAY FOR BITREVERSE |
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `FP` | PARAMETER FOR STSTAT (F) |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |
| 15 | `M` | FROM STSTAT (M = LOG2(N) ) |
| 15 | `NP` | FOR STSTAT (N) |


    --- ABSTRACT ---
    DOES A COMPLEX FFT
    EQUIPMENT:                     AP-120B WITH EITHER MEMORY
    SIZE:  22 PS LOCATIONS
    S-PAD PARAMETERS:
    --- SCRATCH (OVERALL) ---
    1.      CALL 'STSTAT'      THIS TAKES 'N' AND 'F', AND SETS THE BIT-REVERSE
    CALL XFFT4  (TO DO THE NEXT FFT PASS)
    CALL ADV4  (TO ADVANCE TO THE NEXT PASS)
    5.     WHEN DONE, CALL 'CLSTAT' TO CLEAR THE BIT-REVERSE AND FFT-MODE
    SIZE OF INSTALLED FFT TABLE
    SET AP-STATUS FOR BIT-REVERSE SIZE


## XBITRE

`$ENTRY XBITRE`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` | ARRAY BASE ADDRESS |
| 1 | `N` | NUMBER OF COMPLEX POINTS |
| 2 | `DI` | INCREMENT BETWEEN COMPLEX LOCATIONS |
| 3 | `DT` | DELTA FOR T (DI*256) |
| 8 | `CTI` | SHIFT LEFT COUNTER |
| 9 | `BASEP1` | BASE + DI |
| 10 | `AT` | &I STORAGE |
| 11 | `I` | UPPER ADDRESS OF ARRAY = N*DI |
| 12 | `T` | ARRAY SUBSCRIPT SHIFTED LEFT 8 (*256) |
| 13 | `MDEL` |  |
| 14 | `TI` | I STORAGE |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH STANDARD MEMORY
    SIZE:          57 LOCATIONS
    S-PAD PARAMETERS:              BASE ADDRESS OF ARRAY
    --- SCRATCH ---


## PCFFT

`$ENTRY PCFFT, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF ARRAY |
| 1 | `N` | # OF COMPLEX POINTS TO BE TRANSFORMED (>1) |
| 2 | `DI` | MEMORY INCREMENT |
| 3 | `F` | DIRECTIONS:  1 = FORWARD,  -1 = INVERSE |
| 3 | `TN` | EXPANDED N = N*(DI/2)**2 |
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `FP` | PARAMETER FOR STSTAT (F) |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |
| 15 | `M` | FROM STSTAT (M = LOG2(TN) ) |
| 15 | `NP` | FOR STSTAT (TN) |


    --- ABSTRACT ---
    DOES A COMPLEX FFT EXCEPT BIT REVERSE,SET STATUS,CLEAR STATUS
    EQUIPMENT:                     AP-120B WITH EITHER MEMORY
    SIZE:          15 PS LOCATIONS
    DOES A PARTIAL COMPLEX FFT, I.E., THE RADIX 2 AND RADIX 4 PASSES.
    S-PAD PARAMETERS:
    --- SCRATCH (OVERALL) ---
    CALL FFT4  (TO DO THE NEXT FFT PASS)
    CALL ADV4  (TO ADVANCE TO THE NEXT PASS)
    SIZE OF INSTALLED FFT TABLE


## XFFT4

`$ENTRY XFFT4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AR` | A REAL |
| 0 | `BASE` | BASE ADDRESS OF ARRAY |
| 0 | `CR` | C REAL |
| 1 | `AI` | A IMAGINARY |
| 1 | `CI` | C IMAGINARY |
| 1 | `N` | # OF COMPLEX POINTS (NOT USED HERE) |
| 2 | `BBR` | 5 THROUGH 10     B REAL |
| 2 | `BII` | 15 THROUGH 3     W1I * BI |
| 2 | `BRR` | 13 THROUGH 3     W1R * BR |
| 2 | `DR` | 7 THROUGH 10     D REAL |
| 2 | `MINC` | MEMORY INCREMENT |
| 3 | `BI` | 6 THROUGH 9      B IMAGINARY |
| 3 | `BIR` | 16 THROUGH 4     W1I * BR |
| 3 | `BRI` | 14 THROUGH 4     W1R * BI |
| 3 | `DI` | 8 THROUGH 9      D IMAGINARY |
| 3 | `JBASE` | BASE FOR EACH J-LOOP |
| 4 | `READ` | READ POINTER |
| 5 | `WRITE` | WRITE POINTER |
| 6 | `ICTR` | I-LOOP COUNTER |
| 7 | `JCTR` | J-LOOP COUNTER |
| 8 | `TEMP` | TEMPORARY |
| 9 | `W1` | W**1 POINTER |
| 10 | `W2` | W**2 POINTER |
| 11 | `W3` | W**3 POINTER |
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |


    --- ABSTRACT ---
    DOES ONE RADIX 4 COMPLEX FFT PASS
    EQUIPMENT:                     AP-120B WITH FAST (1 CYCLE) MEMORY
    PROGRAM SIZE:                  79 LOCATIONS
    DOES ONE RADIX 4 FFT PASS, AS DETERMINED BY:
    SCRATCH:
    I-LOOP DOES THE 'BUTTERFLIES' ON QUADS OF POINTS, 'MDEL'
    THESE ARE SCRATCH VARIABLES


## XREALT

`$ENTRY XREALT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF INPUT ARRAY |
| 0 | `AMCR` | AR - CR |
| 0 | `C` | BASE ADDRESS OF OUTPUT ARRAY |
| 0 | `RR` | WR*APCR |
| 1 | `APCI` | AI + CI |
| 1 | `N` | NUMBER OF REAL POINTS |
| 1 | `RI` | WR*AMCI |
| 2 | `MDEL` | MEMORY SPACING |
| 2 | `TR` | TEMP REAL |
| 3 | `F` | +1 FOR DIRECT, -1 FOR INVERSE |
| 8 | `W` | W POINTER |
| 9 | `WD` | W DELTA |
| 10 | `XN` | TOP OF ARRAY = N*MDEL/2 |
| 11 | `ICTR` | LOOP COUNTER |
| 12 | `AREAD` | A READ POINTER |
| 13 | `CREAD` | C READ POINTER |
| 14 | `AWRITE` | A WRITE POINTER |
| 15 | `CWRITE` | C WRITE POINTER |


    --- ABSTRACT ---
    EQUIPMENT:   AP-120B WITH FAST (1 CYCLE) MEMORY)
    SIZE:       49 LOCATIONS + STATUS (19) = 68
    S-PAD PARAMETERS:
    THEN CALL THIS SUBROUTINE
    INVERSE:       CALL THIS SUBROUTINE
    --- SCRATCH ---
    SIZE OF FFT COSINE TABLE


## RTOC

`$ENTRY RTOC, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` | ARRAY BASE ADDRESS |
| 1 | `N` | ARRAY LENGTH (A POWER OF 2) |
| 1 | `TI` |  |
| 1 | `TR` |  |
| 2 | `A2I` |  |
| 2 | `A2R` |  |
| 3 | `A1I` |  |
| 3 | `A1R` |  |
| 3 | `MDEL` | MEMORY SPACING (A POWER OF 2) |
| 4 | `LBASE` |  |
| 5 | `MBASE` |  |
| 6 | `WBASE` |  |
| 7 | `TBASE` |  |
| 8 | `N2` |  |
| 9 | `A` |  |
| 10 | `B` |  |
| 11 | `EBASE` |  |
| 12 | `MDEL2` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          139 PS WORDS
    THE FOLLOWING ARE SCRATCH
    SCRATCH:
    FROM ABOVE FORMULAS A1R(0) = AR(0) AND


## CTOR

`$ENTRY CTOR, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` |  |
| 1 | `N` |  |
| 2 | `A2I` |  |
| 2 | `A2R` |  |
| 3 | `A1I` |  |
| 3 | `A1R` |  |
| 3 | `MDEL` |  |
| 4 | `LBASE` |  |
| 5 | `MBASE` |  |
| 6 | `WBASE` |  |
| 7 | `TBASE` |  |
| 8 | `N2` |  |
| 9 | `A` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          74 PS WORDS
    THE FOLLOWING ARE SCRATCH
    SCRATCH:    SP(4-9,15),DPX(-4 TO 3),DPY(-4 TO 3), TM,FA,FM,MD


## BITREV

`$ENTRY BITREV`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BASE` | ARRAY BASE ADDRESS |
| 1 | `N` | N (NUMBER OF COMPLEX POINTS) |
| 9 | `BASEP1` | BASE + DI |
| 10 | `BASEP2` | BASE + 2 * DI |
| 11 | `I` | ARRAY SUBSCRIPT |
| 12 | `T` | ARRAY SUBSCRIPT SHIFTED LEFT 8 (*256) |
| 13 | `DT` | DELTA FOR T (2 * 256 = 512) |
| 14 | `DI` | DELTA FOR I (2) |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B WITH 1 CYCLE (FAST) MEMORY
    SIZE:  45 LOCATIONS
    S-PAD PARAMETERS:
    --- SCRATCH ---


## REALTR

`$ENTRY REALTR`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF INPUT ARRAY |
| 0 | `AMCR` | AR - CR |
| 0 | `RR` | WR*APCR |
| 1 | `APCI` | AI + CI |
| 1 | `C` | BASE ADDRESS OF OUTPUT ARRAY |
| 1 | `RI` | WR*AMCI |
| 2 | `N` | NUMBER OF REAL POINTS |
| 2 | `TR` | TEMP REAL |
| 3 | `F` | +1 FOR DIRECT, -1 FOR INVERSE |
| 8 | `W` | W POINTER |
| 9 | `WD` | W DELTA |
| 10 | `MDEL` | MEMORY DELTA |
| 11 | `ICTR` | LOOP COUNTER |
| 12 | `AREAD` | A READ POINTER |
| 13 | `CREAD` | C READ POINTER |
| 14 | `AWRITE` | A WRITE POINTER |
| 15 | `CWRITE` | C WRITE POINTER |


    --- ABSTRACT ---
    EQUIPMENT:   AP-120B WITH FAST (1 CYCLE) MEMORY)
    SIZE:       49 LOCATIONS + STATUS (19) = 68
    S-PAD PARAMETERS:
    THEN CALL THIS SUBROUTINE
    INVERSE:       CALL THIS SUBROUTINE
    --- SCRATCH ---
    SIZE OF FFT COSINE TABLE


## FFT2B

`$ENTRY FFT2B`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AR` | A REAL |
| 0 | `CR` | C REAL |
| 0 | `SOURCE` | BASE ADDRESS OF SOURCE ARRAY |
| 1 | `AI` | A IMAGINARY |
| 1 | `CI` | C IMAGINARY |
| 1 | `DEST` | BASE ADDRESS OF DESTINATION ARRAY |
| 2 | `AR1` |  |
| 3 | `AI1` |  |
| 3 | `READ` | READ POINTER |
| 4 | `WRITE` | WRITE POINTER |
| 5 | `ICTR` | LOOP COUNTER |
| 6 | `RDEL` | READ POINTER DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | LOOP COUNT |


    --- ABSTRACT ---
    DOES THE FIRST RADIX 2 PASS OF AN FFT WHERE THE BIT-REVERSE IS BEING COMBINED
    EQUIPMENT:                     AP-120B WITH FAST (1 CYCLE) MEMORY
    SIZE:                          17 LOCATIONS
    DOES THE FIRST PASS OF A NOT-IN-PLACE FFT WHERE A RADIX TWO PASS IS NEEDED
    --- SCRATCH ---
    SCRATCH VARIABLES


## FFT4B

`$ENTRY FFT4B`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AR` | A REAL |
| 0 | `CR` | C REAL |
| 0 | `SOURCE` | BASE ADDRESS OF SOURCE ARRAY |
| 1 | `AI` | A IMAGINARY |
| 1 | `CI` | C IMAGINARY |
| 1 | `DEST` | BASE ADDRESS OF DESTINATION ARRAY |
| 2 | `BBR` | B REAL |
| 2 | `DR` | D REAL |
| 3 | `BI` | B IMAGINARY |
| 3 | `DI` | D IMAGINARY |
| 3 | `READ` | READ POINTER |
| 4 | `WRITE` | WRITE POINTER |
| 5 | `ICTR` | I-LOOP COUNTER |
| 6 | `RDEL` | READ POINTER DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | I-LOOP COUNT |


    --- ABSTRACT ---
    DOES THE FIRST RADIX 4 FFT PASS WHEN THE BIT-REVERSE IS
    EQUIPMENT:                     AP-120B WITH FAST (1-CYCLE) MEMORY
    SIZE:                          35 LOCATIONS + SET24B (8) = 43
    DOES A COMBINES BIT-REVERSE AND RADIX 4 FIRST FFT PASS.
    --- SCRATCH ---
    SCRATCH VARIABLES


## FFT2

`$ENTRY FFT2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AR` | A REAL |
| 0 | `BASE` | BASE ADDRESS OF ARRAY |
| 0 | `CR` | C REAL |
| 1 | `AI` | A IMAGINARY |
| 1 | `CI` | C IMAGINARY |
| 2 | `AR1` |  |
| 3 | `AI1` |  |
| 3 | `READ` | READ POINTER |
| 4 | `WRITE` | WRITE POINTER |
| 5 | `ICTR` | LOOP COUNTER |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | LOOP COUNT |


    --- ABSTRACT ---
    DOES THE FIRST RADIX 2 FFT PASS WHERE THE DATA ARRAY HAS A ODD
    EQUIPMENT:                     AP-120B WITH FAST (1-CYCLE MEMORY)
    SIZE:                          16 PROGRAM LOCATIONS
    DOES THE FIRST PASS OF A COMPLEX FFT WHERE A RADIX 2 PASS IS NEEDED
    SCRATCH:
    SCRATCH VARIABLES


## FFT4

`$ENTRY FFT4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AR` | A REAL |
| 0 | `BASE` | BASE ADDRESS OF ARRAY |
| 0 | `CR` | C REAL |
| 1 | `AI` | A IMAGINARY |
| 1 | `CI` | C IMAGINARY |
| 1 | `N` | # OF COMPLEX POINTS (NOT USED HERE) |
| 2 | `BBR` | 5 THROUGH 10     B REAL |
| 2 | `BII` | 15 THROUGH 3     W1I * BI |
| 2 | `BRR` | 13 THROUGH 3     W1R * BR |
| 2 | `DR` | 7 THROUGH 10     D REAL |
| 2 | `JBASE` | BASE FOR EACH J-LOOP |
| 3 | `BI` | 6 THROUGH 9      B IMAGINARY |
| 3 | `BIR` | 16 THROUGH 4     W1I * BR |
| 3 | `BRI` | 14 THROUGH 4     W1R * BI |
| 3 | `DI` | 8 THROUGH 9      D IMAGINARY |
| 3 | `READ` | READ POINTER |
| 4 | `WRITE` | WRITE POINTER |
| 5 | `ICTR` | I-LOOP COUNTER |
| 6 | `JCTR` | J-LOOP COUNTER |
| 7 | `TEMP` | TEMPORARY |
| 8 | `W1` | W**1 POINTER |
| 9 | `W2` | W**2 POINTER |
| 10 | `W3` | W**3 POINTER |
| 11 | `MINC` | MEMORY INCREMENT OF THE ARRAY |
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |


    --- ABSTRACT ---
    DOES ONE RADIX 4 COMPLEX FFT PASS
    EQUIPMENT:                     AP-120B WITH FAST (1 CYCLE) MEMORY
    PROGRAM SIZE:                  79 LOCATIONS
    DOES ONE RADIX 4 FFT PASS, AS DETERMINED BY:
    SCRATCH:
    I-LOOP DOES THE 'BUTTERFLIES' ON QUADS OF POINTS, 'MDEL'
    THESE ARE SCRATCH VARIABLES


## STATUS

`$ENTRY STSTAT`


_No `$EQU` parameter block found._


    --- ABSTRACT ---
    EQUIPMENT:    AP-120B WITH EITHER SPEED MEMORY
    SCRATCH: SP(14-17)
    SCRATCH: SP(14-15)
    SCRATCH: SP(16-17)


## ADV

`$ENTRY ADV4`


| s-pad | name | meaning |
|---|---|---|
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |


    --- ABSTRACT ---
    EQUIPMENT:                     AP-120B WITH EITHER MEMORY
    SIZE:                          7 LOCATIONS
    --- SCRATCH ---


## SET24B

`$ENTRY SET24B`


| s-pad | name | meaning |
|---|---|---|
| 2 | `N` | NUMBER OF COMPLEX POINTS (INPUT) |
| 6 | `RDEL` | READ POINTER DELTA (OUTPUT) |
| 7 | `TEMP` |  |
| 13 | `MDEL` | MEMORY DELTA |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER SPEED MEMORY
    SIZE:          8 LOCATIONS
    S-PAD PARAMETERS:
    --- SCRATCH ---


## VFCL1

`$ENTRY VFCL1`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `C` |  |
| 3 | `K` |  |
| 4 | `N` |  |
| 5 | `ADR` |  |
| 6 | `LOC` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SCRATCH:          SP:0,2,4,6;   DPX: 0  (REL TO DPA)
    DOES C = FUNCTION ( A )


## VFCL2

`$ENTRY VFCL2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 7 | `ADR` |  |
| 8 | `LOC` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SCRATCH:          0,2,4,6,8; DPX:0;  DPY: 0  (REL TO DPA)
    DOES C = FUNCTION ( A , B )


## SPFLT

`$ENTRY SPFLT`


| s-pad | name | meaning |
|---|---|---|
| 1 | `NN` |  |
| 14 | `C27` |  |
| 15 | `NM` |  |


    SCRATCH:  S-PAD 16,17;  DPX 1 (REL TO DPA); TM


## SPUFLT

`$ENTRY SPUFLT`


| s-pad | name | meaning |
|---|---|---|
| 15 | `C27` | TEMP |
| 15 | `NM` | INTEGER TO BE FLOATED |


    ---ABSTRACT---
    FORMULA:    DPX(1) = FLOAT( SP(17) ) WHERE SP(17) IS TREATED AS
    EQUIPMENT: AP WITH EITHER SPEED MEMORY
    SIZE:      8 WORDS
    S-PAD PARAMETERS:
    SCRATCH:  SP(17),DPX(1),DPY(0),FA,TM


## SAVESP

`$ENTRY SAVESP`


| s-pad | name | meaning |
|---|---|---|
| 0 | `N` | SAVED IN DPX(-1) |
| 1 | `J` | SAVED IN DPX(-2) |
| 2 | `RADR` | SAVED IN DPX(-3) |


    --- ABSTRACT ---
    DATAPADS (-3 TO -1) ARE NOW SCRATCHED.
    SIZE:   27. WORDS
    SCRATCH:  DPX( -3 TO 0 )


## SAVSP0

`$ENTRY SAVSP0`


| s-pad | name | meaning |
|---|---|---|
| 14 | `J` |  |
| 15 | `RADR` |  |


    --- ABSTRACT ---
    SIZE:  11 WORDS


## SETSP

`$ENTRY SETSP`


| s-pad | name | meaning |
|---|---|---|
| 12 | `J` | POINTER TO S-PAD TO BE LOADED. |
| 13 | `N` | LOOP CONTROL |
| 14 | `TEMP` | USED FOR 1 LEVEL OF INDIRECT LOAD OF VARIABLES. |
| 15 | `RADR` | POINTER TO PARAMETER LIST IN PS. |


    --- ABSTRACT ---
    IF THE LAST FOUR SPADS ARE NOT SET, THEY ARE USED AS SCRATCH BY THIS ROUTINE.
    SCRATCH:  DPX( -4 TO 0 )
    SIZE:  47. WORDS
    SIZE OF CALL: (FOR N-PARAMETERS):
    SIZE OF CALL: 1 WORD


## SPNEG

`$ENTRY SPNEG`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` |  |


    --- ABSTRACT ---
    SIZE:  2 WORD
    --- SCRATCH ---


## SPNOT

`$ENTRY SPNOT`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` |  |


    --- ABSTRACT ---
    SIZE:  1 WORD
    --- SCRATCH ---


## SPADD

`$ENTRY SPADD`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  1 WORD
    --- SCRATCH ---


## SPSUB

`$ENTRY SPSUB`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  1 WORD
    --- SCRATCH ---


## SPRS

`$ENTRY SPRS`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  5 WORD
    --- SCRATCH ---


## SPLS

`$ENTRY SPLS`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  5 WORD
    --- SCRATCH ---


## SPAND

`$ENTRY SPAND`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  1 WORD
    --- SCRATCH ---


## SPOR

`$ENTRY SPOR`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `B` |  |


    --- ABSTRACT ---
    SIZE:  1 WORD
    --- SCRATCH ---


## SSDM

`$ENTRY SSDM`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A1` |  |
| 0 | `A2` |  |
| 0 | `E1` |  |
| 0 | `E2` |  |
| 1 | `B1` |  |
| 1 | `B2` |  |
| 1 | `F1` |  |
| 1 | `F2` |  |
| 2 | `C1` |  |
| 2 | `C2` |  |
| 3 | `D1` |  |
| 3 | `D2` |  |
| 15 | `EX` |  |


    DOES A*B WHERE A AND B ARE SINGLE PRECISION NUMBERS.
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          81 LOCATIONS(TOTAL) = 33 + DDDA (48)
    SCRATCH:
    DDDA DOES A DOUBLE PRECISION ADD E1 + E2 + F1 + F2 >= A1 + A2


## DDDM

`$ENTRY DDDM`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A1` |  |
| 0 | `A2` |  |
| 0 | `E1` |  |
| 0 | `E2` |  |
| 0 | `HP1` |  |
| 0 | `HP2` |  |
| 1 | `B` |  |
| 1 | `B1` |  |
| 1 | `B2` |  |
| 1 | `F1` |  |
| 1 | `F2` |  |
| 2 | `C1` |  |
| 2 | `C2` |  |
| 3 | `D1` |  |
| 3 | `D2` |  |
| 15 | `EX` | SCRATCH PAD FOR EXPONENT |


    DOES THE DOUBLE PRECISION MULTIPLY OF TWO DOUBLE PRECISION NUMBERS.
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          117 LOCATIONS(TOTAL) = 41 + DDDA (48) + SDDA (28)
    DOES A*B WHERE A AND B ARE DOUBLE PRECISION NUMBERS.
    SCRATCH:
    DDDA DOES A DOUBLE PRECISION ADD E1 + E2 + F1 + F2 >= HP1 + HP2


## SSDA

`$ENTRY SSDA`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | FOR DPX(A) |
| 0 | `B` | FOR DPY(B) |
| 1 | `C` |  |
| 2 | `S1` | DPX(S1) IS HIGH WORD OF SUM |
| 2 | `S2` | DPY(S2) IS LOW WORD OF SUM |


    DOES THE DOUBLE PRECISION ADDITION OF TWO SINGLE PRECISION NUMBERS
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          10 LOCATIONS
    SCRATCH:


## SDDA

`$ENTRY SDDA`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A1` | HIGH WORD OF A |
| 0 | `A2` | LOW WORD OF A |
| 0 | `S1` | HIGH WORD OF SUM |
| 0 | `S2` | LOW WORD OF SUM |
| 1 | `B` |  |
| 2 | `C1` |  |
| 2 | `C2` |  |
| 3 | `D1` |  |
| 3 | `D2` |  |


    DOES THE DOUBLE PRECISION ADDITION OF A SINGLE PRECISION NUMBER
    DOES A + B >= S
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          28 LOCATIONS
    SCRATCH:


## DDDA

`$ENTRY DDDA`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A1` | HIGH WORD OF A |
| 0 | `A2` | LOW WORD OF A |
| 0 | `S1` | HIGH WORD OF SUM |
| 0 | `S2` | LOW WORD OF SUM |
| 1 | `B1` | HIGH WORD OF B |
| 1 | `B2` | LOW WORD OF B |
| 1 | `F1` |  |
| 1 | `F2` |  |
| 2 | `C1` |  |
| 2 | `C2` |  |
| 2 | `G` |  |
| 2 | `H` |  |
| 3 | `D1` |  |
| 3 | `D2` |  |


    DOES DOUBLE PRECISION ADDITION OF A + B
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          48 LOCATIONS
    SCRATCH:


## APNOP

`$ENTRY APNOP, 0`


_No `$EQU` parameter block found._


_The header states no formula, size or abstract._

