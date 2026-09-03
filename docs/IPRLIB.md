# IPRSRC -- routine reference

**Reconstructed from `[327,010]IPRSRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [GRAD2D](#grad2d) | GRAD2D | 12 | 17 |
| [GRD2DB](#grd2db) | GRD2DB | 15 | 16 |
| [LAPL2D](#lapl2d) | LAPL2D | 15 | 16 |
| [LPL2DB](#lpl2db) | LPL2DB | 16 | 16 |
| [MED2D](#med2d) | MED2D | 15 | 15 |
| [CONV2D](#conv2d) | CONV2D | 17 | 16 |
| [MOVREP](#movrep) | MOVREP | 13 | 16 |
| [RFFT2D](#rfft2d) | RFFT2D | 4 | 17 |
| [CFFT2D](#cfft2d) | CFFT2D | 4 | 14 |
| [ERFFT2](#erfft2) | ERFFT2 | 7 | 11 |
| [ECFFT2](#ecfft2) | ECFFT2 | 7 | 11 |
| [ECVMOV](#ecvmov) | ECVMOV | - | 5 |
| [EXUTIL](#exutil) | UNESPF | - | 0 |

13 routines.


## GRAD2D

`$ENTRY GRAD2D, 12`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `CB` |  |
| 1 | `MA` |  |
| 1 | `RHD` |  |
| 2 | `IA` |  |
| 2 | `MID` |  |
| 3 | `JA` |  |
| 3 | `LB` |  |
| 4 | `C` |  |
| 5 | `MC` |  |
| 6 | `IC` |  |
| 7 | `JC` |  |
| 8 | `M` |  |
| 9 | `N` |  |
| 10 | `K` |  |
| 11 | `APT` |  |
| 12 | `CPT` |  |


    ---ABSTRACT---
    CALL GRAD2D(A,MA,NA,IA,JA,C,MC,IC,JC,M,N)
    EQUIPMENT: STANDARD OR FAST MEMORY
    SIZE: 58 + SPMUL (14) = 72 LOCATIONS
    SCRATCH: SPAD=(0-14,16-17)


## GRD2DB

`$ENTRY GRD2DB, 15`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SP0 BECOMES A'(P,Q), INCREMENTED |
| 1 | `MA` | SP1 BECOMES DECREMENTED ROW COUNTER M(I) |
| 2 | `NA` | SP2 REMAIMS NA, # A COLUMNS |
| 3 | `IA` | SP3 BECOMES IA+M FOR TOP TEST |
| 4 | `JA` | SP4 BECOMES JA+N FOR LH TEST |
| 5 | `C` | SP5 BECOMES N, # COLUMNS TO BE PROCESSED |
| 6 | `MC` | SP6 REMAINS # C ROWS |
| 7 | `NC` | SP7 REMAINS # C COLUMNS |
| 8 | `IC` | SP10 BECOMES IA-MA+M+1 FOR BOTTOM TEST |
| 9 | `JC` | SP11 BECOMES JA-NN+N+1 FOR RH TEST |
| 10 | `M` | SP12 REMAINS # ROWS TO BE PROCESSED |
| 11 | `N` | SP13 BECOMES DECREMENTED COLUMN COUNTER |
| 12 | `MCM` | SP14 BECOMES MC-M RFOR NEW COLUMN JUMP |
| 13 | `TMPMA` | SP15 IS TEMPORARY MA, # A ROWS |
| 14 | `ATOP` | SP16 IS TOP-OF-COLUMN,A',INCREMENTED |
| 15 | `CADDR` | SP17 IS INCREMENTED C' ADDRESS |


    ---ABSTRACT---
    OVERSIZED INPUT IMAGES WILL ALLOW FOR THIS CASE.
    CALL GRD2DB(A,MA,NA,IA,JA,C,MC,NC,IC,JC,M,N,B)
    EQUIPMENT: FAST MEMORY
    SIZE: 339 + SPMUL (14) =353 LOCATIONS
    SCRATCH: ALL SPADS,ALL DPADS


## LAPL2D

`$ENTRY LAPL2D, 15`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SP0 BECOMES A'(I),INCREMENTIN |
| 1 | `MA` | SP1 BECOMES M(I), INCREMENTIN |
| 2 | `NA` | SP2 BECOMES IX*MA-IX, ADDRESS |
| 3 | `IA` |  |
| 4 | `JA` |  |
| 5 | `C` |  |
| 6 | `MC` | SP 6 BECOMES MC-M FOR C COL JUMPS |
| 7 | `NC` | SP 7 BECOMES IX*MA,ADDRESS JUMP |
| 8 | `IC` |  |
| 9 | `JC` |  |
| 10 | `M` |  |
| 11 | `N` | SP13 BECOMES N(I),COLUMN COUN |
| 12 | `IX` | SP14 REMAINS IX |
| 13 | `MAM` | SP15 BECOMES MA-M, FOR CHANGIN |
| 14 | `IXMX` | SP16 BECOMES IX*MA+IX FOR ADRE |
| 15 | `CI` | SP17 BECOMES C'(I),INCREMENTIN |


    ---ABSTRACT---
    CALL LAPL2D(A,MA,NA,IA,JA,C,MC,NC,IC,JC,M,N,IX)
    EQUIPMENT: FAST OR STANDARD MEMORY
    SIZE: 62 + SPMUL (14) = 76 LOCATIONS
    SCRATCH: ALL SPADS,DPX(O,1),DPY(0,1)


## LPL2DB

`$ENTRY LPL2DB, 16`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SP0 BECOMES A'(I),INCREMENTIN |
| 1 | `MA` | SP1 BECOMES M(I), INCREMENTIN |
| 2 | `NA` | SP2 BECOMES IX*MA-IX, ADDRESS |
| 3 | `IA` | SP3 BECOMES IA-IX, FOR TOP TE |
| 4 | `JA` | SP4 BECOMES JA-IX, FOR LH TES |
| 5 | `C` | SP5 BECOMES N, FOR LH & RH TE |
| 6 | `MC` | SP6 BECOMES MC-M, TO CHG COLS |
| 7 | `NC` | SP7 BECOMES IX*MA, ADDRESS JU |
| 8 | `IC` | SP10 BECOMES IA-MA+IX, FOR BO |
| 9 | `JC` | SP11 BECOMES JA-NA+IX, FOR RH |
| 10 | `M` | SP12 REMAINS M FOR TOP AND BO |
| 11 | `N` | SP13 BECOMES N(I),COLUMN COUN |
| 12 | `IX` | SP14 REMAINS IX |
| 13 | `MAM` | SP15 BECOMES MA-M, FOR CHANGIN |
| 14 | `IXMX` | SP16 BECOMES IX*MA+IX FOR ADRE |
| 15 | `CI` | SP17 BECOMES C'(I),INCREMENTIN |


    ---ABSTRACT---
    OVERSIZED INPUT IMAGES WILL ALLOW FOR THIS CASE.
    CALL LPL2DB(A,MA,NA,IA,JA,C,MC,NC,IC,JC,M,N,IX,B)
    EQUIPMENT: FAST MEMORY
    SIZE: 309 + SPMUL (14) =323 LOCATIONS
    SCRATCH: ALL SPADS,DPX(0,1),DPY(0,1)


## MED2D

`$ENTRY MED2D, 15`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | A'(I) ADDRESS |
| 1 | `MED` | MEDIAN |
| 2 | `V` | VALUE OF A', USED FOR ADDR'G HIST |
| 3 | `VH` | " |
| 4 | `C` | C'(I) ADDRESS |
| 5 | `CJMP` | MC |
| 6 | `AJMP` | A-JMP FOR FILTERING,STEP TO NEXT POINT IN ROW |
| 7 | `FROW` | COUNTER FOR ROW IN FILTER |
| 8 | `N` | N |
| 9 | `NI` | N(I) COLUMN CTR |
| 10 | `AJMP1` | A-JMP FOR NEW COL FOR FIRST POINT IN ROW FILTER |
| 11 | `H` | H |
| 12 | `FCOL` | COL CTR FOR FILTER |
| 13 | `LOADA` | A-JMP TO LOAD NEW COL FOR NORMAL IN-ROW POINT |
| 14 | `S` |  |


    ---ABSTRACT---
    CALL MED2D(A,MA,IA,JA,C,MC,IC,JC,M,N,IX,H,L)
    EQUIPMENT: FAST OR SLOW  MEMORY
    SIZE:187 + SPMUL (14) + SPFLT (5) + VCLR (4 STND, 16 FAST)
    SCRATCH: ALL SPADS,ALL DPADS


## CONV2D

`$ENTRY CONV2D, 17`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | A |
| 1 | `AADDR` | MA |
| 2 | `IA` | IA |
| 3 | `JA` | JA |
| 4 | `M0` | M |
| 5 | `B` | N |
| 6 | `N` | B |
| 7 | `MB` | MB |
| 8 | `NB` | NB |
| 9 | `NI` | B0 |
| 10 | `CADDR` | C |
| 11 | `MC` | MC |
| 12 | `PNTJMP` | IC |
| 13 | `MBI` | JC |
| 14 | `R` | R |
| 15 | `SCR` |  |


    CALL CONV2D(A,MA,IA,JA,M,N,B,MB,NB,B0,C,MC,IC,JC,R)
    R = 1 IF CORRELATION IS DESIRED
    = 0 IF CONVOLUTION IS DESIRED
    EQUIPMENT: FAST OR SLOW MEMORY
    SIZE: 406  (BASE 8)       (167NS MEMORY)
    SCRATCH: ALL SPADS,ALL DPADS
    0    SCRATCH         SCRATCH
    1    SCRATCH         SCRATCH


## MOVREP

`$ENTRY MOVREP, 13`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | A |
| 1 | `AJMP` | MA |
| 2 | `IA` | IA |
| 3 | `JA` | JA |
| 4 | `C` | C |
| 5 | `CJMP` | MC |
| 6 | `MA` | IC |
| 7 | `MC` | JC |
| 8 | `M` | M |
| 9 | `N` | N |
| 10 | `T` | T |
| 11 | `ROW` |  |
| 12 | `LEVEL` |  |
| 13 | `LASTA` |  |
| 14 | `LASTC` |  |
| 15 | `TEMP` |  |


    ----------ABSTRACT----------
    CALL MOVREP(A,MA,IA,JA,C,MC,IC,JC,M,N,T)
    EQUIPMENT: FAST OR STANDARD MEMORY
    SIZE:129 (BASE 8)        (167 NS MEMORY)


## RFFT2D

`$ENTRY RFFT2D, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ARRAY BASE ADDRESS |
| 0 | `AFFT` | BASE ADDRESS OF FFT |
| 0 | `L` | LEFT HALF FLAG |
| 1 | `N` | NUMBER OF POINTS OF FFT |
| 1 | `N1` | LENGTH OF ROWS |
| 2 | `DI` | SPACING OF FFT |
| 2 | `N2` | LENGTH OF COLUMNS = # ROWS |
| 3 | `F` | FORWARD - INVERSE FFT FLAG |
| 4 | `J` | COUNTS ROWS OR COLUMNS |
| 4 | `K` | INCREMENT FOR MOV |
| 5 | `AN` | ADDRESS FOR START OF ROW OR COLUMN |
| 6 | `C` | ADDRESS FOR MOV |
| 6 | `MDEL` | MEMORY INCREMENT |
| 7 | `D` | ADDRESS FOR MOV |
| 7 | `LN` | NUMBER OF ELEMENTS = MDEL*N1 OR MDEL*N2 |
| 8 | `NCTR` | NUMBER OF POINTS IN FFT |
| 1024 | `R` | RIGHT HALF FLAG |


    --- ABSTRACT ---
    DOES AN IN PLACE TWO DIMENSIONAL REAL FFT WHOSE
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          64 PS WORDS
    THE FOLLOWING ARE SCRATCH


## CFFT2D

`$ENTRY CFFT2D, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF ARRAY |
| 0 | `AFFT` | BASE ADDRESS OF FFT |
| 0 | `L` | LEFT HALF FLAG |
| 1 | `N` | NUMBER OF POINTS OF FFT |
| 1 | `N1` | LENGTH OF ROWS = # COLUMNS |
| 2 | `DI` | SPACING OF FFT |
| 2 | `N2` | LENGTH OF COLUMNS = # ROWS |
| 3 | `F` | FORWARD - INVERSE FFT FLAG |
| 4 | `J` | COUNTS ROWS OR COLUMNS |
| 5 | `AN` | ADDRESS FOR START OF ROW OR COLUMN |
| 6 | `MDEL` | MEMORY INCREMENT |
| 7 | `LN` | NUMBER OF ELEMENTS = MDEL*N1 OR MDEL*N2 |
| 8 | `NCTR` | NUMBER OF POINTS IN FFT |
| 1024 | `R` | RIGHT HALF FLAG |


    --- ABSTRACT ---
    DOES AN IN PLACE TWO DIMENSIONAL COMPLEX FFT WHOSE
    EQUIPMENT:             AP-120B
    SIZE:                  36 PROGRAM LOCATIONS
    THE FOLLOWING ARE SCRATCH:
    SCRATCH (TOTAL) :


## ERFFT2

`$ENTRY ERFFT2, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CH` | SOURCE ARRAY BASE ADDRESS (PAGE NUMBER) |
| 0 | `L` | LEFT HALF FLAG |
| 1 | `CL` | SOURCE ARRAY BASE ADDRESS (WITHIN PAGE) |
| 2 | `N1` | LENGTH OF ROWS = # OF COLUMNS |
| 3 | `N2` | LENGTH OF COLUMNS = # OF ROWS |
| 4 | `F` | FORWARD-INVERSE FFT FLAG |
| 5 | `XH` | WORK VECTOR BASE ADDRESS (PAGE NUMBER) |
| 6 | `XL` | WORK VECTOR BASE ADDRESS (WITHIN PAGE) |
| 7 | `J` | COUNTS NUMBER OF ROWS OR COLUMNS |
| 8 | `TN1` | STORAGE FOR COMPLEX COLUMN COUNT |
| 1024 | `R` | RIGHT HALF FLAG |


    --- ABSTRACT ---
    C = 65536*CH + CL.
    THE FOLLOWING ARE SCRATCH NAMES FOR S-PAD


## ECFFT2

`$ENTRY ECFFT2, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `CH` | SOURCE ARRAY BASE ADDRESS (PAGE NUMBER) |
| 0 | `L` | LEFT HALF FLAG |
| 1 | `CL` | SOURCE ARRAY BASE ADDRESS (WITHIN PAGE) |
| 2 | `N1` | LENGTH OF ROWS = # OF COLUMNS |
| 3 | `N2` | LENGTH OF COLUMNS = # OF ROWS |
| 4 | `F` | FORWARD-INVERSE FFT FLAG |
| 5 | `XH` | WORK VECTOR BASE ADDRESS (PAGE NUMBER) |
| 6 | `XL` | WORK VECTOR BASE ADDRESS (WITHIN PAGE) |
| 7 | `J` | COUNTS NUMBER OF ROWS OR COLUMNS |
| 8 | `CN` | STORES BASE ADDRESS |
| 1024 | `R` | RIGHT HALF FLAG |


    --- ABSTRACT ---
    C = 65536*CH + CL.
    THE FOLLOWING ARE SCRATCH NAMES FOR S-PAD


## ECVMOV

`$ENTRY ECVMOV`


| s-pad | name | meaning |
|---|---|---|
| 0 | `AA` |  |
| 0 | `II` |  |
| 1 | `CC` |  |
| 1 | `KK` |  |
| 14 | `TN` | DUMMY ELEMENT COUNT |


    ---ABSTRACT---
    FORMULA:       C(MK) = A(MI)
    EQUIPMENT:     AP-120B WITH FAST MEMORY
    SIZE:          8 PS WORDS
    S-PAD PARAMETERS
    SCRATCH:       SP(16), DPX(0), DPY(0).
    SCRATCH:       SP: 14; DPX: 0; DPY(0), TM,FA,FM


## EXUTIL

`$ENTRY UNESPF`


_No `$EQU` parameter block found._


    ---ABSTRACT---
    FORMULA: DPX(1) = 100663296. + 65536*SP(16) + SP(17)
    FORMULA:  DPX(1) = FLOAT ( 65536*SP(16) + SP(17) )
    FORMULA:  DPX(1) = FLOAT ( SP(17) )   WHERE SP(17) IS TREATED AS
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 15 + SPFLT (5) = 20 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH:  SP(14,15),DPX(0-2),FA,TM

