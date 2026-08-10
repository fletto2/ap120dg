# Target machine: the PDP-11/44, and a SimH config that matches it

The FPS-100 is going onto Usagi Electric's PDP-11/44. This records that
machine's configuration, a SimH setup that mirrors it, and what still
has to change before an image built here will boot there. Intended as
the basis for a PiDP-11 SD card image.

## The machine

From the build videos (`transcripts/`, the 80 MB drive and format
episodes) -- this is the hardware, not something inferred here:

| | |
|---|---|
| CPU | PDP-11/44, processor spread across ~8 cards |
| options | Commercial Instruction Set (CIS), floating point |
| memory | 4 MB, 22-bit addressing (was 1 MB, rest on hand in cards) |
| fixed disk | Fujitsu 2312 -- 8-inch SMD, 84 MB (sold as 80 MB) |
| disk controller | Emulex SC12, quad-height Unibus, SMD-to-Unibus |
| presented as | **two RK07 and one RK06** behind an emulated RK611 |
| device names | `DM0:` `DM1:` `DM2:` -- `DM0:` is an RK07, label `USAGI0` |
| tape | TU58 |
| planned | 16 serial lines; DEUNA or DELUA for networking |
| OS | RSX-11M -- required, the FPS software targets it |
| accelerator | FPS-100, ~8 MFLOPS SIMD |

The SC12 splits one 84 MB SMD spindle into RK611 units because no single
RK06 or RK07 is that large: an RK07 is about 27 MB, an RK06 about 14.

## SimH configuration

The 11/44 is Unibus, which matters: **an 11/73 will not do**. Setting
`cpu 11/73` makes SimH disable RK, HK and TM as Q-bus-incompatible, and
`set hk enabled` then fails with "not compatible with system bus". On the
11/44 they stay available.

    set cpu 11/44
    set cpu 4M                  ; reports 4088KB -- 4 MB less the I/O page
    set cpu fpp                 ; floating point; TKB needs it
    set hk enabled              ; RK611 -- this is RK06/RK07, NOT "rk"
    set hk0 rk07                ; DM0:  USAGI0
    set hk1 rk07                ; DM1:
    set hk2 rk06                ; DM2:
    att hk0 usagi0.dsk
    att hk1 usagi1.dsk
    att hk2 usagi2.dsk

SimH's `RK` device is the RK11/RK05 and is a different controller
entirely. `HK` is the one that matches the Emulex's emulation.

Capacities, which is the practical win: an RK07 is **53,790 blocks**
against RK05's 4,800. Every "disk full" and `ALLOCATION FAILURE ON FILE`
seen while building the FPS tools on an RK05 scratch volume disappears
at that size.

## What does not work yet, and why

**The RSX-11M V3.1 BL22 pack in `rsx/` has no RK611 driver.** Booted on
the 11/44 with all three HK units attached, `DEV DM:` answers

    DEV -- DEVICE NOT IN SYSTEM

so the drives are invisible to it. That pack was SYSGEN'd for RK05 only
-- consistent with `DEV` showing no magtape and no paper tape either.
Using RK06/RK07 needs a SYSGEN that includes the DM: driver. The videos
show the same conclusion reached on the real machine: the working RSX
came from a Unibone-hosted install copied onto the Fujitsu, after a
"prep gen" configuration session, rather than from the stock pack.

**4 MB does not raise the per-task limit.** RSX still reports
`124K MAPPED` on a 4 MB machine, because that is the size the pack was
generated for. More importantly a task is capped at 32K words -- 64 KB --
by the 16-bit virtual address space, whatever the machine holds. That is
the ceiling LOD100 keeps hitting; RAM does not move it. What would:

- **separate I- and D-space**, which the 11/44 supports, giving 64 KB of
  instructions plus 64 KB of data. Needs a task builder that can emit it
  (RSX-11M-PLUS or M V4.x; the V3.1 pack here cannot).
- a deeper overlay tree, which is what the original LOD100 did --
  INSTAL.TXT 9.14 is a far deeper tree than the reconstruction's four
  branches.

## For a PiDP-11 image

The PiDP-11 front panel maps to SimH's PDP-11, so this configuration
transfers directly. Outstanding work before an image is useful:

1. An RSX-11M SYSGEN with the DM: driver, so RK06/RK07 volumes mount.
2. `ods1make.py` currently builds RK05-geometry volumes only. It needs
   RK07 (53790 blocks) and RK06 (27126) geometry to populate the target
   disks directly.
3. Decide the RSX version. V3.1 is what the FPS software was written
   against and what is on the tape's install notes; M-PLUS would relieve
   the 64 KB pressure but is not what FPS shipped for.

## Replica configuration

`rsx/usagi1144.ini` is the machine above as SimH sees it, and it
validates clean:

| transcript hardware | SimH | note |
|---|---|---|
| PDP-11/44 | `set cpu 11/44` | Unibus -- an 11/73 disables RK/HK/TM |
| 4 MB | `set cpu 4M` | reports 4088KB |
| floating point | `set cpu fpp` | TKB needs it |
| commercial instruction set | `set cpu cis` | |
| Emulex SC12 as RK611 | `set hk enabled` | **HK is RK06/RK07; RK is RK05** |
| two RK07, one RK06 | `set hk0 rk07` / `hk1 rk07` / `hk2 rk06` | DM0:/DM1:/DM2: |
| TU58 | `set tdc enabled` | two units |
| 16 serial lines | `set dz enabled` + `lines=16` | exactly 16 |
| DELUA | `set xu enabled` | XU defaults to DELUA already |

## SYSGEN: the kit, and how far it gets

The V3.1 pack cannot be system-generated -- `EXEMC`, `RSX11M.OLB`,
`SYSVMR`, `RSXMC` and `SYSGEN` are all absent from it. It is a 2.3 MB
pre-built running system, not a distribution.

bitsavers carries full distributions at
`bits/DEC/pdp11/rsx11m/`:

- `rsx11m40.zip` (5.2 MB) -- **RSX-11M V4.0**, five RL02 images:
  `rsxm32` (system), `excprv`, `mcrsrc`, `rlutil`, `hlpdcl`
- `rsx11m42.zip` (5.9 MB) -- V4.2 as a magtape kit, installs to MSCP

The V4.0 RL02 set is the easier route and **it boots on this replica**:

    RSX-11M V4.0 BL32   28.K (BASELINE)

reaching MCR after answering the date and terminal width. RL02 is an
RL11, which is fine on the Unibus 11/44.

`DEV DM:` on the baseline still answers *device not in system* -- the
baseline is deliberately minimal and the DM: driver is what SYSGEN adds.
So the route is confirmed but the generation itself is still to do.

Two reasons to want V4.x rather than a V3 pack:

1. **RK06/RK07 support**, which is the whole point -- an RK07 is 53,790
   blocks against RK05's 4,800, and the FPS tool builds keep running a
   4,800-block scratch volume out of space.
2. **Separate I- and D-space**, which the V4 task builder can emit and
   the 11/44 supports. That is the one thing that would lift LOD100 past
   its 64 KB ceiling; no amount of memory or SYSGEN tuning otherwise
   does, because the limit is the 16-bit address space.

Against that, FPS wrote for V3.2 (INSTAL.TXT says so on every page), so
anything built under V4 needs re-checking against the install notes.

The RK07 attach wrinkle noted earlier is resolved: it was stale
container files left from a run before the geometry was set, not a
configuration fault. On a clean file the drive comes up correctly --
`sectors=22, heads=3, cylinders=815`, which is 53,790 blocks.

### The V4.0 kit has everything the generation needs

Scanning the five RL02 images for the components the V3.1 pack lacks:

| image | carries |
|---|---|
| `rsxm32` | `SYSGEN`, `RSXMC`, `EXEMC`, **`SYSVMR`**, `RSX11M` |
| `mcrsrc` | `SYSGEN`, `RSXMC`, `EXEMC`, `RSX11M`, **`DMDRV`** |
| `excprv` | `SYSGEN`, `RSXMC`, `EXEMC`, `RSX11M`, **`RK611`** |
| `hlpdcl` | `SYSGEN`, `RSXMC`, `EXEMC`, `RSX11M` |
| `rlutil` | `SYSGEN`, `RSX11M` |

`DMDRV` is the DM: driver and `RK611` its controller support -- exactly
what has to be selected during the generation to make the RK07/RK06
volumes usable. Compare the V3.1 pack, where `EXEMC`, `SYSVMR`, `RSXMC`
and `SYSGEN` are all absent.

So the generation is viable, and it is the next piece of work. It is a
long interactive dialogue rather than a command file, so it wants to be
approached as its own task: boot `rsxm32` on the replica, run `@SYSGEN`,
and answer for an 11/44 with 4 MB, DM: on an RK611, DZ11 with sixteen
lines, a DELUA and a TU58.

## Starting the generation

Entry point, confirmed working on the replica:

    boot rl0                      ; rsxm32 -- RSX-11M V4.0 BL32 BASELINE
    >INS $PIP                     ; the 28K baseline has almost nothing installed
    >SET /UIC=[200,200]           ; NOT [1,2] -- SYSGEN.CMD lives here
    >@SYSGEN

which answers

    ; RSX-11M V4.0 BL32   System Generation PHASE I -- version 1.53
    ; RL01 distribution kit
    *  3. Do you want to inhibit execution of MCR commands? [Y/N]:

`[200,200]` on `rsxm32` holds `SYSGEN.CMD`, `SYSGEN2.CMD`, `SYSGEN3.CMD`,
`SGNPARM.CMD`, `SGNBLDDRV.CMD`, `SGNKLAB.CMD`, `SGNSTAND.CMD` -- the
standard three-phase generation: phase I builds the executive, II the
privileged tasks and drivers, III the utilities.

Two SimH conflicts to clear first, both found here:

- **`rl4` does not exist** -- SimH's RL has four units, so `hlpdcl.dsk`
  cannot be mounted alongside the other four. It is the help/DCL disk and
  is not needed for the generation.
- **`TDC` (TU58) collides with `SLU8`** at 017776500 and the boot fails
  with an address conflict. Leave TDC out of the generation configuration
  and add it afterwards.

The questions are numbered, so the dialogue can be scripted -- but it is
several hundred questions over three phases plus long build steps, and a
wrong answer means starting again. The answers that matter for this
target: 11/44, 4 MB, DM: on an RK611, DZ11 with sixteen lines, DELUA,
TU58.
