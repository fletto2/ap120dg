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

### WRTLM in detail — 16 call sites constrain it tightly

    CALL WRTLM (0,1,VAL,0,DBPG-1,0,0,0,0,0.0,0.0)
    CALL WRTLM (1,DT,RPTCNT,ADDR,0,VALVEC(1),VALVEC(2),VALVEC(3),
                VALVEC(4),SPFPN(1),SPFPN(2))
    CALL WRTLM (0,2,IVAL(1),PPASZ,LMID,IV2,IV,0,0,0.0,0.0)
    CALL WRTLM (0,3,0,0,0,0,0,0,0,0.0,0.0)
    CALL WRTLM (1,4,PSPMAX,DBBRK,0,0,0,0,0,0.0,0.0)

- arg 1 is 0/1 — a mode
- arg 2 is 0..4 — the record type
- args 3-5 are count, address, page
- args 6-9 are a four-word integer value vector (`VALVEC`)
- args 10-11 are a REAL pair (`SPFPN`) — the floating value path

`lod100.py` already emits this record format correctly (validated
1160/1160 words against `LOD100.FTN`), so the record layout is known;
what changes is that the routine must present **this** interface.

## Why this matters

With these written, LOD100 can be built from **40 modules of genuine FPS
source** plus 11 written ones, against the LIB100 that already exists —
and FPS's own §9.14 overlay descriptor becomes usable nearly unmodified,
removing the last adaptation from the recovered `LOD10.CMD`.
