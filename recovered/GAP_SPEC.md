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

## Why this matters

With these written, LOD100 can be built from **40 modules of genuine FPS
source** plus 11 written ones, against the LIB100 that already exists —
and FPS's own §9.14 overlay descriptor becomes usable nearly unmodified,
removing the last adaptation from the recovered `LOD10.CMD`.
