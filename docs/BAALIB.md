# BAASRC -- routine reference

**Reconstructed from `[327,010]BAASRC.APS`.**  FPS published no manual for
this library that survives in any archive searched (bitsavers,
archive.org, and the ten manuals transcribed in `docs/ocr/`).
Every line below is quoted or derived from the shipped source;
where a routine does not state something, this says so rather
than guessing.


## Contents

| routine | entry | parameters | s-pads documented |
|---|---|---|---|
| [CVADD](#cvadd) | CVADD | 7 | 8 |
| [CVSUB](#cvsub) | CVSUB | 7 | 8 |
| [CVMUL](#cvmul) | CVMUL | 8 | 15 |
| [CVMAGS](#cvmags) | CVMAGS | 5 | 6 |
| [CVCONJ](#cvconj) | CVCONJ | 5 | 6 |
| [CVMA](#cvma) | CVMA | 10 | 11 |
| [SCJMA](#scjma) | SCJMA | 7 | 8 |
| [CDOTPR](#cdotpr) | CDOTPR | 6 | 7 |
| [CVMOV](#cvmov) | CVMOV | 5 | 6 |
| [CVFILL](#cvfill) | CVFILL | 4 | 5 |
| [CVCOMB](#cvcomb) | CVCOMB | 7 | 8 |
| [CVREAL](#cvreal) | CVREAL | 5 | 6 |
| [VREAL](#vreal) | VREAL | 5 | 6 |
| [VIMAG](#vimag) | VIMAG | 5 | 6 |
| [CVNEG](#cvneg) | CVNEG | 5 | 6 |
| [CVSMUL](#cvsmul) | CVSMUL | 6 | 7 |
| [CVRCIP](#cvrcip) | CVRCIP | 5 | 13 |
| [CRVADD](#crvadd) | CRVADD | 7 | 8 |
| [CRVSUB](#crvsub) | CRVSUB | 7 | 8 |
| [CRVMUL](#crvmul) | CRVMUL | 7 | 8 |
| [CRVDIV](#crvdiv) | CRVDIV | 7 | 8 |
| [POLAR](#polar) | POLAR | 5 | 6 |
| [RECT](#rect) | RECT | 5 | 20 |
| [CVEXP](#cvexp) | CVEXP | 5 | 19 |
| [CVMEXP](#cvmexp) | CVMEXP | 7 | 21 |
| [VCLR](#vclr) | VCLR | 3 | 4 |
| [VMOV](#vmov) | VMOV | 5 | 8 |
| [VSWAP](#vswap) | VSWAP | 5 | 6 |
| [VNEG](#vneg) | VNEG | 5 | 8 |
| [VADD](#vadd) | VADD | 7 | 10 |
| [VSUB](#vsub) | VSUB | 7 | 10 |
| [VMUL](#vmul) | VMUL | 7 | 10 |
| [VSADD](#vsadd) | VSADD | 6 | 9 |
| [VSMUL](#vsmul) | VSMUL | 6 | 9 |
| [VTSADD](#vtsadd) | VTSADD | 6 | 1 |
| [VSSQ](#vssq) | VSSQ | 5 | 8 |
| [VABS](#vabs) | VABS | 5 | 8 |
| [VMA](#vma) | VMA | 9 | 10 |
| [VMSB](#vmsb) | VMSB | 9 | 10 |
| [VMSA](#vmsa) | VMSA | 8 | 9 |
| [VSMA](#vsma) | VSMA | 8 | 9 |
| [VSMSB](#vsmsb) | VSMSB | 8 | 9 |
| [VAM](#vam) | VAM | 9 | 10 |
| [VSBM](#vsbm) | VSBM | 9 | 10 |
| [VSMSA](#vsmsa) | VSMSA | 7 | 8 |
| [VMMA](#vmma) | VMMA | 11 | 12 |
| [VMMSB](#vmmsb) | VMMSB | 11 | 12 |
| [VAAM](#vaam) | VAAM | 11 | 12 |
| [VSBSBM](#vsbsbm) | VSBSBM | 11 | 12 |
| [VAND](#vand) | VAND | 7 | 10 |
| [VEQV](#veqv) | VEQV | 7 | 10 |
| [VOR](#vor) | VOR | 7 | 10 |
| [VINDEX](#vindex) | VINDEX | 6 | 7 |
| [VRVRS](#vrvrs) | VRVRS | 3 | 1 |
| [VFILL](#vfill) | VFILL | 4 | 5 |
| [VRAMP](#vramp) | VRAMP | 5 | 6 |
| [VDIV](#vdiv) | VDIV | 7 | 1 |
| [VTSMUL](#vtsmul) | VTSMUL | 6 | 7 |
| [VSQ](#vsq) | VSQ | 5 | 6 |
| [VSQRT](#vsqrt) | VSQRT | 5 | 1 |
| [VLOG](#vlog) | VLOG | 5 | 19 |
| [VLN](#vln) | VLN | 5 | 16 |
| [VALOG](#valog) | VALOG | 5 | 13 |
| [VEXP](#vexp) | VEXP | 5 | 11 |
| [VSIN](#vsin) | VSIN | 5 | 19 |
| [VCOS](#vcos) | VCOS | 5 | 19 |
| [VATAN](#vatan) | VATAN | 5 | 3 |
| [VATN2](#vatn2) | VATN2 | 7 | 3 |
| [VRAND](#vrand) | VRAND | 4 | 5 |
| [VINT](#vint) | VINT | 5 | 6 |
| [VFRAC](#vfrac) | VFRAC | 5 | 6 |
| [DOTPR](#dotpr) | DOTPR | 6 | 9 |
| [RMSQV](#rmsqv) | RMSQV | 4 | 5 |
| [MEANV](#meanv) | MEANV | 4 | 5 |
| [MEAMGV](#meamgv) | MEAMGV | 4 | 5 |
| [MEASQV](#measqv) | MEASQV | 4 | 5 |
| [SVE](#sve) | SVE | 4 | 5 |
| [SVEMG](#svemg) | SVEMG | 4 | 5 |
| [SVESQ](#svesq) | SVESQ | 4 | 5 |
| [SVS](#svs) | SVS | 4 | 5 |
| [MAXV](#maxv) | MAXV | 4 | 1 |
| [MINV](#minv) | MINV | 4 | 1 |
| [MAXMGV](#maxmgv) | MAXMGV | 4 | 1 |
| [MINMGV](#minmgv) | MINMGV | 4 | 1 |
| [XMAXV](#xmaxv) | XMAXV | 4 | 1 |
| [XMINV](#xminv) | XMINV | 4 | 1 |
| [XMAXMG](#xmaxmg) | XMAXMG | 4 | 1 |
| [XMINMG](#xminmg) | XMINMG | 4 | 1 |

88 routines.


## CVADD

`$ENTRY CVADD, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)+B(MJ))+I(A(MI+1)+B(MJ+1)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH FAST MEMORY
    SIZE: 13 LOCATIONS
    FORTRAN: CALL CVADD(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0),DPY(0),FA,MD


## CVSUB

`$ENTRY CVSUB, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)-B(MJ))+I(A(MI+1)-B(MJ+1)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH FAST MEMORY
    SIZE: 13 LOCATIONS
    FORTRAN: CALL CVSUB(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0),DPY(0),FA,MD


## CVMUL

`$ENTRY CVMUL, 8`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 0 | `AR` | REAL PART OF A |
| 0 | `RB` | REAL PART OF B |
| 1 | `AI` | IMAGINARY PART OF A |
| 1 | `BI` | IMAGINARY PART OF B |
| 1 | `I` | VECTOR A INCREMENT |
| 2 | `B` | VECTOR B ORIGIN |
| 2 | `TI` | STORAGE FOR IMAGINARY PART |
| 2 | `TR` | STORAGE FOR REAL PART |
| 3 | `J` | VECTOR B INCREMENT |
| 4 | `C` | VECTOR C ORIGIN |
| 5 | `K` | VECTOR C INCREMENT |
| 6 | `N` | VECTOR LENGTH |
| 7 | `F` | FLAG FOR COMPLEX CONJUGATE |
| 234 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  26
    S-PAD PARAMETERS
    SCRATCH:
    F = 1:  COMPLEX MULTIPLY
    F = - 1:  COMPLEX MULTIPLY WITH A CONJUGATE


## CVMAGS

`$ENTRY CVMAGS, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 2 | `C` | VECTOR C ORIGIN |
| 3 | `K` | VECTOR C INCREMENT |
| 4 | `N` | VECTOR LENGTH |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  13 LOCATIONS
    DOES C(M) = AR(M)*AR(M) + AI(M)*AI(M)
    SCRATCH:


## CVCONJ

`$ENTRY CVCONJ, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ADDRESS OF COMPLEX SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK) + IC(MK+1) = A(MI) - IA(MI+1), FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH FAST MEMORY
    SIZE: 10 LOCATIONS
    FORTRAN: CALL CVCONJ(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4), DPX(0), DPA UNCHANGED


## CVMA

`$ENTRY CVMA, 10`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF COMPLEX SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN REAL ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF COMPLEX SOURCE VECTOR B |
| 3 | `J` | INCREMENT BETWEEN REAL ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF COMPLEX SOURCE VECTOR C |
| 5 | `K` | INCREMENT BETWEEN REAL ELEMENTS OF C |
| 6 | `D` | BASE ADDRESS OF COMPLEX DESTINATION VECTOR D |
| 7 | `L` | INCREMENT BETWEEN REAL ELEMENTS OF D |
| 8 | `N` | NUMBER OF ELEMENTS IN C |
| 9 | `F` | FLAG FOR NORMAL OR CONJUGATE MULTIPLY |
| 938 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA: (D(ML)+ID(ML+1))=(C(MK)+IC(MK+1)) +
    EQUIPMENT: AP-120 WITH FAST MEMORY
    SIZE: 35 LOCATIONS
    FORTRAN CALL: CALL CVMA(A,I,B,J,C,K,D,L,N,F)
    S-PAD PARAMETERS
    F=1, NORMAL
    F=-1, CONJUGATE
    SCRATCH:  SP(0,2,4,6),  DPX(-2,-1,0,1),  DPY(0,1),  DPA UNCHANGED


## SCJMA

`$ENTRY SCJMA, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF COMPLEX SOURCE VECTOR A |
| 1 | `I` | INCREMENT BETWEEN REAL ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF REAL SOURCE VECTOR B |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF REAL DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA: C(MK)=B(MJ)+(A(MI))**2+(A(MI+1))**2
    EQUIPMENT: AP120 WITH FAST MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN CALL: CALL SCJMA(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6), DPX(0,1), DPY(1),  DPA UNCHANGED.


## CDOTPR

`$ENTRY CDOTPR, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `I` | INCREMENT OF A |
| 2 | `B` | BASE ADDR OF B |
| 3 | `J` | INCREMENT OF B |
| 4 | `C` | BASE ADDR OF C |
| 5 | `N` | LENGTH OF VECTORS |
| 42 | `BITMAP` |  |


    ALGORITHM DOES THE DOT PRODUCT OF THESE VECTORS.
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15. LOCATIONS
    ---------- SCRATCH ----------


## CVMOV

`$ENTRY CVMOV, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = A(MI)+IA(MI+1) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 9 LOCATIONS
    FORTRAN: CALL CVMOV(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4),MD


## CVFILL

`$ENTRY CVFILL, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ADDRESS OF CONSTANT REAL VALUE |
| 1 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 2 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 3 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 12 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = A(0)+IA(1) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 8 LOCATIONS
    FORTRAN: CALL CVFILL(A,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(1,3), DPX(0),MD


## CVCOMB

`$ENTRY CVCOMB, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF REAL VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF IMAGINARY VECTOR |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = A(MI)+IB(MJ) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 10 LOCATIONS
    FORTRAN: CALL CVCOMB(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),MD


## CVREAL

`$ENTRY CVREAL, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF REAL VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = A(MI)+I0.0 FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 9 LOCATIONS
    FORTRAN: CALL CVREAL(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4),MD


## VREAL

`$ENTRY VREAL, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF COMPLEX VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF REAL DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:   C(MK) = A(MI) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 1 + VMOV (14 - FAST; 6 - SLOW) = 15 FAST; 7 SLOW
    FORTRAN: CALL VREAL(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4),MD    (SLOW MEM)


## VIMAG

`$ENTRY VIMAG, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF COMPLEX VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF REAL DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:   C(MK) = A(MI+1) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 2 + VMOV (14 - FAST; 6 - SLOW) = 16 FAST; 8 SLOW
    FORTRAN: CALL VIMAG(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4),MD    (SLOW MEM)


## CVNEG

`$ENTRY CVNEG, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = -A(MI)-IA(MI+1) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 11 LOCATIONS
    FORTRAN: CALL CVNEG(A,I,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4),FA,MD


## CVSMUL

`$ENTRY CVSMUL, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | SOURCE VECTOR BASE ADDRESS |
| 1 | `I` | A ADDRESS INCREMENT |
| 2 | `B` | SCALAR ADDRESS |
| 3 | `C` | DESTINATION VECTOR BASE ADDRESS |
| 4 | `K` | C ADDRESS INCREMENT |
| 5 | `N` | ELEMENT COUNT |
| 50 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = B * (A(MI)+IA(MI+1))  FOR M=0 TO N-1
    EQUIPMENT: AP120B WITH EITHER SPEED MEMORY
    SIZE:      12
    FORTRAN CALL:  CALL CVSMUL(A,I,B,C,K,N)
    SCRATCH:       SP(0,3,5),DPX(0),FM,MD
    ENTER WITH FOLLOWING S-PAD PARAMETERS:


## CVRCIP

`$ENTRY CVRCIP, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A VECTOR |
| 0 | `ONE` |  |
| 0 | `R` |  |
| 1 | `AR2` |  |
| 1 | `I` | INCREMENT FOR VECTOR A |
| 2 | `AI2` |  |
| 2 | `AR1` |  |
| 2 | `C` | BASE ADDRESS OF VECTOR C |
| 3 | `AI1` |  |
| 3 | `K` | INCREMENT FOR VECTOR C |
| 4 | `N` | ELEMENT COUNT FOR C |
| 5 | `ONEPTR` | POINTER TO 1.0 IN TM |
| 26 | `BITMAP` |  |


    DOES THE ELEMENT BY ELEMENT RECIPROCAL OF A COMPLEX VECTOR
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 23 LOCATIONS + DIVIDE
    SCRATCH: SP:0,2,4; DPX: 0-2;  DPY: 0-2  (REL TO DPA) PLUS DIVIDE
    S-PAD PARAMETERS:


## CRVADD

`$ENTRY CRVADD, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR (COMPLEX) |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR (REAL) |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)+B(MJ))+I(A(MI+1)+B(MJ)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL CRVADD(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0),FA,MD


## CRVSUB

`$ENTRY CRVSUB, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR (COMPLEX) |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR (REAL) |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)-B(MJ))+I(A(MI+1)-B(MJ)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL CRVSUB(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0),FA,MD


## CRVMUL

`$ENTRY CRVMUL, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR (COMPLEX) |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR (REAL) |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)*B(MJ))+I(A(MI+1)*B(MJ)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 14 LOCATIONS
    FORTRAN: CALL CRVMUL(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6),DPX(0),FM,MD


## CRVDIV

`$ENTRY CRVDIV, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR (COMPLEX) |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF SOURCE VECTOR (REAL) |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF COMPLEX ELEMENTS IN C |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)+IC(MK+1) = (A(MI)/B(MJ))+I(A(MI+1)/B(MJ)) FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 17 + VDIV (75) = 92 LOCATIONS
    FORTRAN: CALL CRVDIV(A,I,B,J,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(0,2,4,6-15),DPX(-2 TO 3),DPY(-4 TO 2),FA,FM,MD,TM


## POLAR

`$ENTRY POLAR, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENT PAIRS OF A |
| 2 | `C` | BASE ADDRESS OF VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENT PAIRS OF C |
| 4 | `N` | NUMBER OF ELEMENT PAIRS IN C |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    DOES RECTANGULAR TO POLAR CONVERSION ON PAIRS OF POINTS
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE        17 LOCATIONS
    S-PAD PARAMETERS:
    --- SCRATCH ---


## RECT

`$ENTRY RECT, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `U` |  |
| 0 | `V` |  |
| 1 | `D` |  |
| 1 | `I` | AT LEAST INCREMENT 2 |
| 1 | `RES1` |  |
| 2 | `C` |  |
| 2 | `D2` |  |
| 2 | `DPREV` |  |
| 2 | `RES2` |  |
| 2 | `RESULT` |  |
| 3 | `K` | AT LEAST INCREMENT 2 |
| 4 | `N` |  |
| 12 | `B` |  |
| 13 | `NINTRO` |  |
| 14 | `MASK` |  |
| 14 | `TABLE1` |  |
| 15 | `STATUS` |  |
| 15 | `TABLE` |  |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    DOES  C( MK ) = A(MI) * COS ( A(MI+1) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 58. LOCATIONS
    FORTRAN  CALL: CALL RECT (A, I, C, K, N)
    SCRATCH: SP(0,2,4,12.-15.),DPX(-4 TO +3),DPY(-4 TO +2),FA,FM,MD,TM
    S-PAD PARAMETERS:
    ---SCRATCH---
    CONSTANTS (DEPENDENT ON SIZE OF TMROM COSINE TABLE)


## CVEXP

`$ENTRY CVEXP, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `U` |  |
| 0 | `V` |  |
| 1 | `D` |  |
| 1 | `I` |  |
| 1 | `RES1` |  |
| 2 | `C` |  |
| 2 | `D2` |  |
| 2 | `DPREV` |  |
| 2 | `RES2` |  |
| 2 | `RESULT` |  |
| 3 | `K` | INCREMENT AT LEAST 2 |
| 4 | `N` |  |
| 13 | `NINTRO` |  |
| 14 | `MASK` |  |
| 14 | `TABLE1` |  |
| 15 | `STATUS` |  |
| 15 | `TABLE` |  |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    VECTOR CVEXP  (ANGLES IN RADIANS)  EXP(IX)=COS(X)+ISIN(X)
    DOES C( MK ) = COS ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 52. LOCATIONS
    FORTRAN CALL: CALL CVEXP (A, I, C, K, N)
    SCRATCH: SP(0,2,4,13.-15.),DPX(-4 TO +3),DPY(-4,-3,-1 TO +2),FA,FM,MD,TM
    S-PAD PARAMETERS:
    ---SCRATCH---
    CONSTANTS (DEPENDENT ON SIZE OF TMROM COSINE TABLE)


## CVMEXP

`$ENTRY CVMEXP, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `U` |  |
| 0 | `V` |  |
| 1 | `D` |  |
| 1 | `I` |  |
| 1 | `RES1` |  |
| 2 | `B` |  |
| 2 | `D2` |  |
| 2 | `DPREV` |  |
| 2 | `RES2` |  |
| 2 | `RESULT` |  |
| 3 | `J` |  |
| 4 | `C` |  |
| 5 | `K` |  |
| 6 | `N` |  |
| 13 | `NINTRO` |  |
| 14 | `MASK` |  |
| 14 | `TABLE1` |  |
| 15 | `STATUS` |  |
| 15 | `TABLE` |  |
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    DOES  C( MK ) = B(MJ) * COS ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 57. LOCATIONS
    FORTRAN  CALL: CALL CVMEXP (A, I, B, J, C, K, N)
    SCRATCH: SP(0,2,4,6,13.-15.),DPX(-4 TO +3),DPY(-4 TO +2),FA,FM,MD,TM
    S-PAD PARAMETERS:
    ---SCRATCH---
    CONSTANTS (DEPENDENT ON SIZE OF TMROM COSINE TABLE)


## VCLR

`$ENTRY VCLR, 3`


| s-pad | name | meaning |
|---|---|---|
| 0 | `C` | BASE ADDRESS OF C |
| 1 | `K` | INCREMENT FOR C |
| 2 | `N` | NUMBER OF ELEMENTS IN C |
| 6 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH FAST MEMORY
    SIZE:  8 + SPUFLT (8) = 16 LOCATIONS


## VMOV

`$ENTRY VMOV, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT FOR A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `C` | BASE ADDRESS OF VECTOR C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | ELEMENT OUUNT FOR C |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  8 LOCATIONS + SPUFLT (8) = 16 LOCATIONS
    SCRATCH:
    S-PAD PARAMETERS:


## VSWAP

`$ENTRY VSWAP, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `C` | BASE ADDR OF C |
| 3 | `K` | INCREMENT OF C |
| 4 | `N` | LENGTH OF VECTORS |
| 26 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      13. + SPUFLT (8) = 21. LOCATIONS


## VNEG

`$ENTRY VNEG, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT FOR VECTOR A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `C` | BASE ADDRESS FOR VECTOR C |
| 3 | `K` | INCREMENT FOR VECTOR C |
| 4 | `N` | ELEMENT COUNT OF VECTOR C |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  10 + SPUFLT (8) = 18 LOCATIONS
    DOES C(MK) = - A(MI)
    S-PAD PARAMETERS:
    SCRATCH:         S-PADS:  0,2,4,17


## VADD

`$ENTRY VADD, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INDEX BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  12  + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    --- SCRATCH ---


## VSUB

`$ENTRY VSUB, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INDEX BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    --- ABSTRACT ---
    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:   12 + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    --- SCRATCH ---


## VMUL

`$ENTRY VMUL, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF A |
| 1 | `I` | INCREMENT FOR A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `N` | ELEMENT COUNT FOR C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    DOES C(MK) = A(MI) * B(MJ),   FOR M = 0 TO N-1
    SIZE:  12 + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH:


## VSADD

`$ENTRY VSADD, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | CONSTANT VECTOR B |
| 3 | `C` | VECTOR C ORIGIN |
| 4 | `K` | VECTOR C INCREMENT |
| 5 | `N` | VECTOR LENGTH |
| 15 | `NM` |  |
| 50 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  11 + SPUFLT (8) = 19 LOCATIONS
    DOES C(M) = A(M) + B   FOR M = 0 TO N - 1
    S-PAD PARAMETERS:
    SCRATCH:


## VSMUL

`$ENTRY VSMUL, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | CONSTANT VECTOR B |
| 3 | `C` | VECTOR C ORIGIN |
| 4 | `K` | VECTOR C INCREMENT |
| 5 | `N` | VECTOR LENGTH |
| 15 | `NM` |  |
| 50 | `BITMAP` |  |


    EQUIPMENT:   AP-120B WITH ONE CYCLE MEMORY
    SIZE:  12 + SPUFLT (8) = 20 LOCATIONS
    DOES C(MK) = A(MI)*B FOR M = 0 TO N - 1
    S-PAD PARAMETERS
    SCRATCH:


## VTSADD

`$ENTRY VTSADD, 6`


| s-pad | name | meaning |
|---|---|---|
| 54 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT: AP-120B WITH STANDARD OR FAST MEMORY
    SIZE: 9
    FORTRAN: CALL VTSADD (A, I, B, C, K, N)
    S-PAD PARAMETERS:
    ---SCRATCH---


## VSSQ

`$ENTRY VSSQ, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT FOR VECTOR A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `C` | BASE ADDRESS OF VECTOR C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | LENGTH OF C |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  13 + SPUFLT (8) = 21 LOCATIONS
    DOES C(K) = A(I) * ABS(A(I)),  FOR M = 0 TO N-1
    S-PAD PARAMETERS:
    --- SCRATCH ---


## VABS

`$ENTRY VABS, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | A VECTOR ORIGIN |
| 1 | `I` | A VECTOR INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `C` | C VECTOR ORIGIN |
| 3 | `K` | C VECTOR INCREMENT |
| 4 | `N` | LENGTH OF C |
| 15 | `NM` |  |
| 26 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:   9 + SPUFLT (8) = 17 LOCATIONS
    DOES C(MK) = ABS(A(MI)),   FOR M = 0 TO N-1
    S-PAD PARAMETERS:
    SCRATCH:


## VMA

`$ENTRY VMA, 9`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `N` | NUMBER OF COMPONENTS |
| 426 | `BITMAP` |  |


    THIS ALGORITHM DOES D <= A*B+C COMPONENT-WISE
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15 + SPUFLT (8) = 23 LOCATIONS
    ---------- SCRATCH ----------


## VMSB

`$ENTRY VMSB, 9`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `N` | NUMBER OF COMPONENTS |
| 426 | `BITMAP` |  |


    THIS ALGORITHM DOES D <= A*B-C COMPONENT-WISE
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15 + SPUFLT (8) = 23 LOCATIONS
    ---------- SCRATCH ----------


## VMSA

`$ENTRY VMSA, 8`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | ADDR FOR C |
| 5 | `D` | BASE ADDR FOR D |
| 6 | `L` | INCREMENT FOR D |
| 7 | `N` | VECTOR LENGTH |
| 202 | `BITMAP` |  |


    THIS ALGORITHM DOES D(M)<=A(M)*B(M)+C FOR N ELEMENTS
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE: 15. + SPUFLT (8) = 23 WORDS
    ---------- S-PAD PARAMETERS ----------
    --------- SCRATCH ----------


## VSMA

`$ENTRY VSMA, 8`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `C` |  |
| 4 | `J` |  |
| 5 | `D` |  |
| 6 | `K` |  |
| 7 | `N` |  |
| 210 | `BITMAP` |  |


    THIS ALGORITHM DOES D<=A*B+C WHERE B IS A SCALAR
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      13. LOCATIONS + SPUFLT (8) = 21. LOCATIONS
    --------SCRATCH--------


## VSMSB

`$ENTRY VSMSB, 8`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 1 | `I` |  |
| 2 | `B` |  |
| 3 | `C` |  |
| 4 | `J` |  |
| 5 | `D` |  |
| 6 | `K` |  |
| 7 | `N` |  |
| 210 | `BITMAP` |  |


    THIS ALGORITHM DOES D<=A*B-C WHERE B IS A SCALAR
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      13. LOCATIONS + SPUFLT (8) = 21. LOCATIONS
    --------SCRATCH--------


## VAM

`$ENTRY VAM, 9`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `N` | LENGTH OF VECTORS |
| 426 | `BITMAP` |  |


    THIS ALGORITHM DOES D <=(A+B)*C
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15 + SPUFLT (8) = 23 WORDS
    ---------- SCRATCH ----------


## VSBM

`$ENTRY VSBM, 9`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `N` | LENGTH OF VECTORS |
| 426 | `BITMAP` |  |


    THIS ALGORITHM DOES D <=(A-B)*C
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15 + SPUFLT (8) = 23 WORDS
    ---------- SCRATCH ----------


## VSMSA

`$ENTRY VSMSA, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `I` | INCREMENT OF A |
| 2 | `B` | BASE ADDR OF B |
| 3 | `C` | BASE ADDR OF C |
| 4 | `D` | BASE ADDR OF D |
| 5 | `L` | INCREMENT OF D |
| 6 | `N` | SIZE OF VECTORS |
| 98 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      15 + SPUFLT (8) = 23 WORDS
    ---------- SCRATCH ----------


## VMMA

`$ENTRY VMMA, 11`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `E` | BASE ADDR FOR E |
| 9 | `M` | INCREMENT FOR E |
| 10 | `N` | SIZE OF VECTORS |
| 1706 | `BITMAP` |  |


    THIS ALGORITHM DOES E<= A*B+C*D
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      19 + SPUFLT (8) = 27 WORDS
    ---------- SCRATCH ----------


## VMMSB

`$ENTRY VMMSB, 11`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `B` | BASE ADDR FOR B |
| 3 | `J` | INCREMENT FOR B |
| 4 | `C` | BASE ADDR FOR C |
| 5 | `K` | INCREMENT FOR C |
| 6 | `D` | BASE ADDR FOR D |
| 7 | `L` | INCREMENT FOR D |
| 8 | `E` | BASE ADDR FOR E |
| 9 | `M` | INCREMENT FOR E |
| 10 | `N` | SIZE OF VECTORS |
| 1706 | `BITMAP` |  |


    THIS ALGORITHM DOES E<= A*B-C*D
    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      19 + SPUFLT (8) = 27 WORDS
    ---------- SCRATCH ----------


## VAAM

`$ENTRY VAAM, 11`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `D` | BASE ADDRESS OF VECTOR D |
| 7 | `L` | INCREMENT BETWEEN ELEMENTS OF D |
| 8 | `E` | BASE ADDRESS OF VECTOR E |
| 9 | `M` | INCREMENT BETWEEN ELEMENTS OF E |
| 10 | `N` | LOOP COUNTER FOR THE NUMBER OF COMPONENTS DESIRED |
| 1706 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      13 LOCATIONS
    ---------- SCRATCH ----------


## VSBSBM

`$ENTRY VSBSBM, 11`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INCREMENT BETWEEN ELEMENTS OF A |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INCREMENT BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF VECTOR C |
| 5 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 6 | `D` | BASE ADDRESS OF VECTOR D |
| 7 | `L` | INCREMENT BETWEEN ELEMENTS OF D |
| 8 | `E` | BASE ADDRESS OF VECTOR E |
| 9 | `M` | INCREMENT BETWEEN ELEMENTS OF E |
| 10 | `N` | LOOP COUNTER FOR THE NUMBER OF COMPONENTS DESIRED |
| 1706 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH FAST MEMORY
    SIZE:      13 LOCATIONS
    ---------- SCRATCH ----------


## VAND

`$ENTRY VAND, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INDEX BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(MK) = B(MJ) AND A(MI)     FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH FAST MEMORY
    SIZE:    12 LOCATIONS + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    OTHER S-PAD PARAMETERS:
    SCRATCH: SP(0,2,4,14,15), DPX(0-1),DPY(0), FA,MD,TM


## VEQV

`$ENTRY VEQV, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INDEX BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(MK) = B(MJ) EQV A(MI)     FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH FAST MEMORY
    SIZE:    12 LOCATIONS + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    OTHER S-PAD PARAMETERS:
    SCRATCH: SP(0,2,4,14,15), DPX(0-1),DPY(0), FA,MD,TM


## VOR

`$ENTRY VOR, 7`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | BASE ADDRESS OF VECTOR B |
| 3 | `J` | INDEX BETWEEN ELEMENTS OF B |
| 4 | `C` | BASE ADDRESS OF C |
| 5 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 6 | `N` | NUMBER OF ELEMENTS IN C |
| 15 | `NM` |  |
| 106 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(MK) = B(MJ) OR A(MI)     FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH FAST MEMORY
    SIZE:    12 LOCATIONS + SPUFLT (8) = 20 LOCATIONS
    S-PAD PARAMETERS
    OTHER S-PAD PARAMETERS:
    SCRATCH: SP(0,2,4,15), DPX(0-1),DPY(0), FA,MD,TM


## VINDEX

`$ENTRY VINDEX, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `B` | BASE ADDR OF B |
| 2 | `J` | INCREMENT OF B |
| 3 | `C` | BASE ADDR OF C |
| 4 | `K` | INCREMENT OF C |
| 5 | `N` | SIZE OF VECTORS |
| 52 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE:      16. + SPUFLT (8) = 24. WORDS
    ---------- SCRATCH ----------


## VRVRS

`$ENTRY VRVRS, 3`


| s-pad | name | meaning |
|---|---|---|
| 6 | `BITMAP` |  |


    ---- ABSTRACT ------
    FORMULA:
    EQUIPMENT:  AP 120B WITH EITHER MEMORY.
    CALL     :  CALL VRVRS (C,K,N)
    SIZE     :  19 + 14 APAL WORDS.
    SCRATCH  :  SP(0,2,16,17),FA,FM,MD


## VFILL

`$ENTRY VFILL, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ADDRESS OF CONSTANT VALUE |
| 1 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 2 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 3 | `N` | NUMBER OF ELEMENTS IN C |
| 12 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)=A,  FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 6 LOCATIONS
    FORTRAN: CALL VFILL(A,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(1,3), DPA UNCHANGED


## VRAMP

`$ENTRY VRAMP, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | ADDRESS OF INITIAL RAMP VALUE |
| 1 | `B` | ADDRESS OF STEP INCREMENT |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR C |
| 3 | `K` | INCREMENT BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 24 | `BITMAP` |  |


    ---ABSTRACT---
    FORMULA:  C(MK)=M*B+A,  FOR M=0 TO N-1
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 12 LOCATIONS
    FORTRAN: CALL VRAMP(A,B,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(2,4), DPX(0), DPY(0), DPA UNCHANGED


## VDIV

`$ENTRY VDIV, 7`


| s-pad | name | meaning |
|---|---|---|
| 106 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          76. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---
    S-PAD PARAMETERS
    THIS DOESN'T NEGATE Y(2).  OTHERWISE, SAME CODE AS ABOVE.
    THIS DOESN'T NEGATE Y(3).  OTHERWISE, SAME CODE AS ABOVE.
    THIS DOESN'T NEGATE Y(L).  OTHERWISE, SAME CODE AS IN LOOP.


## VTSMUL

`$ENTRY VTSMUL, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `I` | INCREMENT OF A |
| 2 | `B` | TABLE MEMORY ADDR OF SCALAR |
| 3 | `C` | BASE ADDR OF C |
| 4 | `K` | INCREMENT OF C |
| 5 | `N` | SIZE OF VECTORS |
| 54 | `BITMAP` |  |


    ---ABSTRACT----
    FORMULA:  C(MK) = A(MI) * B    FOR M=0 TO N-1
    EQUIPMENT: AP-120B WITH FAST OR STANDARD MEMORY
    SIZE:      9. LOCATIONS
    ---------- SCRATCH ----------


## VSQ

`$ENTRY VSQ, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | BASE ADDRESS OF C |
| 3 | `K` | INDEX BETWEEN ELEMENTS OF C |
| 4 | `N` | NUMBER OF ELEMENTS IN C |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(MK) = A(MI) * A(MI)     FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    9 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,2,4), DPX(0), FM,MD


## VSQRT

`$ENTRY VSQRT, 5`


| s-pad | name | meaning |
|---|---|---|
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP-120B WITH EITHER MEMORY
    SIZE:          80. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## VLOG

`$ENTRY VLOG, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 0 | `U` |  |
| 0 | `V` |  |
| 0 | `V2` |  |
| 0 | `X` |  |
| 1 | `I` | ADDRESS INCREMENT FOR A |
| 1 | `XTEMP` |  |
| 1 | `YTEMP` |  |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR |
| 2 | `LN2` | (NOTE: USES SAME STORAGE AS YTEMP1) |
| 2 | `XTEMP1` |  |
| 2 | `YTEMP1` |  |
| 3 | `K` | ADDRESS INCREMENT FOR C |
| 3 | `LOGE` |  |
| 3 | `S` |  |
| 4 | `N` | ELEMENT COUNT |
| 11 | `MASK` |  |
| 12 | `ZEROFLAG` |  |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA:  C(MK) = LOG (ABS(A(MI))   FOR M=0 TO N-1
    EQUIPMENT:     AP 120B WITH EITHER MEMORY
    SIZE:  62 LOCATIONS
    FORTRAN CALL:  CALL VLOG (A,I,C,K,N)
    SCRATCH:       SP(0,2,4,13-17), DPX(0-3), DPY(-1 TO 3), FA, FM, MD, TM
    S-PAD PARAMETERS:
    THIS DOESN'T MATTER, SINCE ARG IS 0 ANYWAY.


## VLN

`$ENTRY VLN, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF SOURCE VECTOR |
| 0 | `U` |  |
| 0 | `V` |  |
| 0 | `V2` |  |
| 0 | `X` |  |
| 1 | `I` | ADDRESS INCREMENT FOR A |
| 1 | `XTEMP` |  |
| 1 | `YTEMP` |  |
| 2 | `C` | BASE ADDRESS OF DESTINATION VECTOR |
| 2 | `LN2` | (NOTE: USES SAME STORAGE AS YTEMP1) |
| 2 | `XTEMP1` |  |
| 2 | `YTEMP1` |  |
| 3 | `K` | ADDRESS INCREMENT FOR C |
| 3 | `S` |  |
| 4 | `N` | ELEMENT COUNT |
| 26 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA:  C(MK) = LN (ABS(A(MI))   FOR M=0 TO N-1
    EQUIPMENT:     AP 120B WITH EITHER MEMORY
    SIZE:  45 LOCATIONS
    FORTRAN CALL:  CALL VLN(A,I,C,K,N)
    SCRATCH:       SP(0,2,4,15-17), DPX(0-3), DPY(0-2), FA, FM, MD, TM
    S-PAD PARAMETERS:


## VALOG

`$ENTRY VALOG, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS FOR SOURCE VECTOR A |
| 0 | `F` |  |
| 0 | `X` |  |
| 0 | `YTEMP` |  |
| 1 | `F2` |  |
| 1 | `I` | ADDRESS INCREMENT FOR A |
| 1 | `YTEMP1` |  |
| 2 | `C` | BASE ADDRESS FOR DESTINATION VECTOR C |
| 2 | `LN10` |  |
| 2 | `SCALE` |  |
| 3 | `K` | ADDRESS INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT |
| 26 | `BITMAP` |  |


    FORMULA: C(MK) = 10. ** A(M(I))  FOR M = 0 TO N-1
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE:  59 LOCATIONS
    FORTRAN CALL:  CALL VALOG (A, I, C, K, N)
    SCRATCH:       SP(0,2,4,15-17),DPX(-3 TO +2),DPY(0-2),FA,FM,MD,TM
    SCRATCH PAD PARAMETERS:


## VEXP

`$ENTRY VEXP, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS FOR SOURCE VECTOR A |
| 0 | `F` |  |
| 0 | `X` |  |
| 0 | `YTEMP` |  |
| 1 | `F2` |  |
| 1 | `I` | ADDRESS INCREMENT FOR A |
| 2 | `C` | BASE ADDRESS FOR DESTINATION VECTOR C |
| 2 | `SCALE` |  |
| 3 | `K` | ADDRESS INCREMENT FOR C |
| 4 | `N` | ELEMENT COUNT |
| 26 | `BITMAP` |  |


    FORMULA: C(MK) = EXP ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE:  56 LOCATIONS
    FORTRAN CALL:  CALL VEXP (A, I, C, K, N)
    SCRATCH:       SP(0,2,4,15-17),DPX(-3 TO +2),DPY(0),FA,FM,MD,TM
    SCRATCH PAD PARAMETERS:


## VSIN

`$ENTRY VSIN, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `U` |  |
| 0 | `V` |  |
| 1 | `D` |  |
| 1 | `I` |  |
| 1 | `RES1` |  |
| 2 | `C` |  |
| 2 | `D2` |  |
| 2 | `DPREV` |  |
| 2 | `RES2` |  |
| 2 | `RESULT` |  |
| 3 | `K` |  |
| 4 | `N` |  |
| 13 | `NINTRO` |  |
| 14 | `MASK` |  |
| 14 | `TABLE1` |  |
| 15 | `STATUS` |  |
| 15 | `TABLE` |  |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    DOES C( MK ) = SIN ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 42. LOCATIONS
    FORTRAN CALL: CALL VSIN (A, I, C, K, N)
    SCRATCH: SP(0,2,4,13.-15.),DPX(-4 TO +2),DPY(-1 TO +2),FA,FM,MD,TM
    S-PAD PARAMETERS:
    (1)    U = X * SCALE, WHERE SCALE = (2/PI) * COSINE-TABLE-SIZE
    (NOTE: IF X IS IN RANGE 0 TO PI/2, U IS IN RANGE 0 TO TABLE-SIZE)
    (2)    V = FIXT (U)
    (3)    D = U - V
    Q = -1 / (6 * SCALE**3)
    S = -1 / (2 * SCALE**2)
    ---SCRATCH---
    CONSTANTS (DEPENDENT ON SIZE OF TMROM COSINE TABLE)


## VCOS

`$ENTRY VCOS, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` |  |
| 0 | `U` |  |
| 0 | `V` |  |
| 1 | `D` |  |
| 1 | `I` |  |
| 1 | `RES1` |  |
| 2 | `C` |  |
| 2 | `D2` |  |
| 2 | `DPREV` |  |
| 2 | `RES2` |  |
| 2 | `RESULT` |  |
| 3 | `K` |  |
| 4 | `N` |  |
| 13 | `NINTRO` |  |
| 14 | `MASK` |  |
| 14 | `TABLE1` |  |
| 15 | `STATUS` |  |
| 15 | `TABLE` |  |
| 26 | `BITMAP` |  |


    ---ABSTRACT---
    DOES C( MK ) = COS ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 42. LOCATIONS
    FORTRAN CALL: CALL VCOS (A, I, C, K, N)
    SCRATCH: SP(0,2,4,13.-15.),DPX(-4 TO +2),DPY(-1 TO +2),FA,FM,MD,TM
    S-PAD PARAMETERS:
    (1)    U = X * SCALE, WHERE SCALE = (2/PI) * COSINE-TABLE-SIZE
    (NOTE: IF X IS IN RANGE 0 TO PI/2, U IS IN RANGE 0 TO TABLE-SIZE)
    (2)    V = FIXT (U)
    (3)    D = U - V
    Q = -1 / (6 * SCALE**3)
    S = -1 / (2 * SCALE**2)
    ---SCRATCH---
    CONSTANTS (DEPENDENT ON SIZE OF TMROM COSINE TABLE)


## VATAN

`$ENTRY VATAN, 5`


| s-pad | name | meaning |
|---|---|---|
| 5 | `ADR` | RELATIVE ADDRESS OF FUNCTION |
| 6 | `LOC` | BASE LOCATION TO WHICH ADR IS RELATIVE |
| 26 | `BITMAP` |  |


    DOES C(MK) = ATAN ( A(MI) )
    EQUIPMENT:  AP-120B WITH EITHET MEMORY
    SIZE:  3 LOCATIONS + VFCL1 (11) + ATAN (74 INCLUDING DIV) = 88
    S-PAD PARAMETERS:


## VATN2

`$ENTRY VATN2, 7`


| s-pad | name | meaning |
|---|---|---|
| 7 | `ADR` | RELATIVE ADDRESS OF FUNCTION |
| 8 | `LOC` | BASE LOCATION TO WHICH ADR IS RELATIVE |
| 106 | `BITMAP` |  |


    DOES C(M) = ARCTANGENT ( B(M) / A(M) ) FOR M = 0 TO N-1
    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE:  3 LOCATIONS + VFCL2 (12) + ATN2 (74 INCLUDING DIV) = 89
    S-PAD PARAMETERS:


## VRAND

`$ENTRY VRAND, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `S` | ADDRESS OF SEED |
| 1 | `C` | BASE ADDRESS OF C |
| 2 | `K` | INCREMENT FOR C |
| 3 | `N` | DIMENSION OF C |
| 12 | `BITMAP` |  |


    ---ABSTRACT---
    IN THE NEXT CALL TO VRAND.  ANY SEED CAN BE USED INCLUDING ZERO.
    KNUTH, VOLUME 2).  IT IS BASED ON THE RECURSIVE FORMULA
    A = 2  *A1+A2 = 2  *DPY(1)+DPY(2)
    B = 2  *B1+B2 = 2  *DPY(-1)+DPY(-2)
    X = 2  *X1+X2 = 2  *DPX(1)+DPX(2)
    A = 5 (MOD 8)
    EQUIPMENT: AP-120 WITH EITHER MEMORY
    SIZE: 57 LOCATIONS
    FORTRAN: CALL VRAND(S,C,K,N)
    S-PAD PARAMETERS
    SCRATCH:  SP(1,3), DPX(0 TO 3), DPY(-4 TO 3), DPA UNCHANGED


## VINT

`$ENTRY VINT, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR OF A |
| 1 | `I` | INCREMENT OF A |
| 2 | `C` | BASE ADDR OF B |
| 3 | `K` | INCREMENT OF B |
| 4 | `N` | SIZE OF VECTORS |
| 26 | `BITMAP` |  |


    EQUIPMENT: AP-120B WITH FAST OR STANDARD MEMORY
    SIZE:      9. LOCATIONS
    ---------- SCRATCH ----------


## VFRAC

`$ENTRY VFRAC, 5`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDR FOR A |
| 1 | `I` | INCREMENT FOR A |
| 2 | `C` | BASE ADDR FOR C |
| 3 | `K` | INCREMENT FOR C |
| 4 | `N` | SIZE OF VECTORS |
| 26 | `BITMAP` |  |


    INTEGER FLOATING POINT NUMBERS IN C WHOSE SIZE IS N
    EQUIPMENT: AP-120B WITH FAST OR STANDARD MEMORY
    SIZE:      7. LOCATIONS


## DOTPR

`$ENTRY DOTPR, 6`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR A ORIGIN |
| 1 | `I` | VECTOR A INCREMENT |
| 1 | `NN` | FLOATED VECTOR LENGTH |
| 2 | `B` | VECTOR B ORIGIN |
| 3 | `J` | VECTOR B INCREMENT |
| 4 | `C` | VECTOR C ORIGIN |
| 5 | `N` | VECTOR LENGTH |
| 15 | `NM` |  |
| 42 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH ONE CYCLE MEMORY
    SIZE:  13 + SPUFLT (8) = 21 WORDS
    DOES C = SUM ( A(MI) * B(MJ) ) FOR M = 0 TO N-1
    SCRATCH:


## RMSQV

`$ENTRY RMSQV, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF RESULT |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SQRT ( SUM ( A(MI)*A(MI) / N ) )   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    8 + SPUFLT (8) + SVESQ (10) + DIV (28) + SQRT (28) = 82 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3,12-15),DPX(0,1),DPY(0,1),FA,FM,MD,TM


## MEANV

`$ENTRY MEANV, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF RESULT |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SUM ( A(MI) / N )   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    7 + SPUFLT (8) + SVE (7) + DIV (28) = 50 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3,13-15),DPX(0,1),DPY(0),FA,FM,MD,TM


## MEAMGV

`$ENTRY MEAMGV, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF RESULT |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SUM ( ABS(A(MI)) / N )   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    7 + SPUFLT (8) + SVEMG (10) + DIV (28) = 53 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3,13-15),DPX(0,1),DPY(0),FA,FM,MD,TM


## MEASQV

`$ENTRY MEASQV, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF RESULT |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SUM ( A(MI)*A(MI) / N )   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    7 + SPUFLT (8) + SVESQ (10) + DIV (28) = 53 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3,13-15),DPX(0,1),DPY(0),FA,FM,MD,TM


## SVE

`$ENTRY SVE, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | VECTOR ORIGIN |
| 1 | `I` | VECTOR INCREMENT |
| 2 | `C` | SCALAR (RESULT) ORIGIN |
| 3 | `N` | VECTOR LENGTH |
| 10 | `BITMAP` |  |


    DOES C(0) = SUM ( A(MI) )   FOR M = 0 TO N-1
    EQUIPMENT: AP-120B WITH EITHER MEMORY
    SIZE: 7 PROGRAM LOCATIONS
    SCRATCH: SP: 0,2,3; DPX: 0 (RELATIVE TO DPA)
    S-PAD PARAMETERS:


## SVEMG

`$ENTRY SVEMG, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF SUM |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SUM ( ABS(A(MI)))   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    10 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3),DPX(0),FA,MD


## SVESQ

`$ENTRY SVESQ, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | BASE ADDRESS OF VECTOR A |
| 1 | `I` | INDEX BETWEEN ELEMENTS OF A |
| 2 | `C` | ADDRESS OF SUM |
| 3 | `N` | NUMBER OF ELEMENTS IN A |
| 10 | `BITMAP` |  |


    --- ABSTRACT ---
    FORMULA: C(0) = SUM ( A(MI) * A(MI))   FOR M = 0 TO N-1
    EQUIPMENT:   AP-120B WITH EITHER MEMORY
    SIZE:    10 LOCATIONS
    S-PAD PARAMETERS
    SCRATCH: SP(0,3),DPX(0),FA,FM,MD


## SVS

`$ENTRY SVS, 4`


| s-pad | name | meaning |
|---|---|---|
| 0 | `A` | A VECTOR ORIGIN |
| 1 | `I` | A VECTOR INCREMENT |
| 2 | `C` | ANSWER LOCATION |
| 3 | `N` | VECTOR LENGTH |
| 10 | `BITMAP` |  |


    EQUIPMENT:  AP-120B WITH EITHER MEMORY
    SIZE:   11 LOCATIONS
    DOES C(0) = SUM ( A(MI) * ABS(A(MI)) )   FOR M = 0 TO N-1
    S-PAD PARAMETERS:
    SCRATCH:


## MAXV

`$ENTRY MAXV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          20. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## MINV

`$ENTRY MINV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          20. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## MAXMGV

`$ENTRY MAXMGV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          20. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## MINMGV

`$ENTRY MINMGV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          20. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## XMAXV

`$ENTRY XMAXV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          22. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## XMINV

`$ENTRY XMINV, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          22. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## XMAXMG

`$ENTRY XMAXMG, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          22. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---


## XMINMG

`$ENTRY XMINMG, 4`


| s-pad | name | meaning |
|---|---|---|
| 10 | `BITMAP` |  |


    ---ABSTRACT---
    EQUIPMENT:     AP WITH EITHER MEMORY
    SIZE:          22. LOCATIONS
    S-PAD PARAMETERS:
    ---SCRATCH---

