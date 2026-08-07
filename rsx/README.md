# PDP-11 FORTRAN kits for building FPS-100 host software

The FPS-100 host tools (ASM100, SIM100, DBG100, LED100, VFC100, and the lost
LNK100/LOD100) are PDP-11 FORTRAN programs built under RSX-11M. To compile
any of them -- original or reconstructed -- you need a PDP-11 FORTRAN
compiler, which was a separately licensed layered product and is therefore
not part of a base RSX-11M distribution.

These are the compiler kits. **The DEC images themselves are not
redistributed here** -- run `./fetch_kits.sh` to download them from bitsavers
and verify them against the checksums below.

## Which compiler does FPS need?

Either FORTRAN IV or FORTRAN IV-PLUS. `FIRST.CMD` on the FPS tape probes for
both and prefers F4P:

```
.110: .IFINS F4P .GOTO 120
.120: .IFINS F4P  REM F4P
      INS $F4P/INC=44000
      .IFINS F4P  .GOTO 130
      ; F4P OR FOR CANNOT BE FOUND !!!  INSTALL ONE BEFORE RESUMING.
```

and carries a switch string for each:

```
.SETS $F4P2 "/CO:99./-TR/-I4"     ! FORTRAN IV-PLUS
.SETS $FOR2 "/-I4/-SN"            ! FORTRAN IV
.SETS $FOR1 $FOR2+"/-VA"
```

The shared `/-I4` is why a bare `INTEGER` in the FPS sources means
`INTEGER*2`. Because plain FORTRAN IV is accepted, **F4P is not required** --
`FOR` is sufficient.

## Contents

| file | what it is |
|---|---|
| `rsx31wStr11andFtn.dsk.gz` | RSX-11M 3.1 pack with **`FOR.TSK` already built and installed**, plus `SYSLIB.OLB`, `FOROTS.OBJ`, `FORNHD.OBJ`, `FORRES.MAC`. Needs no installation -- boot and compile. |
| `AN-1822C-BC_F4RSX_V2.2.dsk.gz` | FORTRAN IV V2.2 **distribution kit**: `FOR.OLB` plus the task-build procedures `FOR11M.CMD`/`FOR11M.ODL` (RSX-11M), `FOR11D.CMD` (RSX-11D), `FOR11U.CMD`, `FORIAS.CMD` (IAS), `FORVMS.CMD`, and the object-time system (`FOROTS`, `FOREIS`, `FOREAE`, `FORFIS`, `FORFPU`, `FORNHD`, `FORRES.MAC`). This is what you install onto an existing pack. |
| `pdp11-f77-rsx-v40-bin.rk.gz` | FORTRAN-77 V4.0 for RSX: `F77.OLB`, build procedures `F7711M.CMD`/`.ODL`, and the full `F4P*` object-time system including `F4POTS.OBJ`. Useful for its OTS; F77 itself is *not* what FPS targeted and differs from FORTRAN IV in DO-loop and Hollerith semantics. |

`FILE_INVENTORY.txt` lists the names recovered from each image. It is a
heuristic scan of blocks that parse as Files-11 file headers, with the ident
area decoded from RAD50 -- a lower bound, not an authoritative directory
listing. A proper listing needs a working ODS-1 reader or a booted system.

## Source and checksums

All three come from bitsavers:

<http://www.bitsavers.org/bits/DEC/pdp11/discimages/rk05/>

- [AN-1822C-BC_F4RSX_V2.2.dsk.gz](http://www.bitsavers.org/bits/DEC/pdp11/discimages/rk05/AN-1822C-BC_F4RSX_V2.2.dsk.gz) (152K)
- [rsx31wStr11andFtn.dsk.gz](http://www.bitsavers.org/bits/DEC/pdp11/discimages/rk05/rsx31wStr11andFtn.dsk.gz) (877K)
- [pdp11-f77-rsx-v40-bin.rk.gz](http://www.bitsavers.org/bits/DEC/pdp11/discimages/rk05/pdp11-f77-rsx-v40-bin.rk.gz) (220K)

Verified 2026-08-07, unmodified:

```
689aaec104dff33072dcdb4182e7ca7254899ea5a5477aef9b40ce02adda53ad  AN-1822C-BC_F4RSX_V2.2.dsk.gz
f6367a7ffa312c52fd1dc2f2b08daba0542d87c68c0ba66421d2645fef529602  pdp11-f77-rsx-v40-bin.rk.gz
bc025ae416b2d1728974ec0d89158ee90692d535d728bc769441a77111881291  rsx31wStr11andFtn.dsk.gz
```

All are RK05 images (2,457,600 bytes uncompressed; the F77 image is
2,482,176) and all are ODS-1 -- `DECFILE11A` appears in the home block.

These are DEC software distributions and are deliberately **not** committed
to this repository; they are build tooling, not part of the FPS-100
preservation set. `fetch_kits.sh` downloads and checksums them.

## Usage

```
./fetch_kits.sh          # download from bitsavers and verify
pdp11 boot_rsx.ini       # boot RSX-11M 3.1 with FORTRAN IV
```

Verified working: the pack boots to `RSX-11M V3.1 BL22  124K  MAPPED` on
volume `UWM`, and `[1,2]STARTUP` installs the compiler:

```
>TIM 12:00 07-AUG-86
>ACS DK0:/BLKS=150
>INS $EDI
>INS $PIP
>INS $FOR
```

so FORTRAN IV is available as `FOR` at the MCR `>` prompt.

**SimH console input does not come from stdin.** Piping text into the
simulator sends it to SimH's own `sim>` interpreter, not to the running
operating system. Use `expect`/`send` rules in the `.ini` instead, as
`boot_rsx.ini` does for the date prompt.

The RSX-11M v5.1.1 distribution used elsewhere in this work is not part of
this directory; it is a separate, much larger set of RL02 images.

## Caveats for the FPS build

- **Version skew.** FPS targeted RSX-11M v3.2 (Jan 1980). The ready-built
  pack here is v3.1. FCS and TKB are broadly compatible across those, but not
  identical, and the FPS command files assume v3.2 conventions.
- **Address space.** Everything must fit the PDP-11's 64 KB per-task limit,
  which is why LOD100 shipped with a three-branch overlay descriptor
  (recoverable from INSTAL.TXT §9.14) rather than as a flat task.
- **LIB100 is a prerequisite.** `LNK10.CMD` and `LOD10.CMD` both state
  "LIB100 MUST BE BUILT AND IN PLACE". `LIB100.CMD` is recoverable from
  INSTAL.TXT §9.6 and builds from IAPEX, DAPEX, FDAPEX, IUTIL, ADUTIL and
  DGNHSR -- all present on the tape except `FDUTIL.FTN`, which is missing
  and would need reconstructing from its callers.
