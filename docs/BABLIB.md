# BABSRC -- routine reference

**Reconstructed from `[327,010]BABSRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [VMAX](#vmax) | VMAX | 7 | 10 |
| [VMIN](#vmin) | VMIN | 7 | 10 |
| [LVGT](#lvgt) | LVGT | 7 | 8 |
| [LVGE](#lvge) | LVGE | 7 | 8 |
| [LVEQ](#lveq) | LVEQ | 7 | 8 |
| [LVNE](#lvne) | LVNE | 7 | 8 |
| [LVNOT](#lvnot) | LVNOT | 5 | 6 |
| [VLMERG](#vlmerg) | VLMERG | 9 | 10 |
| [VMAXMG](#vmaxmg) | VMAXMG | 7 | 8 |
| [VMINMG](#vminmg) | VMINMG | 7 | 8 |
| [VCLIP](#vclip) | VCLIP | 7 | 8 |
| [VICLIP](#viclip) | VICLIP | 7 | 8 |
| [VLIM](#vlim) | VLIM | 7 | 8 |
| [VFIX](#vfix) | VFIX | 5 | 8 |
| [VFLT](#vflt) | VFLT | 5 | 7 |
| [VSMAFX](#vsmafx) | VSMAFX | 7 | 1 |
| [VSEFLT](#vseflt) | VSEFLT | 5 | 8 |
| [VSHFX](#vshfx) | VSHFX | 6 | 8 |
| [VSCALE](#vscale) | VSCALE | 7 | 10 |
| [VSCSCL](#vscscl) | VSCSCL | 6 | 11 |
| [XVSCAL](#xvscal) | XVSCAL | 10 | 11 |
| [XVSCSC](#xvscsc) | XVSCSC | 7 | 12 |
| [VFLT32](#vflt32) | VFLT32 | 5 | 16 |
| [VFIX32](#vfix32) | VFIX32 | 5 | 14 |
| [VUP16](#vup16) | VUP16 | 5 | 17 |
| [VUPS16](#vups16) | VUPS16 | 5 | 21 |
| [VPK16](#vpk16) | VPK16 | 5 | 17 |
| [VUP8](#vup8) | VUP8 | 5 | 20 |
| [VUPS8](#vups8) | VUPS8 | 5 | 24 |
| [VPK8](#vpk8) | VPK8 | 5 | 21 |
| [MTRANS](#mtrans) | MTRANS | 6 | 1 |
| [SOLVEQ](#solveq) | SOLVEQ | 7 | 36 |
| [XSOLVE](#xsolve) | XSOLVE | 10 | 37 |
| [FMMM](#fmmm) | FMMM | 6 | 1 |
| [FMMM32](#fmmm32) | FMMM32 | 6 | 1 |
| [MMUL](#mmul) | MMUL | 9 | 1 |
| [MMUL32](#mmul32) | MMUL32 | 9 | 1 |
| [MVML3](#mvml3) | MVML3 | 9 | 1 |
| [MVML4](#mvml4) | MVML4 | 9 | 1 |
| [MATINV](#matinv) | MATINV | 2 | 1 |
| [XMATIN](#xmatin) | XMATIN | 3 | 1 |
| [CTRN3](#ctrn3) | CTRN3 | 9 | 1 |
| [RFFT](#rfft) | RFFT | 3 | 4 |
| [RFFTB](#rfftb) | RFFTB | 4 | 5 |
| [CFFT](#cfft) | CFFT | 3 | 12 |
| [CFFTB](#cfftb) | CFFTB | 4 | 14 |
| [RFFTSC](#rfftsc) | RFFTSC | 4 | 12 |
| [CFFTSC](#cfftsc) | CFFTSC | 2 | 8 |
| [CONV](#conv) | CONV | 8 | 17 |
| [VPOLY](#vpoly) | VPOLY | 8 | 1 |
| [DEQ22](#deq22) | DEQ22 | 6 | 14 |
| [VSUM](#vsum) | VSUM | 6 | 7 |
| [VTRAPZ](#vtrapz) | VTRAPZ | 6 | 7 |
| [VSIMPS](#vsimps) | VSIMPS | 6 | 7 |
| [SETC5](#setc5) | SETC5 | 0 | 1 |
| [RDC5](#rdc5) | RDC5 | 1 | 2 |
| [DAREAD](#daread) | DAREAD | 1 | 2 |
| [XDAREA](#xdarea) | XDAREA | 2 | 3 |
| [DAWRIT](#dawrit) | DAWRIT | 2 | 3 |
| [MDCOM](#mdcom) | MDCOM | 2 | 3 |

60 routines.


## VMAX

`$ENTRY VMAX, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | VECTOR B ORIGIN |
| 3 | `J` | VECTOR B INCREMENT |
| 4 | `C` | VECTOR C ORIGIN |
| 5 | `K` | VECTOR C INCREMENT |
| 6 | `N` | VECTOR LENGTH |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE: 14 + SPUFLT (8) = 22 WORDS
    S-PAD PARAMETERS:
    SCRATCH:


## VMIN

`$ENTRY VMIN, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | VECTOR B ORIGIN |
| 3 | `J` | VECTOR B INCREMENT |
| 4 | `C` | VECTOR C ORIGIN |
| 5 | `K` | VECTOR C INCREMENT |
| 6 | `N` | VECTOR LENGTH |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE: 14 + SPUFLT (8) = 22 WORDS
    S-PAD PARAMETERS:
    SCRATCH:


## LVGT

`$ENTRY LVGT, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 106 | `BITMAP` |  |


    THIS ALGORITHM DOES    C(mK) = 1.0  IF  A(mI)>B(mJ)
    C(mK) = 0.0  IF  A(mI)=<B(mJ)
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       15 + SPUFLT (8) = 23 WORDS
    --------SCRATCH--------


## LVGE

`$ENTRY LVGE, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 106 | `BITMAP` |  |


    THIS ALGORITHM DOES    C(mK) = 1.0  IF  A(mI)=>B(mJ)
    C(mK) = 0.0  IF  A(mI)<B(mJ)
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       15 + SPUFLT (8) = 23 WORDS
    --------SCRATCH--------


## LVEQ

`$ENTRY LVEQ, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 106 | `BITMAP` |  |


    THIS ALGORITHM DOES    C(mK) = 1.0  IF  A(mI)=B(mJ)
    C(mK) = 0.0  IF  A(mI)not=B(mJ)
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       15 + SPUFLT (8) = 23 WORDS
    --------SCRATCH--------


## LVNE

`$ENTRY LVNE, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 106 | `BITMAP` |  |


    THIS ALGORITHM DOES    C(mK) = 1.0  IF  A(mI)not=B(mJ)
    C(mK) = 0.0  IF  A(mI)=B(mJ)
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       15 + SPUFLT (8) = 23 WORDS
    --------SCRATCH--------


## LVNOT

`$ENTRY LVNOT, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `C` |  |
| 3 | `K` |  |
| 4 | `N` |  |
| 26 | `BITMAP` |  |


    THIS ALGORITHM DOES    C(mK) = 1.0  IF  A(mI)=0.0
    C(mK) = 0.0  IF  A(mI)not=0.0
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       13 + SPUFLT (8) = 21 WORDS
    --------SCRATCH--------


## VLMERG

`$ENTRY VLMERG, 9`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `D` |  |
| 7 | `L` |  |
| 8 | `N` |  |
| 426 | `BITMAP` |  |


    THIS ALGORITHM DOES    D(mL) = A(mI)  IF  C(mK)not=0.0
    D(mL) = B(mJ)  IF  C(mK)=0.0
    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:       15 + SPUFLT (8) = 23 WORDS
    --------SCRATCH--------


## VMAXMG

`$ENTRY VMAXMG, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK) = MAX ( ABS(A(MI)), ABS(B(MJ)) ) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL VMAXMG(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0,1),DPY(0,1),FA,MD


## VMINMG

`$ENTRY VMINMG, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK) = MIN ( ABS(A(MI)), ABS(B(MJ)) ) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL VMINMG(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0,1),DPY(0,1),FA,MD


## VCLIP

`$ENTRY VCLIP, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | ADDRESS OF SMALLER SCALAR |
| 3 | `C` | ADDRESS OF LARGER SCALAR |
| 4 | `D` | BASE ADDRESS OF DESTINATION VECTOR |
| 5 | `L` | INCREMENT BETWEEN ELEMENTS OF D |
| 6 | `N` | NUMBER OF ELEMENTS IN D |
| 98 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  D(ML) = B      IF A(MI)<B
    = A(MI)  IF B<=A(MI)<=C
    = C      IF A(MI)>C
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 16 LOCATIONS
    FORTRAN: CALL VCLIP(A,I,B,C,D,L,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,4,6),DPX(0,1),DPY(0),FA,FM,MD,TM


## VICLIP

`$ENTRY VICLIP, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | ADDRESS OF SMALLER SCALAR |
| 3 | `C` | ADDRESS OF LARGER SCALAR |
| 4 | `D` | BASE ADDRESS OF DESTINATION VECTOR |
| 5 | `L` | INCREMENT BETWEEN ELEMENTS OF D |
| 6 | `N` | NUMBER OF ELEMENTS IN D |
| 98 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  D(ML) = A(MI)  IF A(MI)<B
    = B      IF B<=A(MI)<0
    = C      IF 0<=A(MI)<C
    = A(MI)  IF A(MI)>C  FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 19 LOCATIONS
    FORTRAN: CALL VICLIP(A,I,B,C,D,L,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,4,6),DPX(0,1),DPY(0),FA,FM,MD,TM


## VLIM

`$ENTRY VLIM, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | ADDRESS OF SCALAR TO COMPARE WITH SOURCE |
| 3 | `C` | ADDRESS OF SCALAR TO SET INTO DESTINATION |
| 4 | `D` | BASE ADDRESS OF DESTINATION VECTOR |
| 5 | `L` | INCREMENT BETWEEN ELEMENTS OF D |
| 6 | `N` | NUMBER OF ELEMENTS IN D |
| 98 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  D(ML) = -C      IF A(MI)<B
    = C      IF A(MI)>=B
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL VLIM(A,I,B,C,D,L,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,4,6),DPX(0,1),DPY(0),FA,MD


## VFIX

`$ENTRY VFIX, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT OF VECTOR A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `C` | BASE ADDRESS FOR VECTOR C |
| 3 | `K` | INCREMENT FOR VECTOR C |
| 4 | `N` | ELEMENT COUNT |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  10  + SPUFLT (8) = 18 WORDS


## VFLT

`$ENTRY VFLT, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `C` |  |
| 3 | `K` |  |
| 4 | `N` |  |
| 13 | `C27` |  |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B, 1 CYCLE MD
    DPX (0,1) (SCRATCH)
    SP(0,2,4,15) (SCRATCH)


## VSMAFX

`$ENTRY VSMAFX, 7`


| s-pad | name | meaning |
|---|---|---|
| 98 | `BITMAP` |  |


    ---ABSTRACT---
    D(MK) = FIX (A(MI)*B + C)
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE: 14
    FORTRAN: CALL VSMAFX(A,I,B,C,D,K,N)
    S-PAD PARAMETERS:
    ---SCRATCH---


## VSEFLT

`$ENTRY VSEFLT, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR OF INTEGERS |
| 1 | `I` | ADDRESS INCREMENT OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR |
| 3 | `K` | ADDRESS INCREMENT OF C |
| 4 | `N` | ELEMENT COUNT |
| 14 | `EY` |  |
| 15 | `C27` |  |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA:  C(MK) = FLOAT (SIGN EXTEND (A(MI)) )  FOR M=0 TO N-1
    EQUIPMENT:  AP120B WITH EITHER SPEED MD MEMORY
    SIZE:       15
    FORTRAN CALL:  CALL VSEFLT(A,I,C,K,N)
    SCRATCH:       SP(0,2,4,14,15),DPX(0),DPY(0,1),FA,MD,TM
    ENTER WITH FOLLOWING S-PAD PARAMETERS:


## VSHFX

`$ENTRY VSHFX, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `C` | BASE ADDRESS OF C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT FOR C |
| 5 | `SHFT` | SHIFT (POWER OF 2 MULTIPLY) DESIRED BEFORE FIXING |
| 6 | `T` |  |
| 58 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B
    SIZE:             10. LOCATIONS
    SCRATCH:          S-PAD:  0,2,4,6
    S-PAD PARAMETERS:
    SCRATCH S-PAD:


## VSCALE

`$ENTRY VSCALE, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | ADDRESS OF B(0) |
| 3 | `C` | BASE ADDRESS OF C |
| 4 | `K` | INCREMENT FOR C |
| 5 | `N` | ELEMENT COUNT FOR C |
| 6 | `WIDTH` | WIDTH OF DESIRED INTEGERS: 2-28 |
| 7 | `T` |  |
| 15 | `MAX` |  |
| 114 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             14. LOCATIONS
    SCRATCH:          S-PAD:  0,3,5,7,10  (OCTAL)
    S-PAD PARAMETERS:
    IN THE SPECIFIED INTEGER SIZE
    SCRATCH S-PAD REGISTERS:


## VSCSCL

`$ENTRY VSCSCL, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `C` | BASE ADDRESS OF C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT FOR C |
| 5 | `WIDTH` | WIDTH OF DESIRED INTEGERS: 2-28 |
| 12 | `PTR` |  |
| 13 | `T` |  |
| 14 | `CTR` |  |
| 15 | `MAX` | THIS CONTAINS THE LARGEST EXPONENT FOUND |
| 58 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             21. LOCATIONS
    SCRATCH:  SP: 0,2,4,12.-15.
    S-PAD PARAMETERS:
    IN THE SPECIFIED INTEGER SIZE
    AS THE MAXIMUM EXPONENT SIZE TO BE SCALED TO FIT IN THE
    SCRATCH S-PAD REGISTERS:


## XVSCAL

`$ENTRY XVSCAL, 10`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | ADDRESS OF B(0) |
| 3 | `C` | BASE ADDRESS OF C |
| 4 | `K` | INCREMENT FOR C |
| 5 | `N` | ELEMENT COUNT FOR C |
| 6 | `WIDTH` | WIDTH OF DESIRED INTEGERS: 2-28 |
| 7 | `IEXP` | MD ADDRESS TO STORE M |
| 8 | `T` |  |
| 15 | `MAX` |  |
| 114 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             15. LOCATIONS
    SCRATCH:          S-PAD:  0,3,5,7,10,17  (OCTAL)
    S-PAD PARAMETERS:
    IN THE SPECIFIED INTEGER SIZE
    SCRATCH S-PAD REGISTERS:


## XVSCSC

`$ENTRY XVSCSC, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `C` | BASE ADDRESS OF C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT FOR C |
| 5 | `WIDTH` | WIDTH OF DESIRED INTEGERS: 2-28 |
| 6 | `IEXP` | ADDRESS TO STORE M |
| 12 | `PTR` |  |
| 13 | `T` |  |
| 14 | `CTR` |  |
| 15 | `MAX` | THIS CONTAINS THE LARGEST EXPONENT FOUND |
| 58 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:        AP-120B WITH EITHER MEMORY
    SIZE:             22. LOCATIONS
    SCRATCH:  SP: 0,2,4,12.-15.
    S-PAD PARAMETERS:
    IN THE SPECIFIED INTEGER SIZE
    AS THE MAXIMUM EXPONENT SIZE TO BE SCALED TO FIT IN THE
    SCRATCH S-PAD REGISTERS:


## VFLT32

`$ENTRY VFLT32, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `NN` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `TE` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 3 | `T4` |  |
| 4 | `N` | VECTOR LENGTH |
| 9 | `E7` |  |
| 10 | `E67` |  |
| 11 | `E10` |  |
| 13 | `EXB` |  |
| 14 | `E33` |  |
| 15 | `EX` |  |
| 15 | `NM` | TEMP STORAGE FOR VECTOR LENGTH |
| 26 | `BITMAP` |  |


    EQUIPMENT:     AP-120B WITH STANDARD OR FAST MEMORY
    SIZE:          61 + SPUFLT (8) = 69 WORDS


## VFIX32

`$ENTRY VFIX32, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 0 | `M026` | MASK TO EXTRACT BITS 0-26 |
| 0 | `M2831` | MASK TO EXTRACT BITS 28-31 |
| 1 | `I` | INCREMENT FOR A |
| 1 | `M27` | MASK TO EXTRACT BIT 27 |
| 1 | `TE` | TEMP FOR EXPONENT BITS |
| 2 | `ANS` | PLACE TO PACK ANSWER |
| 2 | `B27` | BIT 27 (ON) |
| 2 | `C` | BASE ADDRESS OF C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT |
| 14 | `N56` | HOLDS 56 |
| 15 | `E` | HOLD EXPONENT PART |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:     AP-120B WITH EITHER SPEED MAIN MEMORY
    SIZE:          34. WORDS
    S-PAD PARAMETERS:
    SCRATCH:  S-PAD: 0,2,4,16,17


## VUP16

`$ENTRY VUP16, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 1 | `B1` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `NN` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `TA` |  |
| 3 | `B0` |  |
| 3 | `K` | DESTITNATION VECTOR INCREMENT |
| 4 | `N` | SOURCE VECTOR LENGTH |
| 10 | `E33` |  |
| 11 | `K3` |  |
| 12 | `EXB` |  |
| 13 | `E13` |  |
| 14 | `E47` |  |
| 15 | `EX` |  |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:     AP-120B WITH STANDRD OR FAST MEMORY
    SIZE:          56 + SPUFLT (8) = 64 INSTRUCTIONS


## VUPS16

`$ENTRY VUPS16, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 1 | `C0` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `NN` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `TE` |  |
| 3 | `C1` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 4 | `N` | SOURCE VECTOR LENGTH |
| 6 | `K3` |  |
| 7 | `EY` |  |
| 8 | `E33` |  |
| 9 | `E13` |  |
| 10 | `E47` |  |
| 11 | `ENEG` |  |
| 12 | `EBITS` |  |
| 13 | `ET` |  |
| 14 | `EXB` |  |
| 15 | `EX` |  |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:     AP-120B WITH STANDARD OR FAST MEMORY
    SIZE:          51 + SPUFLT (8) = 59 INSTRUCTIONS


## VPK16

`$ENTRY VPK16, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 0 | `ANS` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `TB` |  |
| 2 | `C` | DESTINATION VECTOR ADDRSS |
| 2 | `TE` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 3 | `TA` |  |
| 4 | `N` | VECTOR LENGTH |
| 9 | `E15` |  |
| 10 | `CL` |  |
| 11 | `I3` |  |
| 12 | `E14` |  |
| 13 | `E17` |  |
| 14 | `EXB` |  |
| 15 | `EX` |  |
| 26 | `BITMAP` |  |


    VPK16 DOES NOT CHECK FOR NUMBERS OUT OF RANGE.
    EQUIPMENT:     AP-120B WITH STANDARD OR FAST MEMORY
    SIZE:          52 LOCATIONS


## VUP8

`$ENTRY VUP8, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 0 | `M1` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `M2` |  |
| 1 | `NN` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `M3` |  |
| 2 | `TE` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 3 | `M4` |  |
| 4 | `N` | SOURCE VECTOR LENGTH |
| 9 | `C13` |  |
| 10 | `C23` |  |
| 11 | `C33` |  |
| 12 | `E37` |  |
| 13 | `E3` |  |
| 14 | `EXB` |  |
| 15 | `EX` |  |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:     AP-120B WITH STANDARD OR FAST MEMORY
    SIZE:          64 + SPUFLT (8) = 72 INSTRUCTIONS


## VUPS8

`$ENTRY VUPS8, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 0 | `T1` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `NN` |  |
| 1 | `SB1` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `SB2` |  |
| 2 | `T0` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 3 | `SB3` |  |
| 3 | `T3` |  |
| 4 | `N` | SOURCE VECTOR LENGTH |
| 6 | `E10` |  |
| 7 | `E37` |  |
| 8 | `ET7` |  |
| 9 | `E33` |  |
| 10 | `E23` |  |
| 11 | `E13` |  |
| 12 | `E7` |  |
| 13 | `E3` |  |
| 14 | `EXB` |  |
| 15 | `EX` |  |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:     AP-120B WITH STANDARD OR FAST MEMORY
    SIZE:          100 + SPUFLT (8) = 108 INSTRUCTIONS


## VPK8

`$ENTRY VPK8, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR ADDRESS |
| 0 | `ANS` |  |
| 1 | `I` | SOURCE VECTOR INCREMENT |
| 1 | `LB` |  |
| 2 | `A2` |  |
| 2 | `C` | DESTINATION VECTOR ADDRESS |
| 2 | `TA` |  |
| 3 | `K` | DESTINATION VECTOR INCREMENT |
| 3 | `M3` |  |
| 3 | `TE` |  |
| 4 | `N` | DESTINATION VECTOR LENGTH |
| 6 | `E0` |  |
| 7 | `E15` |  |
| 8 | `E4` |  |
| 9 | `E11` |  |
| 10 | `E14` |  |
| 11 | `E24` |  |
| 13 | `E17` |  |
| 14 | `EXB` |  |
| 15 | `EX` |  |
| 26 | `BITMAP` |  |


    VPK8 DOES NOT CHECK FOR NUMBERS OUT OF RANGE.
    SIZE:          67. LOCATIONS


## MTRANS

`$ENTRY MTRANS, 6`


| s-pad | name | meaning |
|---|---|---|
| 58 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:                  AP-120B
    SIZE:                       18. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## SOLVEQ

`$ENTRY SOLVEQ, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | MATRIX OF COEFFICIENTS |
| 1 | `ADT1` |  |
| 1 | `ADT2` |  |
| 1 | `N` | ORDER OF MATRIX |
| 1 | `PIVI` | INVERSE OF PIVOT |
| 2 | `ADS` |  |
| 2 | `ADX` |  |
| 2 | `ADY` |  |
| 2 | `CTR2` |  |
| 2 | `X` |  |
| 2 | `XMCTR` | FLOATED M |
| 2 | `Y` | MATRIX OF DATA VECTORS |
| 3 | `ADT` |  |
| 3 | `M` | NUMBER OF DATA VECTORS |
| 3 | `XNCTR` | FLOATED NCTR |
| 4 | `ROWADD` | WORK VECTOR FOR ROW ADDRESSES |
| 5 | `XADD` |  |
| 5 | `XIN` | BASE ADDRESS OF SSOLUTION MATRI |
| 5 | `YADD` |  |
| 6 | `CTR1` |  |
| 6 | `STST` | ADDRESS OF SINGULARITY ERROR |
| 7 | `A1` |  |
| 8 | `A2` |  |
| 9 | `SAVEA` |  |
| 10 | `BITMAP` |  |
| 10 | `NN` |  |
| 10 | `SAVADD` |  |
| 11 | `L` |  |
| 11 | `SAVROW` |  |
| 12 | `NCTR` | COUNTS PASSES THROUGH |
| 13 | `SAVEY` |  |
| 13 | `YA` |  |
| 14 | `ADYT` |  |
| 14 | `YROW` |  |
| 15 | `A3` |  |
| 15 | `K` |  |


    EQUIPMENT:     AP 120B WITH FAST MEMORY
    SIZE:          182 + DIV (28) + SPUFLT (8) = 218. AP WORDS
    FORTRAN CALL:  CALL SOLVEQ(A,N,B,M,ROWADD,X,STST)
    SCRATCH:       SP(0-17),DPX(-4 TO 3),DPY(-4 TO 3),FA,FM,MD,TM
    THE FOLLOWING ARE SCRATCH ADDRESSES:
    THE NEXT PART OF THE PROGRAM DOES THE ELIMINATION ON


## XSOLVE

`$ENTRY XSOLVE, 10`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | MATRIX OF COEFFICIENTS |
| 1 | `ADT1` |  |
| 1 | `ADT2` |  |
| 1 | `N` | ORDER OF MATRIX |
| 1 | `PIVI` | INVERSE OF PIVOT |
| 2 | `ADS` |  |
| 2 | `ADX` |  |
| 2 | `ADY` |  |
| 2 | `CTR2` |  |
| 2 | `X` |  |
| 2 | `XMCTR` | FLOATED M |
| 2 | `Y` | MATRIX OF DATA VECTORS |
| 3 | `ADT` |  |
| 3 | `M` | NUMBER OF DATA VECTORS |
| 3 | `XNCTR` | FLOATED NCTR |
| 4 | `ROWADD` | WORK VECTOR FOR ROW ADDRESSES |
| 5 | `XADD` |  |
| 5 | `XIN` | BASE ADDR OF SOLUTION MATRIX |
| 5 | `YADD` |  |
| 6 | `CTR1` |  |
| 6 | `STST` | ADDR OF SINGULARITY TEST VALUE |
| 7 | `A1` |  |
| 7 | `IERR` | ADDRESS OF SINGULARITY FLAG |
| 8 | `A2` |  |
| 9 | `SAVEA` |  |
| 10 | `BITMAP` |  |
| 10 | `NN` |  |
| 10 | `SAVADD` |  |
| 11 | `L` |  |
| 11 | `SAVROW` |  |
| 12 | `NCTR` | COUNTS PASSES THROUGH |
| 13 | `SAVEY` |  |
| 13 | `YA` |  |
| 14 | `ADYT` |  |
| 14 | `YROW` |  |
| 15 | `A3` |  |
| 15 | `K` |  |


    EQUIPMENT:     AP 120B WITH FAST MEMORY
    SIZE:          188. + DIV (28) + SPUFLT (8) = 224. AP WORDS
    FORTRAN CALL:  CALL XSOLVE(A,N,B,M,ROWADD,X,STST,IERR)
    SCRATCH:       SP(0-17),DPX(-4 TO 3),DPY(-4 TO 3),FA,FM,MD,TM
    THE FOLLOWING ARE SCRATCH ADDRESSES:
    THE NEXT PART OF THE PROGRAM DOES THE ELIMINATION ON


## FMMM

`$ENTRY FMMM, 6`


| s-pad | name | meaning |
|---|---|---|
| 56 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:                     AP-120B
    SIZE:                          64. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---
    IN LOOP4.  LOOP1 DOES THE BASIC DOT PRODUCT.  LOOP2


## FMMM32

`$ENTRY FMMM32, 6`


| s-pad | name | meaning |
|---|---|---|
| 56 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:                     AP-120B
    SIZE:                          34. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---
    IN LOOP2, WHICH IS CONTAINED IN LOOP3.  LOOP1 DOES THE BASIC


## MMUL

`$ENTRY MMUL, 9`


| s-pad | name | meaning |
|---|---|---|
| 490 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:    AP-120B WITH EITHER MEMORY
    SCRATCH:      SP(0-15.)


## MMUL32

`$ENTRY MMUL32, 9`


| s-pad | name | meaning |
|---|---|---|
| 490 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SCRATCH:       SP(0-14.), DPY(0), DPA(0- # OF ROWS OF B)
    S-PAD PARAMETERS:


## MVML3

`$ENTRY MVML3, 9`


| s-pad | name | meaning |
|---|---|---|
| 474 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          29. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## MVML4

`$ENTRY MVML4, 9`


| s-pad | name | meaning |
|---|---|---|
| 474 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          40. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## MATINV

`$ENTRY MATINV, 2`


| s-pad | name | meaning |
|---|---|---|
| 2 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:       133. LOCATIONS   PLUS DIVIDE(28.) = 161.
    S-PAD PARAMETERS:
    --- SCRATCH ---
    FROM THE END BACKWARD.  IT DOES NOT COMPUTE (1/PIV)*PIV.
    THIS DOES THE FORWARD ELIMINATION.


## XMATIN

`$ENTRY XMATIN, 3`


| s-pad | name | meaning |
|---|---|---|
| 2 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:       136.  PLUS DIVIDE (28.) = 164. WORDS
    S-PAD PARAMETERS:
    --- SCRATCH ---
    FROM THE END BACKWARD.  IT DOES NOT COMPUTE (1/PIV)*PIV.
    THIS DOES THE FORWARD ELIMINATION.


## CTRN3

`$ENTRY CTRN3, 9`


| s-pad | name | meaning |
|---|---|---|
| 460 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA: D(MLP+QL) = SUM (A(Q+3R) * {B(MJP+RK) - C(R)} ) FOR R=0,1,2
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          37. LOCATIONS
    FORTRAN:  CALL CTRN3(A,B,J,JP,C,D,L,LP,N)
    S-PAD PARAMETERS:
    ---SCRATCH---


## RFFT

`$ENTRY RFFT, 3`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` |  |
| 1 | `N` |  |
| 2 | `F` |  |
| 6 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE:18 LOCS + REALTR (49) + CFFT (187 FAST, 185 STD) = 254 (FAST), 252 (STD)
    --- SCRATCH (OVERALL) ---
    DOES A REAL FFT:
    DIRECT:    DOES FIRST AN N/2 POINT COMPLEX FFT, AND THEN
    INVERSE:   DOES AN N POINT INVERSE REAL TRANSFORM PASS,


## RFFTB

`$ENTRY RFFTB, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `C` |  |
| 2 | `N` |  |
| 3 | `F` |  |
| 12 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:    AP-120B WITH EITHER MEMORY
    SIZE:15 LOCATIONS + REALTR (49) + CFFTB (190) = 254
    --- SCRATCH (OVERALL) ---
    DOES A REAL FFT:
    DIRECT:    DOES FIRST AN N/2 POINT COMPLEX FFT, AND THEN
    INVERSE:   DOES AN N POINT INVERSE REAL TRANSFORM PASS,


## CFFT

`$ENTRY CFFT, 3`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF ARRAY |
| 1 | `N` | # OF COMPLEX POINTS IN THE ARRAY (>1) |
| 2 | `F` | DIRECTION: 1= FORWARD,  -1= INVERSE |
| 6 | `BITMAP` |  |
| 11 | `MINC` | ARRAY INCREMENT BETWEEN REAL ELEMENTS (2) |
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
    SIZE:        21 + FFT2 (16) + FFT4 (79) + STATUS (19) + ADV (7)
    S-PAD PARAMETERS:
    --- SCRATCH (OVERALL) ---
    1.      CALL 'STSTAT'      THIS TAKES 'N' AND 'F', AND SETS THE BIT-REVERSE
    CALL FFT4  (TO DO THE NEXT FFT PASS)
    CALL ADV4  (TO ADVANCE TO THE NEXT PASS)
    5.     WHEN DONE, CALL 'CLSTAT' TO CLEAR THE BIT-REVERSE AND FFT-MODE
    SIZE OF INSTALLED FFT TABLE
    SET AP-STATUS FOR BIT-REVERSE SIZE


## CFFTB

`$ENTRY CFFTB, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE ARRAY |
| 1 | `C` | DESTINATION ARRAY |
| 1 | `NN` | PLACE TO SAVE N |
| 2 | `N` | # OF COMPLEX POINTS IN THE ARRAY(>1) |
| 3 | `F` | DIRECTION: 1= FORWARD,  -1= INVERSE |
| 11 | `MINC` | ARRAY INCREMENT BETWEEN REAL ELEMENTS (2) |
| 12 | `BITMAP` |  |
| 12 | `WD` | W DELTA |
| 13 | `MDEL` | MEMORY DELTA |
| 14 | `FP` | PARAMETER FOR STSTAT (F) |
| 14 | `ICOUNT` | I-LOOP COUNT |
| 15 | `JCOUNT` | J-LOOP COUNT |
| 15 | `M` | FROM STSTAT ( M = LOG2(N) ) |
| 15 | `NP` | FOR STSTAT (N) |


    --- ABSTRACT ---
    DOES A NOT-IN-PLACE COMPLEX FFT WHICH COMBINES THE BIT-REVERSE WITH
    EQUIPMENT:                     AP-120B WITH EITHER MEMORY
    SIZE:         25 + FFT2B (25) + FFT4 (79) + STATUS (19) + FFT4B (43-SET24B(8))
    DOES A COMPLEX FFT WHICH AVOIDS A SEPARATE BIT-REVERSING
    S-PAD PARAMETERS:
    --- SCRATCH (OVERALL) ---
    1.      CALL 'STSTAT'      THIS TAKES 'N' AND 'F', AND SETS THE BIT-REVERSE
    CALL FFT4  (TO DO THE NEXT FFT PASS)
    CALL ADV4  (TO ADVANCE TO THE NEXT PASS)
    6.     WHEN DONE, CALL 'CLSTAT' TO CLEAR THE BIT-REVERSE AND FFT-MODE
    SIZE OF INSTALLED FFT TABLE
    SET AP-STATUS FOR BIT-REVERSE SIZE


## RFFTSC

`$ENTRY RFFTSC, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF DATA |
| 1 | `N` | NUMBER OF ELEMENTS IN C |
| 2 | `F` | FORMATTING FLAG |
| 3 | `FS` | SCALING FLAG |
| 10 | `CC` |  |
| 11 | `NN` |  |
| 12 | `I1` |  |
| 13 | `FT` |  |
| 14 | `BITMAP` |  |
| 14 | `CN` |  |
| 15 | `C1` |  |
| 15 | `TP` |  |


    ---ABSTRACT---
    EQUIPMENT: AP120 WITH EITHER MEMORY
    SIZE: 35 LOCATIONS + DIV (28 LOCATIONS) = 63 LOCATIONS
    FORTRAN: CALL RFFTSC(C,N,F,FS)
    S-PAD PARAMETERS:
    F=2  UNPACK FROM FORMAT I. TO II.
    F=3  UNPACK FROM FORMAT I. TO III.
    F=-2  PACK FROM II. TO I.
    F=-3  PACK FORM III. TO I.
    SCRATCH: SP(12-17), DPX(0), DPY(0), DPA UNCHANGED
    F=3 MEANS N/2 + 1 COMPLEX PAIRS


## CFFTSC

`$ENTRY CFFTSC, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF DATA |
| 1 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 2 | `BITMAP` |  |
| 11 | `CC` |  |
| 12 | `I2` |  |
| 13 | `NN` |  |
| 14 | `CCC` |  |
| 15 | `TP` |  |


    ---ABSTRACT---
    EQUIPMENT: AP120 WITH EITHER MEMORY
    SIZE: 18 LOCATIONS + DIV (28 LOCATIONS) = 46 LOCATIONS
    FORTRAN: CALL CFFTSC(C,N)
    S-PAD PARAMETERS:
    SCRATCH: SP(13-17), DPX(0), DPY(0,1), DPA UNCHANGED


## CONV

`$ENTRY CONV, 8`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR. OF A. |
| 1 | `I` | INC. FOR A. |
| 2 | `B` | BASE ADDR. OF B. |
| 3 | `J` | INC. FOR B. |
| 4 | `C` | BASE ADDR. FOR C |
| 5 | `K` | INC. FOR C. |
| 6 | `N` | NUMBER OF ANSWERS. |
| 7 | `M` | SIZE OF B. |
| 8 | `TT` | THIS WILL CONTAIN THE SIZE OF A FOR ADC. |
| 9 | `SAVEB` |  |
| 10 | `SAVEA` |  |
| 11 | `SAVEM` |  |
| 12 | `JUNK` |  |
| 13 | `ITT` |  |
| 14 | `CCTR` |  |
| 15 | `TF` |  |
| 490 | `BITMAP` |  |


    ---ABSTRACT---
    THIS DOES A CONVOLUTION, WITH THE OPERATOR POINTS IN
    EQUIPMENT:    AP-120B WITH EITHER MEMORY
    L=THE ELEMENT COUNT OF A.THE FORTRAN CALL SHOULD THEN LOOK LIKE:
    CALL FCONV (A,I,B,J,C,K,N,M,L)
    SCRATCH:      SP(0-16.), DPX(0-31), DPY(0-31)
    LOOP1B, WHICH GENERALLY DOES THE SAME THING AS
    S-PAD PARAMETERS:


## VPOLY

`$ENTRY VPOLY, 8`


| s-pad | name | meaning |
|---|---|---|
| 234 | `BITMAP` |  |


    -- ABSTRACT--
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:   37 WORDS
    SCRATCH:       SP(0-9), DPX(-4 TO 0), DPY(-2, -4)


## DEQ22

`$ENTRY DEQ22, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A (LOCATION OF A(0)) |
| 0 | `AM1` | A(I-1) |
| 0 | `B1` | B(1) |
| 1 | `AM2` | A(I-2) |
| 1 | `B2` | B(2) |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF THE 5 COEFFICIENTS (ADDRESS OF |
| 2 | `B3` | B(3) |
| 2 | `CM2` | C(I-2) AND C(M-1) |
| 3 | `B4` | B(4) |
| 3 | `C` | BASE ADDRESS OF DESTINATION VECTOR (ADDRESS OF |
| 4 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 5 | `N` | NUMBER OF ELEMENTS IN THE VECTORS |
| 50 | `BITMAP` |  |


    --- ABSTRACT ---
    DOES A 2 POLE, 2 ZERO RECURSIVE (IIR - INFINITE IMPULSE RESPONSE)
    EQUIPMENT:                     AP-120B WITH EITHER MEMORY
    SIZE:                          25 LOCATIONS
    --- SCRATCH ---
    DOES THE EQUATION:
    S-PAD PARAMETERS:


## VSUM

`$ENTRY VSUM, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 5 | `H` | ADDRESS OF INTEGRATION STEP SIZE H |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    VECTOR MULTIPLIED BY THE INTEGRATION STEP SIZE.  WITH A STEP
    SIZE OF 1.0 THE INTEGRATION SIMPLY PRODUCES A RUNNING SUM OF
    FORMULA:   C(MK)=SUM H*A(LI) FROM L=0 TO M, FOR M=0,1,...,N-1
    ACCURACY: ERROR IS PROPORTIONAL TO H*D WHERE D=MAX(A)
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE:  13 LOCATIONS
    FORTRAN: CALL VSUM(A,I,C,K,N,H)
    S-PAD PARAMETERS
    ---SCRATCH---


## VTRAPZ

`$ENTRY VTRAPZ, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 5 | `H` | ADDRESS OF INTEGRATION STEP SIZE H |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:   C(0)=0.0
    ACCURACY: ERROR IS PROPORTIONAL TO H*H*D WHERE D IS MAX OF
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE:  16 LOCATIONS
    FORTRAN: CALL VTRAPZ(A,I,C,K,N,H)
    S-PAD PARAMETERS
    SCRATCH: SP(0,2,4), DPX(0), DPY(0-1), DPA UNCHANGED


## VSIMPS

`$ENTRY VSIMPS, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 5 | `H` | ADDRESS OF INTEGRATION STEP SIZE H |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA: C(0)=0.0
    ACCURACY:  ERROR IS PROPORTIONAL TO (H**4)*D FOR M EVEN
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 26. LOCATIONS
    FORTRAN: CALL VSIMPS(A,I,C,K,N,H)
    S-PAD PARAMETERS
    ---SCRATCH---


## SETC5

`$ENTRY SETC5, 0`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA: N/A
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 1
    FORTRAN: CALL SETC5
    S-PAD PARAMETERS
    SCRATCH:  NONE


## RDC5

`$ENTRY RDC5, 1`


| s-pad | name | meaning |
|---|---|---|
| 0 | `BITMAP` |  |
| 0 | `C` | DESTINATION ADDRESS FOR STATUS |


    ---ABSTRACT---
    FORMULA: SP(15) AND C(0) = CTL05 BIT
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 8
    FORTRAN: CALL RDC5(C)
    S-PAD PARAMETERS
    SCRATCH:  SP(14,15),DPX(0),DA


## DAREAD

`$ENTRY DAREAD, 1`


| s-pad | name | meaning |
|---|---|---|
| 0 | `DA` | DEVICE ADDRESS |
| 1 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  SP(15) = DEVICE REGISTER (DA)
    EQUIPMENT:  AP120B WITH EITHER MEMORY
    SIZE:       2
    FORTRAN CALL:  CALL DAREAD(DA)
    SCRATCH:       DA
    ENTER WITH FOLLOWING S-PAD PARAMETERS:


## XDAREA

`$ENTRY XDAREA, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `DA` | DEVICE ADDRESS |
| 1 | `BITMAP` |  |
| 1 | `VAL` | MD ADDRESS TO STORE DA |


    ---ABSTRACT---
    FORMULA:  SP(15) = DEVICE REGISTER (DA)
    EQUIPMENT:  AP120B WITH EITHER MEMORY
    SIZE:       3
    FORTRAN CALL:  CALL XDAREA(DA,VAL)
    SCRATCH:       DA
    ENTER WITH FOLLOWING S-PAD PARAMETERS:


## DAWRIT

`$ENTRY DAWRIT, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `DA` | DEVICE ADDRESS |
| 1 | `VAL` | VALUE TO WRITE TO REGISTER |
| 3 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  DEVICE REGISTER (DA) = VAL
    EQUIPMENT:  AP120B WITH EITHER MEMORY
    SIZE:       2
    FORTRAN CALL:  CALL DAWRIT(DA,VAL)
    SCRATCH:       DA
    ENTER WITH FOLLOWING S-PAD PARAMETERS:


## MDCOM

`$ENTRY MDCOM, 2`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ADDRESS OF FIRST VALUE |
| 0 | `BITMAP` |  |
| 1 | `B` | ADDRESS OF SECOND VALUE |


    --- ABSTRACT ---
    FORMULA:  SP(17) =  1  IF A>B
    =  0  IF A=B
    = -1  IF A<B
    EQUIPMENT:  AP120B WITH EITHER MEMORY
    SIZE:       11 LOCATIONS
    S-PAD PARAMETERS:
    SCRATCH:  DPX,FA,MD

