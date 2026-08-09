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
