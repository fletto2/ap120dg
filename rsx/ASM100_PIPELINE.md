# Validating the reconstruction against a 1981 binary

The FDUTIL reconstruction can be checked against ground truth: build the
*original* ASM100 assembler on a real PDP-11, link it against a LIB100
containing the reconstruction, assemble a source that shipped on the
tape, and compare the object it produces with the object that shipped
beside it.

**Result: byte-identical, on two sources.**

| source | modules | errors | vs shipped |
|---|---|---|---|
| `SYMSRC.APS` -> `SYMLIB.APO` | 66 | 0 | identical (7199 bytes) |
| `DGNSRC.APS` -> `DGNLIB.APO` | 11 | 0 | identical (10592 bytes) |

sizes after stripping the trailing spaces RSX pads onto output records.

`SYMSRC` is only `$EQU` constant definitions, so on its own it proves
little about the assembler -- it never emits an instruction. `DGNSRC` is
the diagnostic library: real AP microcode, so instruction encoding,
symbol resolution, relocation records and multi-block modules are all
exercised. It is also the library whose `APFET` module carries two
`***CODE` blocks, the case that exposed a relocation bug in `lnk100.py`.

Either way the run exercises `INFILE`, `PAKS` and `DATTIM` from the
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
