# What a complete LOD100 still needs, and the interfaces it must match

40 of LOD100's program units are recovered and compile clean
(`LOD100_RECOVERED.FTN`). This is the specification for the rest, derived
from the recovered source's own call sites — the same method used for
`FDUTIL_SPEC.md`.

## Not needed after all

`IOVS`, `SYM2`, `VALVEC`, `COMSYM`, `SFILE`, `SFILE1` are **arrays**, not
routines — a first pass mis-read them as external references. `WRTLIN`
is already in LIB100. Of the 47 library primitives the source uses,
**LIB100 as we build it supplies 40**.

## Must be written (11)

Signatures below are what the recovered code actually calls. The existing
`reconstructed/LOD100.FTN` has four of these names, taken from
INSTAL.TXT §9.14, but **invented every signature** — none match:

| module | real interface (from call sites) | reconstruction has |
|---|---|---|
| `WRTLM`  | `(MODE,TYPE,CNT,ADDR,PAGE,V1,V2,V3,V4,R1,R2)` 11 args, last two REAL | `(LUN)` |
| `WRTBR`  | `(FLAG,BUF,LEN,N,ZERO,D1,D2)` 7 args | `()` |
| `TREE`   | `(STR,IPTR,RADIX,LEVEL,SYM)` 5 args | `(ARG,NARG)` |
| `TASKY`  | `(STR,IPTR,FLAG,RADIX)` 4 args | `(ARG,NARG)` |
| `TABGET` | `(TABLE,I,IVAL,SYM)` INTEGER FUNCTION | absent |
| `BLKSKP` | `(STR,IPTR,IDENT)` | absent |
| `TSKLNK` | `()` no arguments | absent |
| `APLDBD` | not called by the 40 — driven from `.MAIN.` | absent |
| `APMDIO` | not called by the 40 | absent |
| `APPRIO` | not called by the 40 | present, different role |
| `WRTDAT` | not called by the 40 | absent |

plus `.MAIN.`, the mainline.

### WRTLM in detail — the manual specifies it, chapter 4

**The load module format is documented**: LOD100 Reference Manual §4.2.
Every block is an **eight-word header** optionally followed by data
records, and the block numbers are exactly WRTLM's second argument:

    4.2.1  Code/Overlay/32-Bit MD Data Block (0)
           header:  0 count addr pg dest 0 0 0
    4.2.2  Data Block (1)
           header:  1 count 0 pg 0 0 0 0
           record:  type rc addr 0 value-a value-b value-c value-d
    4.2.3  Information Block (2)
           header:  2 ppaad ppasz lmid ovlen ovaddr 0 0
    4.2.4  End Block (3)
           logical:      3 0 0 0 0 0 0 0
           terminating:  3 1 0 0 0 0 0 0

So **argument 1 selects header (0) or data record (1)**, and the rest are
that record's words in order. Every call site fits:

| call | manual |
|---|---|
| `WRTLM(0,0,RECCNT*PACK,VAL,OVPAGE,DEST,0,0,0,0.,0.)` | code header: count, addr, pg, **dest** |
| `WRTLM(0,2,IVAL(1),PPASZ,LMID,IV2,IV,0,0,0.,0.)` | info header: **ppaad, ppasz, lmid, ovlen, ovaddr** |
| `WRTLM(0,3,0,...)` / `WRTLM(0,3,1,...)` | **logical** vs **terminating** end block |
| `WRTLM(1,DT,RPTCNT,ADDR,0,VALVEC(1..4),SPFPN(1),SPFPN(2))` | data record: type, **rc**, addr, value-a..d |
| `WRTLM(1,4,PSPMAX,DBBRK,...)` | data type **4 = double precision integer (38-bit)** |

Data-record types are `1` 16-bit integer, `2` single precision host real,
`4` double precision integer (38-bit) — which is why arguments 10-11 are
a REAL pair: they carry the type-2 value.

Note §4.2.3's caveat, which an implementation must honour: *"there may be
multiple occurrences of the information block header. Only the last one
is meaningful."*

## The overlay table entry is 16 words in task mode, not 8

`ENDLNK` builds each entry into `BUFFER` and strides by 16
(`IF (J+16 .LE. BUFSIZ)`), filling `J` through `J+15`:

    J+0   (OVDTA(I,6) & 15) * 8      segment number * 8
    J+1   OVDTA(I,1)                 MD address
    J+2   (OVDTA(I,6) & 15)          segment number
    J+3   OVDTA(I,3)                 length in PS words
    J+4   0
    J+5   OVDTA(I,2)                 PS address
    J+6   0
    J+7   OVDTA(I,4) >> 1            partition count
    J+8   0
    J+9   TSKDTA(TSKPTR,1)           task id
    J+10  0
    J+11  1 for the first entry, else 0
    J+12..J+15  0

and the total length is **halved when not in task mode**:

    IVAL(3)=OVPTR*OVMESZ
    IF (.NOT.TASKFL) IVAL(3)=IVAL(3)/2

So the eight-word entry recorded in CLAUDE.md — from Loader table 2-1 and
Supervisor table 2-2 — is the **non-task** form; task mode uses 16.
`OVMESZ` itself is set in one of the missing modules.

That also fixes the `OVDTA` column meanings, which no manual states:

| column | meaning |
|---|---|
| 1 | MD address |
| 2 | PS address |
| 3 | length in PS words |
| 4 | partition count (stored doubled) |
| 5 | masked to 8 bits for the map (`LOADMP`) |
| 6 | segment number, low 4 bits |
| 7 | pointer used by `OVLY` to release program data |
| 8, 9 | masked to 8 bits by `OVLY` |

## What FINISH settles

**A missing READYQ is an ERROR, not a silent skip.**

    ID=SRCST(DBDTA1,1,-1,RDYQUE,6)      look for the header
    IF (ID.EQ.0) GO TO 90010            -> CALL ERRMES(35)
    C RDYQUE NOT DEFINED

CLAUDE.md records a dispute over the STATUS bit `001000` being set "only
when READYQ is defined", with `lod100.py` right and the FORTRAN wrong.
The real loader does not treat an absent READYQ as a case to handle at
all — in task mode with tasks present it is a hard error, message 35.

**TSKDTA's columns**, which no manual gives:

| column | meaning |
|---|---|
| 1 | task id (used to name the `.MPnnn` overlay map) |
| 3 | flags — bit 0 tested by `LOADMP` |
| 4, 5 | map listing values, 6 digits at columns 15 and 23 |
| 6 | **RLINK** pointer — index of the next task |
| 7 | **LLINK** pointer — index of the previous task |
| 8 | **TCB address** |

and the ready queue is emitted as, for each task,

    CALL WRTLM(0,0,4,TSKDTA(I,8),0,1,0,0,0,0.0,0.0)   header at the TCB
    CALL WRTLM(1,0,TSKDTA(J,8),0,TSKDTA(K,8),...)     RLINK, LLINK

so the links hold the **TCB addresses** of the neighbours, not indices —
a doubly linked list, as the manual says, but through addresses.

**The host interface routine is not a stub.** CLAUDE.md records "HASI
generation is stubbed in both tools". FINISH writes it directly, and this
is the template:

          SUBROUTINE MTSnn(PSSIZ)
          INTEGER CODE,PSSIZ
          COMMON /CODEnn/ CODE(mmmmmm)
          CALL MTSGO (PSSIZ,nn,CODE,mmmmmm)
          RETURN
          END

with `nn` the load module id and `mmmmmm` MXDATA — its own comment calls
it "the FPS100 interface routine ... how the user loads his load module
and starts the supervisor running. ITS LIKE A HASI."

The parameter passing area is a symbol `.PPA.` inserted into `DBDTA1`,
sized `PPASZ = PGINFO(DBPG,1) - DBBRK`, and the information block is
written only when an LM file is open (`SLMFIL(1).NE.0`).

## Why this matters

With these written, LOD100 can be built from **40 modules of genuine FPS
source** plus 11 written ones, against the LIB100 that already exists —
and FPS's own §9.14 overlay descriptor becomes usable nearly unmodified,
removing the last adaptation from the recovered `LOD10.CMD`.
