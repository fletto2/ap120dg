# FPS-100 install package

The 1981 distribution installs itself by **destroying its own sources as
it goes**. Nine files are missing from the surviving tape image, and six
of them are named by a `PIP ... /DE` in one of the install command files.

This package is that distribution as it would look if it had never done
that: everything the tape holds, plus what was lost, minus the deletions.

    python3 make_package.py          # rebuilds src/ and MANIFEST.txt

## What is in it

**190 files.** The 182 on the tape, plus seven that were lost and one
name repair. `MANIFEST.txt` classifies every one.

### Recovered verbatim — not guesses

`INSTAL.TXT` reproduces three of the lost command files in full. They are
transcribed, not reconstructed:

| file | source |
|---|---|
| `LIB100.CMD` | INSTAL.TXT §9.6 |
| `LNK10.CMD`  | INSTAL.TXT §9.13 |
| `LOD10.CMD`  | INSTAL.TXT §9.14 |

`LOD10.CMD` is the one adaptation: it generates FPS's own overlay
descriptor inline, naming *their* module decomposition (`APLDBD`,
`LMSRC2`, `RDREC`, `OUTSCN`, `SRCN` …). The reimplementation has a
different set of program units, so its own `LOD100.ODL` is used instead.
Everything else in the file, including `UNITS=17` and `ACTFIL=8`, is
verbatim.

### Reimplementations — clearly marked

These sources are genuinely gone. They are new code written from the
manuals and from their callers, **not** recovered FPS source:

| file | how it is checked |
|---|---|
| `FDUTIL.FTN` | the original ASM100, linked against a LIB100 carrying it, reproduces all nine shipped `.APO` libraries |
| `LNK100.FTN` | E module matches `lnk100.py`; its linked VADD+SPUFLT is byte-identical to the shipped BAAHSR block |
| `LOD100.FTN` | load module matches `lod100.py`, 1160 of 1160 words |
| `LOD100.ODL` | overlay descriptor for the reimplementation's own decomposition |

### Repairs

- **`DEVTABLE.MAC`** — the distribution index and `DRV100.CMD` both call
  for `DEVTABLE`, but the tape holds the name truncated to `DEVTAB.MAC`.
  Both names are present; the content is identical.
- **NUL padding trimmed from 92 sources.** Tape records are NUL padded
  and FORTRAN reads the padding as a spurious `.MAIN.` program unit that
  fails on line 1. `software/fps100sw/` keeps the untrimmed originals.

## The deletions

**49 deletions are commented out**, not removed — the original text stays
readable and the change is reversible. Each is prefixed `;RM;`:

    ;RM;  PIP IAPEX.*;1,DAPEX.*;1,FDAPEX.*;1,IUTIL.*;1,FDUTIL.*;1/DE

Where a line deleted sources *and* intermediates, it is replaced by one
that deletes only the intermediates:

    ;RM;  PIP ASM100.FTN;1,ASM100.MAP;*/DE
          PIP ASM100.MAP;*/DE

The interactive prompts (`DELETE HSR SOURCES`, `DELETE APEX AND
UTILITIES SOURCES`) are answered no by a `.SETF`, so an unattended
install keeps its sources. Note the originals skip the prompt entirely
when `$MAST` is set — `MASTER.CMD` sets it, so the authentic full
install deletes without asking.

**Two idioms had to be distinguished.** A deletion naming a source
extension (`ASM100.FTN;1`) and a wildcard against version *one*
(`IAPEX.*;1`, `FDUTIL.*;1`). Version 1 is what came off the tape, so
`;1` means the distribution copy; `;*` is used for libraries and build
intermediates and is deliberately left alone — those are hygiene, not
loss. Missing the second idiom left the very deletion that removed
`FDUTIL` in place.

## What this does not settle

The deletions **do not explain the tape**. `LIB100.CMD` deletes seven
files and six of them survive on the image; `PDS100.CMD` deletes five
more that also survive. This package names the deleting commands and
removes them. Why exactly those nine files are absent is still open.
