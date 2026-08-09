# Validating the reconstruction against a 1981 binary

The FDUTIL reconstruction can be checked against ground truth: build the
*original* ASM100 assembler on a real PDP-11, link it against a LIB100
containing the reconstruction, assemble a source that shipped on the
tape, and compare the object it produces with the object that shipped
beside it.

**Result: all nine libraries reproduced. 376 modules, 0 errors.**

| source | modules | vs shipped |
|---|---|---|
| `SYMSRC` -> `SYMLIB` | 66 | identical |
| `DGNSRC` -> `DGNLIB` | 11 | identical |
| `APFSRC` -> `APFLIB` | 34 | identical |
| `UTLSRC` -> `UTLLIB` | 39 | identical |
| `IPRSRC` -> `IPRLIB` | 13 | identical |
| `AMLSRC` -> `AMLLIB` | 33 | identical |
| `BABSRC` -> `BABLIB` | 60 | identical |
| `SIGSRC` -> `SIGLIB` | 32 | identical **except `***FPB`** |
| `BAASRC` -> `BAALIB` | 88 | identical **except `***FPB`** |

sizes compared after stripping the trailing spaces RSX pads onto output
records.

## The two that differ are the tape's inconsistency, not the pipeline's

`SIGLIB.APO` and `BAALIB.APO` mark their parameter blocks `***FPB`;
everything this ASM100 produces marks them `***PB`. Replace one string
with the other and both become byte-identical -- the byte counts confirm
it, SIG short by exactly 26 and BAA by exactly 88, which are the counts
of the marker.

ASM100 REL 1.00 -- the source that shipped on this same tape -- can only
write `***PB`: there is one FORMAT for it, at line 1384,
`5005 FORMAT ( 4X,2H12,1X,6A1,6X,5H***PB)`, and the string `FPB` does not
occur anywhere in the file.

The decisive evidence is internal: `BABSRC` uses `$PARAM` 59 times and
its shipped object carries 59 `***PB`, matching REL 1.00 exactly, while
`BAASRC` uses it 88 times and its shipped object carries 88 `***FPB`.
Same tape, same pseudo-op, different marker. So `SIGLIB` and `BAALIB`
were assembled by a **later ASM100 than the one distributed beside
them**. `lnk100.py` already accepted both spellings, which is why this
had never surfaced.

`SYMSRC` alone would prove little -- it is only `$EQU` definitions and
never emits an instruction. The rest are real microcode, so instruction
encoding, symbol resolution, relocation records and multi-block modules
are all exercised, including `APFET` with its two `***CODE` blocks, the
case that exposed a relocation bug in `lnk100.py`.

Every run exercises `INFILE`, `PAKS` and `DATTIM` from the
reconstruction; a defect in any of them changes or prevents the output.

## The build

`ASM10.CMD` on the tape is the original procedure and carries ASM100's
own overlay descriptor as `.DATA` lines -- extract them, strip the
`.DATA ` prefix, and point `LB:'$LUIC'LIB100` at wherever LIB100 lives.

    FOR ASM100=ASM100/-I4/-SN/-VA      ! switches matter, see below
    FOR IUTIL=IUTIL/-I4/-SN/-VA
    FOR FDUTIL=FDUTIL/-I4/-SN/-VA
    MAC ADUTIL=ADUTIL
    LBR LIB100/CR:1000:256:256
    LBR LIB100/IN=IUTIL,FDUTIL,ADUTIL
    LBR ASM100/CR:1000:256:256
    LBR ASM100/IN=ASM100
    TKB @ASM100                        ! ASM100.CMD: ASM100/CP,ASM100=ASM100/MP
                                       !             UNITS=12 / ACTFIL=6 / //

Drive it with an RSX indirect file (`@DK1:BUILD`) rather than a chain of
SimH `expect` rules: two console commands instead of twenty, and no
races. This is how FPS drove it too.

## Things that cost time

- **The compiler switches are not optional.** `SETUP.CMD` sets
  `$FOR1 = "/-I4/-SN/-VA"`. Without them TKB reports
  `SEGMENT ... HAS ADDRESS OVERFLOW: ALLOCATION DELETED` on the leaf
  overlays. With them ASM100 builds clean at 186 blocks.
- **`LBR /CR:1000:256:256`.** The defaults, and `/CR:400:200:60`, give
  `EPT OR MNT EXCEEDED` -- IUTIL alone is 62 modules. Values above ~256
  are rejected as `ILLEGAL SWITCH`. LIB100's original `/CR` parameters
  are lost with `LIB100.CMD`, one of the nine files missing from the tape.
- **Tape sources carry trailing NUL padding.** FORTRAN reads it as a
  spurious `.MAIN.` program unit and fails on line 1. Strip it on the way
  into the volume; the archive must stay byte-identical to the tape.
- **`ods1make.py` needed multi-extent files.** A retrieval pointer holds
  count-1 in one byte, so one extent caps at 256 blocks; ASM100.FTN is
  527.
- **A task image must be contiguous**, so a built `.TSK` cannot be copied
  onto a fresh volume and run -- `INS -- FILE NOT CONTIGUOUS`.

## LNK100 and LOD100 under their own command files

`INSTAL.TXT` 9.13 and 9.14 give `LNK10.CMD` and `LOD10.CMD` verbatim, and
both reconstructions now build under them, against a real LIB100:

    FOR LNK100=LNK100/-I4/-SN/-VA          ! $FOR1
    TKB @LNK100                            ! LNK100/CP,LNK100=LNK100,LIB100/LB
                                           ! / , UNITS=12 , //   -- no ODL
    FOR LOD100=LOD100/-I4/-SN              ! $FOR2, note: no /-VA
    LBR LOD100/CR:1000:256:256
    LBR LOD100/IN=LOD100
    TKB @LOD100C                           ! LOD100/CP,LOD100=LOD100/MP
                                           ! UNITS=17 , ACTFIL=8 , //

LNK100.TSK comes out at 66 blocks with **no** overlay descriptor, which is
what `LNK10.CMD` implies -- the original fit unaided and so does this.
LOD100.TSK is 145 blocks under its ODL, which `LOD10.CMD` does supply.

**These two files independently confirm the FDUTIL unit mapping.**
`LNK100.CMD` asks for `UNITS=12` and `LOD100.CMD` for `UNITS=17`. Under
the file-number+7 rule those are exactly the highest unit each tool can
reach: LNK100 uses file numbers up to 5, LOD100 up to 10. Nothing else
explains why a linker would need seventeen logical units.

**Open**: running LNK100 on the assembled objects is not working yet. A
bare `L DGNOBJ.APO` fails with `NO SUCH FILE` from `LODFIL`, and
`L DK1:DGNOBJ.APO` gets past the lookup but then hangs without reaching
`LOAD COMPLETE`. So the reconstruction's `ASSIGN`-plus-implicit-open path
behaves differently from ASM100's `ASSIGN`-plus-explicit-`OPEN`, and it
does not pick up `SY:`. That is the next thing to chase.

## The full chain, on the real machine

    DGNSRC.APS  --ASM100-->  DGNOBJ.APO  --LNK100-->  DGNLNK.LM
                             identical to               identical to
                             shipped DGNLIB.APO         lnk100.py (283 lines)

ASM100 is built from tape source; LNK100 is the reconstruction built
under `LNK10.CMD`; both link LIB100, which carries the reconstructed
FDUTIL. `LNK DGNLNK.LM=DGNOBJ.APO` reports `HIGH= 431` -- octal 431 is
281, and DGNLIB has 282 instructions -- and 3 undefined symbols, which
are `ILOG2`, `CFFT` and `!ONE`, exactly what `lnk100.py` reports for the
same input.

### Driving LNK100

`LNK100` uses the manual's **two-line** dialogue: the command letter on
one line, its argument on the next. Sending `L DGNOBJ.APO` on a single
line makes it take `L` and then read the *following line* as the
filename, which is why it reported `NO SUCH FILE` naming a file that was
plainly there, and why a lone `L` hung -- it was waiting for the argument
line. LOD100, by contrast, takes command and argument on one line.

Better still, install it and use the command line, which avoids the
console send queue entirely:

    INS LNK100.TSK/TASK=...LNK
    LNK DGNLNK.LM=DGNOBJ.APO

`LOAD` now opens through `INFILE` rather than a bare `ASSIGN`. A bare
`ASSIGN` with no `OPEN` leaves the unit unconnected, and the first READ
then either reports no such file or falls back to the terminal and blocks
forever. Using INFILE is also what `LNK10.CMD` implies by linking LIB100.
