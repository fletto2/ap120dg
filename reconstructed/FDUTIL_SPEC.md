# FDUTIL — recovered specification

`FDUTIL.FTN` is the one LIB100 component missing from the FPS-100 tape.
`LNK10.CMD` and `LOD10.CMD` both state "LIB100 MUST BE BUILT AND IN PLACE",
so it blocks building either reconstructed tool against the real library.

Nothing of FDUTIL itself survives. But **every one of its callers does**, and
128 call sites across 848 KB of source constrain it tightly. This document
is what those call sites establish.

## Why it exists at all

FPS split each layer into host-independent and host-dependent halves, and
said so in the file headers:

    IAPEX  = HOST INDEPENDENT APEX
    FDAPEX = HOST DEPENDENT APEX
    IUTIL  = INDEPENDENT UTILITIES
    FDUTIL = (host-dependent utilities, by the same convention)

So FDUTIL is *by design* the host-specific utility layer. The decisive
evidence is that **IUTIL — the independent half — calls `WRTLIN` and
`DATTIM` rather than doing its own I/O**. Anything that touches the
operating system was pushed down here.

That also means much of FDUTIL would have to be rewritten for a DG Nova
port regardless, exactly as `DAPEX.MAC` was.

## How the contents were determined

Two independent methods, agreeing:

1. **ODL module lists.** `ART10`, `MEM10`, `PTH10` and `UFT10` name LIB100
   modules explicitly, e.g.
   `RT11: .FCTR LB:LIB100/LB:APINIT:DAPEX:APMODE:DUTIL`.
   43 modules are named; 37 resolve to surviving sources.
2. **Unresolved references.** `LED10.CMD` builds LED100 as
   `LED100=LED100,LB:LIB100/LB` — its own object and LIB100, nothing else.
   Any symbol LED100 references and does not define must be in LIB100, and
   six of LIB100's seven components survive.

## Entry points

`lun = -1` means the user terminal throughout (`DATA VTTY/-1/`).

### File and terminal I/O — host-dependent

| routine | form | sites |
|---|---|---|
| `INFILE(op,file,lun)` | function → status, 0 = success | 77 |
| `WRTLIN(str,lun,len)` | write a string | 82 |
| `RDLIN(str,lun,len)` | function → status | 3 |
| `POSN(op,iv,lun,ierr)` | file positioning | 2 |
| `DATTIM(buf)` | date and time into buf | 2 |

`INFILE` is the whole file interface in one routine. Its operation codes are
named in VFC100's own DATA statement:

    DATA VR,VW,VRW,VCLOSE,VDEL,VREW,VSCR /1,2,3,4,5,6,7/

    1 VR      open for read
    2 VW      open for write
    3 VRW     open read/write
    4 VCLOSE  close
    5 VDEL    delete
    6 VREW    rewind
    7 VSCR    scratch

ASM100's usage is consistent with every one of those readings:

    IL = INFILE (1,SFILE,SLUN)    open source for read
    IL = INFILE (2,BFILE,OLUN)    open object for write
    ID = INFILE (4,SFILE,SLUN)    close source
    ID = INFILE (5,TFILE,TLUN)    delete temp
    IL = INFILE (6,TFILE,TLUN)    rewind temp
    IL = INFILE (7,TFILE,TLUN)    scratch temp

`WRTLIN` examples showing the terminal convention and the file case:

    CALL WRTLIN(PROMPT,-1,80)        DBG100, to the terminal
    CALL WRTLIN(MSG,VWTTY,80)        IUTIL, to the terminal
    IF (LUN.GT.0) CALL WRTLIN(MSG,LUN,RECSIZ)   IUTIL, to a file

### String handling — host-independent

| routine | form | sites |
|---|---|---|
| `PAKS(src,dst,6)` | pack a 6-character symbol | 8 |
| `UPAKS(src,dst,6)` | unpack a 6-character symbol | 10 |
| `LENS(str)` | function → current length | 2 |

Both packers are always called in place with a length of 6:
`CALL PAKS (SYM,SYM,6)`. Whether the packing is RAD50 or two characters per
word is not determined by the call sites; RSX supplies `IRAD50`/`R50ASC` if
it is the former.

### Load module construction — shared with LOD100

| routine | form | sites |
|---|---|---|
| `WRTLM(...)` | 11 args in the main form | 16 |
| `WRTBR(1,BUFFER,LEN,1,0,DUMMY,DUMMY)` | 7 args | 4 |
| `TREE(STRTRE,IPTR,RADIX,0,SYM)` | 5 args | 1 |
| `TASKY(STR,IPTR,1,RADIX)` | 4 args | 1 |
| `BLKSKP(STRX,IPTRX,IDENT)` | 3 args | 1 |
| `TSKLNK` | no parenthesised call seen | 1 |

**All six of these appear verbatim in LOD100's overlay descriptor**
(INSTAL.TXT §9.14), so FDUTIL and LOD100 share source. Reconstructing
either advances the other.

`WRTLM`'s main form is

    CALL WRTLM (1,DT,RPTCNT,ADDR,0,VALVEC(1),VALVEC(2),...)

which maps onto the type-1 data block record in the Loader manual §4.2.2 --
`[valtyp, repcnt, addr, 0, value-a, value-b, value-c, value-d]` -- the
record `lod100.py` already emits. **This mapping is inference, not
established**: it fits the argument order and count exactly, but no
surviving document states it.

`DUTIL` appears only in ODL module lists and is never called in 848 KB of
source, so it is most likely the object module name for FDUTIL itself,
which the ODLs reference to place it in a chosen overlay segment.

## Callers

Every caller survives except the two tools we are reconstructing.

| source | size | sites |
|---|---|---|
| LED100.FTN | 339 KB | 73 |
| VFC100.FTN | 55 KB | 37 |
| DBG100.FTN | 116 KB | 13 |
| IUTIL.FTN | 83 KB | 4 |
| ASM100.FTN | 256 KB | 1 |

plus ART100, MEM100, PTH100 and UFT100, which name FDUTIL modules in their
overlay descriptors.

**Missing callers: LNK100 and LOD100** — so any entry point used *only* by
those two is invisible to this analysis. The list above is a lower bound.

## What is not recoverable this way

Argument *types* are only partly constrained; the call sites give counts and
usage but a reconstruction has to pick representations. Return conventions
are known only where a result is tested (`INFILE(...).NE.0`).

The remaining route to certainty is a binary: `LBR` preserves insertion
order, and `UTL10.CMD` inserts `IUTIL,FDUTIL,ADUTIL,DGNHSR`. A surviving
`LIB100.OLB`, or any `.TSK` linked against it, would give FDUTIL's routines
in original order with their sizes, and disassembly would supply the bodies.
No such binary exists in either workspace — worth asking the community for
any RSX-11M pack from a site that ran an FPS-100.
