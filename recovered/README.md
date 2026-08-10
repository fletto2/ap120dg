# Recovered from the tape: LOD100's source

`LOD100.FTN` is one of the nine files this project treated as lost. It is
not lost. **6,297 lines of it survive inside the file named
`[327,010]LED100.FTN`**, which is mis-bounded on the tape image.

## What that file actually is

`LED100.FTN` is 338,928 bytes -- larger than ASM100.FTN, for a tool whose
manual says its "sole function is to streamline libraries for the
loader". It contains three things:

1. **lines 1-347** — LED100's own damaged tail: the header is gone (the
   file opens with a bare `O`, and line 2 starts mid-sentence), leaving
   some comments plus `CPYSBR` and `TYPC`. → `LED100_FRAGMENT.FTN`
2. **lines 348-6644** — **LOD100's source**, 41 subprograms, alphabetical
   from `BLNKST` to `SRCN`, cut mid-`COMMON /LDTABS/`.
   → `LOD100_RECOVERED.FTN`
3. **lines 6645-7314** — the tape's own long-form index, running through
   `===== FILE 68 =====` … `===== FILE 192 =====` to `END OF TAPE`.

The source identifies itself in every subprogram banner:

    C    *    THIS VERSION OF APLOAD WAS PRODUCED BY CROCK
    C    *    ON TUE, JAN 08 1980 FOR THE PDP11 COMPUTER AT 16:26:32

APLOAD is the loader. **40** of the 54 modules named in LOD100's own overlay descriptor
(INSTAL.TXT §9.14) are present. (An earlier count said 41: `TYPC`
appears in this file but its banner reads **APLED**, so it is the
library editor's same-named utility from the LED100 head, not
LOD100's. LOD100's own `TYPC` sorts after `SRCN` and is in the lost
tail.) The 13 absent ones are exactly
what truncation predicts: `.MAIN.`, `APLDBD`, `APMDIO`, `APPRIO`,
`BLKSKP` sort *before* `BLNKST`; `TABGET`, `TASKY`, `TREE`, `TSKLNK`,
`WRTBR`, `WRTDAT`, `WRTLIN`, `WRTLM` sort *after* `SRCN`.

## This corrects the forensics on record

"Every payload byte belongs to a named file; 0 orphan bytes" is true
byte-wise, but that accounting never checked the **boundaries**. At least
one is wrong, straddling a real file break and swallowing the tape index.
**Other "missing" files are worth re-examining the same way.**

## It compiles, cleanly, on the real machine

    FOR LODREC=LODREC/-I4/-SN
    -> LODREC.OBJ, 156,522 bytes, ZERO diagnostics

40 complete program units (the 41st, `SRCN`, is the one cut mid-`COMMON`;
the file here is trimmed to the last complete `END`). A clean compile of
274 KB of FORTRAN is conclusive: the extraction boundaries are right and
the source is uncorrupted. Reproduce with `rsx/lod100_recovered_compile.ini`.

## What it needs that is not here

Of LOD100's own modules, 8 are referenced but absent: `BLKSKP`, `TABGET`,
`TASKY`, `TREE`, `TSKLNK`, `WRTBR`, `WRTLIN`, `WRTLM` -- plus `.MAIN.`,
`APLDBD`, `APMDIO` and `APPRIO`, which nothing here calls but the task
needs. **LIB100 as we build it already supplies 40 of the 47 library
primitives** the source uses (`EXTVT`, `SRCST`, `INSST`, `RPLVT`,
`EXTTOK`, `STOI`, the `I*16` arithmetic, and FDUTIL's `INFILE`/`RDLIN`/
`PAKS`/`UPAKS`). Only `IOVS`, `SYM2`, `VALVEC`, `COMSYM`, `SFILE` and
`SFILE1` are unaccounted for.

## What it settles about the reconstruction

`reconstructed/LOD100.FTN` is an independent reimplementation and shares
only 9 subprogram names with the original -- the decompositions differ.
But the original answers a question the reconstruction could not:

**Symbols are not scoped by segment at all.** Every lookup in the real
loader is

    SRCST (ENTDTA,1,-1,SYM,6)

-- the whole entry table, index 1 to end, no segment filter anywhere.
CLAUDE.md records the "1 word of 3880" difference as an open semantic
question: the FORTRAN reconstruction resolves a symbol defined in a
parent segment, `lod100.py` does not. **The FORTRAN was closer and
`lod100.py` was wrong; the original is more permissive than either.**
