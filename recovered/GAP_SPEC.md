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

## The overlay table entry: 8 MD words = 16 host words

**Correction.** An earlier note here claimed the entry is "16 words in
task mode, not 8", contradicting Loader table 2-1 and Supervisor table
2-2. That was a **unit error**, and cross-reading the Supervisor manual
settles it.

Supervisor 2.2.3.2: *"Each entry consists of eight main data words"*,
with a note that each MD word has **EXP / HM / LM** portions. An MD word
is 32 bits -- `FSLMLD`'s convention is "32 BITS OF HOST PER MD WORD" --
so on a 16-bit host **one MD word is two host words**.

`ENDLNK` writes sixteen host words, which is **eight MD words**, and they
land exactly on Table 2-2:

| MD word | Table 2-2 | ENDLNK host words |
|---|---|---|
| 1 | overlay segment number | `J+0 = (col6&15)*8`, `J+1 = col1` |
| 2 | MD address | `J+2 = (col6&15)`, `J+3 = col3` |
| 3 | PS address | `J+4 = 0`, `J+5 = col2` |
| 4 | length in PS words | `J+6 = 0`, `J+7 = col4>>1` |
| 5 | task id | `J+8 = 0`, `J+9 = TSKDTA(TSKPTR,1)` |
| 6 | resident bits | `J+10 = 0`, `J+11 = 1 for the first` |
| 7 | first PS partition | `J+12 = 0`, `J+13 = 0` |
| 8 | partition count | `J+14 = 0`, `J+15 = 0` |

`IVAL(3)=OVPTR*OVMESZ` with `/2` when not in task mode is a host-word to
MD-word conversion, not a size difference between modes.

**The two manuals and the code agree.** The lesson is the mirror of the
one already on file: check the units before correcting a manual.

That also pins the `OVDTA` columns, which no manual gives. **Derived from
the writes, not from the emit order** — reading `ENDLNK` alone gave the
wrong answer for 1/2/3 and this corrects it:

| column | set by | meaning |
|---|---|---|
| 1 | *not in the recovered 40* | emitted at `J+1`; set by the missing `TREE` |
| 2 | `OVLY`: `=PSBRK` | **PS address** |
| 3 | `OVLY`: `=DBBRK` / `=PGINFO(OVPG,2)` | **MD address** |
| 4 | `LOAD`: `=(PSBRK-PSHLD)*2` | **PS length, stored doubled** — `ENDLNK` emits `>>1` |
| 5 | *not in the recovered 40* | masked to 8 bits by `LOADMP`; set by the missing `TREE` |
| 6 | `OVLY`: `=IOR16(...,OVPG-1)` | page in the low bits; `ENDLNK` also reads `&15` for the segment |
| 7 | `OVLY`: `=PRGDTA(1)+1` | program data pointer, released by `OVLY` |
| 8 | `OVLY`: `=IOR16(ENTDTA(1)+1,ENTPT1<<8)` | entry table pointer + `ENTPT1` |
| 9 | `OVLY`: `=IOR16(EXTDTA(1)+1,ENTPT1<<8)` | external table pointer + `ENTPT1` |

**Columns 1 and 5 are the ones `TREE` must set** — they are read by
`ENDLNK` and `LOADMP` but written nowhere in the recovered 40, which is
exactly the signature of a value produced by a missing module.

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

## Status: 7 written, and the last four should NOT be invented

Written and compiling clean on the PDP-11, each to an interface and a
data contract derived from the recovered code or the manual:

    WRTLM  WRTBR  TREE  TASKY  TABGET  TSKLNK  BLKSKP

**The remaining four are not called by anything.** `APLDBD`, `APMDIO`,
`APPRIO` and `WRTDAT` appear in FPS's §9.14 overlay descriptor but are
referenced by none of the recovered 40 and none of the 7 above. Their
placement is all the evidence there is:

    R1:    .MAIN. APLDBD LIB LOAD ERRMES      root, always resident
    R3:    WRTDAT WRTLM WRTBR LDBMAK WRTLIN   root, the writers
    LMBS1: SRCN SRC1 SRC2 BLNKST COMPOS APPRIO
    TWIG2: APMDIO

That places `APLDBD` with the loading core, `WRTDAT` with the load-module
writers, and `APMDIO` on its own twig — suggestive, not a specification.
Writing them from that would be **invention**, which is the opposite of
the goal: their contracts cannot be derived, so anything produced would
be plausible code that no evidence constrains.

**So the next step is `.MAIN.` and a link, not four more modules.**
Nothing calls the four, so a hybrid LOD100 links without them:

    40 recovered modules + the 7 written + .MAIN. + LIB100

`.MAIN.` *is* constrained — the command set is manual §2.3, its dispatch
targets (`LIB`, `LOAD`, `OUTPUT`, `INIT`, `FINISH`, `MDOFF`, `MMAX`,
`NOLOAD`, `PSOFF`, `MARK`, `PURGE`, `LOADMP`) are all present in the
recovered source with known signatures, and `LOD100C.CMD` fixes its task
build at `UNITS=17`, `ACTFIL=8`.

Should the four turn out to be needed at link time, the honest form is a
stub that reports "not recovered" rather than a guess.

## COMAND's list: 34 commands, and the manual documents 25

`COMAND (IFLAG,STR,MAXLEN)` returns the index of a command in its
`CMNDS` list, so that list's **order is `.MAIN.`'s dispatch order**:

     1 LO   2 MAP  3 XX   4 HE   5 LIN  6 EX   7 F    8 OU   9 C
    10 LF  11 OV  12 N   13 LM  14 PP  15 DE  16 B   17 INI 18 LIB
    19 A   20 MD  21 PS  22 PM  23 MM  24 R   25 INP 26 EC  27 DU
    28 TR  29 MO  30 HS  31 TA  32 PR  33 MAR 34 PU

Matching them against manual §2.3 accounts for 24: `LO`ad, `MAP`,
`EX`it, `F`orce, `OU`tput, `C`all, `OV`erlay, `N`oload, `LM`id, `PP`a,
`INI`t, `LIB`, `MD`off, `PS`off, `PM`ax, `MM`ax, `R`adix, `INP`ut,
`TR`ee, `MO`de, `TA`sk, `PR`i, `MAR`k, `PU`rge.

**Ten are undocumented**: `XX`, `HE`, `LIN`, `LF`, `DE`, `B`, `A`, `EC`,
`DU`, `HS`. Two can be guessed from the recovered code — `EC` sets
`EKOFLG`/`EKOLUN`, an echo of input, and `LIN` pairs with `LINKS`/
`LINKUP` — but the rest have no evidence at all.

That matters for `.MAIN.`: a faithful dispatch has **34 branches**, not
25, and the ten undocumented ones must reach *something*. The honest
form is a branch that reports the command as unimplemented rather than
one that silently does nothing, so a command file using one fails
loudly instead of producing a quietly wrong load module.

## Cross-check against the other manuals

Asked to certify consistency, so: **the manuals agree with each other.**
Where anything disagreed it was this project's notes.

- **Overlay table entry** -- Loader 2-1 and Supervisor 2-2 both say
  **eight MD words**. My "16 words" was host words; see above.
- **TCB** -- Loader table 2-2 and Supervisor table 2-1 are **identical**,
  both listing sixteen fields, and both state *"each entry consists of
  one MD word"*. CLAUDE.md's summary listed eleven and omitted `TYPE`
  (4), `ANSKEY` (6), `LSTMSG` (12) and `ICLOCK` (15) -- enough to put
  every field after word 3 at the wrong offset. Corrected.
- **The MD word unit is consistent everywhere**: overlay entries, TCB
  entries and `FSLMLD`'s "32 BITS OF HOST PER MD WORD" all agree, which
  is what makes the host-word/MD-word distinction the thing to check
  first when a count looks doubled.



With these written, LOD100 can be built from **40 modules of genuine FPS
source** plus 11 written ones, against the LIB100 that already exists —
and FPS's own §9.14 overlay descriptor becomes usable nearly unmodified,
removing the last adaptation from the recovered `LOD10.CMD`.
