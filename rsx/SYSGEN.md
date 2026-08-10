# Driving an RSX-11M V4.0 SYSGEN under SimH

The V3.1 pack cannot be system-generated -- it is a pre-built running
system, not a distribution (see `PDP11_44_TARGET.md`).  A system matched to
the 11/44 target therefore has to be generated from the V4.0 kit
(`rsx11m40.zip`, five RL02 images).

SYSGEN is a console dialogue of well over a hundred questions, so it has to
be driven mechanically.  What follows is what actually works, and the traps
that each cost a full run to find.  A run from boot to the end of Phase I
setup takes roughly ten minutes of wall clock, so a trap that is only
visible at the end is expensive.

## Answer by question TEXT, never by position

The obvious harness -- replay a list of answers in order -- desynchronises
the moment a question is added or skipped, and SYSGEN skips questions
depending on earlier answers (answering `N` to autoconfigure skips question
2 entirely, so the numbering visibly jumps 1, 3, 4, ...).  After a
desynchronisation every later answer goes to the wrong question and the
result is silent nonsense.

Bind each answer to a distinctive fragment of its own question instead, one
one-shot SimH `expect` rule per question:

    expect "loating point processor" send after=15000000,delay=250000,"Y\r"; continue

A question with no rule simply stalls, and the log names it exactly.  That
turns each run into "reveal the next unknown question", which converges.

## The four traps that cost the most

**A leading `\r` shifts every answer one question late.**  It answers the
current prompt with its default and pushes the real answer onto the *next*
prompt.  This is subtle because the run still looks plausible -- the
answers are all accepted, just by the wrong questions.  The tell is an
answer appearing after a question it does not fit (`Y` on "inhibit
execution of MCR commands?").

**A leading space is not ignored.**  It was tried as a way to absorb the
first character, which SimH can drop after a match.  RSX rejects `" Y"` and
simply re-prompts.  The correct fix for the dropped character is timing --
a long enough `after=` for RSX to have posted its terminal read -- not a
prefix character.  Note the delay does not want to be *too* long either:
at `after=60000000` the run got measurably less far in the same wall clock.

**SimH's `expect` is case-sensitive, and SYSGEN's capitalisation is not
guessable.**  The prompt is `Extended instruction set (EIS) present?`, not
`Extended Instruction Set`.  Write every fragment starting one character
in (`loating point processor`, `arity memory`, `apping registers`) so the
case of the leading letter cannot matter, or anchor on a parenthesised
abbreviation like `(EIS)` / `(CIS)` which has fixed case.

**A fragment must be anchored to something only a live prompt emits.**  This
went wrong twice, both times producing a one-question shift that looked like
a harness bug:

- `ap device` also matches `listing/map device have at least 120 columns`,
  so that question got answered with a default and the real answer landed on
  the next one.
- `1920.K` also matches SYSGEN's own *printed example* of what a successful
  boot looks like -- its closing instructions contain the literal line
  `;       RSX11M V4.0 BL32     1920.K  MAPPED`.  Both post-boot rules fired
  on the documentation and were consumed long before the system booted.

SYSGEN's instructional text is always prefixed with `;`, so anchoring on the
preceding CR-LF distinguishes prose from output:
`expect "\r\nRSX11M V4.0 BL32"` matches the real banner and not the example.
Arming speculative rules ahead of the dialogue is still worth it -- `XDT`
landed for free -- but short fragments are how the shift comes back.

**`autosize` silently overrides the drive type** when a container already
exists: `set hk2 rk06` still autoconfigured as an RK07 because SimH sized
the drive from the file.  The obvious fix -- `set hkN noautosize` -- is a
TRAP, and a worse one: with it, `att -n` creates a 210-BLOCK STUB instead
of a full drive, so anything later written to that disk is silently lost.
See "SimH HK container traps" below.  Create each container fresh, in the
same session that uses it, with the type set and autosize left alone:

    set hk enabled
    set hk0 rk07 ; set hk1 rk07 ; set hk2 rk06
    att -n hk0 usagi0.dsk ...

RSX's own autoconfigure then reports the target exactly:
`DMA` at 177440 vector 210, units 0 and 1 RK07, unit 2 RK06.

## SYSGEN writes to the distribution disks

A second run that boots the half-generated `rsxm32` dies during SAV with

    SAV -- System may not boot correctly
    SYSTEM CRASH AT LOCATION 011520

before SYSGEN is even reached.  Keep a pristine extract of the kit
(`m40.orig/`) and restore the working copies from it at the start of every
attempt.  This is not optional; it is the default outcome of iterating.

## Do not `pkill -f` a path from an interactive shell

    pkill -9 -f "BIN/pdp11"

matches the command line of the very shell running it, so the wrapper kills
itself.  The visible symptoms are an odd exit code (144) and, worse, a
command chain that silently never runs its later steps -- one "relaunch"
never started at all, and a stale simulator survived the cleanup that was
supposed to remove it.  Use `pkill -x pdp11`, or issue the kill from a
process whose own command line does not contain the pattern.

**A stale simulator is genuinely destructive here.**  It keeps reading the
same `sysgen.ini`, writing the same `sysgen.log` and holding the same disk
containers, so two machines interleave into one log and the run appears to
stall at a random question.  Kill before every run.

## Reading the log

Do not conclude "wedged" from a log that has stopped growing.  The console
log flushes in chunks, so two samples taken minutes apart can be
byte-identical while the run is progressing normally -- this produced a
wrong diagnosis of a hang at the K-series question, which was in fact
answered and merely slow.  Watch with `tail -F` (follow by name: the
harness deletes and recreates the log, so `tail -f` ends up on a dead
inode) and filter for prompts and failures together:

    tail -F -n 0 sysgen.log | grep -aE --line-buffered \
        "PHASE|SYSTEM CRASH|HALT instruction|SYSGEN -- |\* *[0-9]+\. "

## Autoconfigure hangs; the manual path works

Answering `Y` to question 1 runs autoconfigure, which correctly identifies
the whole machine, and then hangs after question 2 with the CPU spinning --
reproduced with a single clean simulator over a 540-second run.  Answering
`N` proceeds normally into the target configuration section.  That is the
better path regardless: the target hardware is known exactly, so the device
list is specified rather than probed.

## Target configuration answers for the 11/44

    Processor Type                  11/44
    switch register                 (default, N)
    Memory size                     1920      K-word blocks -- SYSGEN's
                                              ceiling, and 3.84 MB of the
                                              machine's 4 MB
    K-series devices                N
    Floating point processor        Y
    EIS                             Y
    CIS                             Y

Note 1920 KW is the maximum SYSGEN accepts (`[D R:64.-1920.]`), and that
this has no bearing on the 32K-word per-task limit, which is the 16-bit
virtual address space and is unaffected by how much memory the machine has.

## The DELUA does not appear in SYSGEN

Autoconfigure lists `YZA`/`YZB` for the two DZ11s and finds the disks, but
no Ethernet device.  That is expected: the DEUNA/DELUA driver (`XE:`) is
part of DECnet-11M, a separate layered product, not the base executive.  It
is configured when DECnet is installed, not during SYSGEN.

## The baseline is CONSUMED, so the run must not stop at Phase II

Phase II ends with the new system present as a task image,
`[1,54]RSX11M.SYS`, and **nothing has written a bootstrap for it**.  The
RSXM32 volume will not boot on its own at that point -- SimH reports

    HALT instruction, PC: 000002 (HALT)

That is not a failed generation.  DEC's procedure boots the new system from
the baseline that is *still running* at the end of Phase II:

    >BOO [1,54]RSX11M
    RSX11M V4.0 BL32     1920.K  MAPPED
    >TIM ...
    >SAV /WB

`SAV /WB` is what makes the volume self-booting, so the boot and the save
have to happen in the SAME simulator session as the generation.  Killing the
simulator after Phase II throws the baseline away and there is no way back
to it except regenerating.

**`SAV` refuses while the checkpoint file is active:**

    SAV -- Checkpoint file still in use on DL0:

STARTUP allocates it (`ACS SY:/BLKS=512.`), so release it first with
`ACS SY:/BLKS=0` and then `SAV /WB`.

**Snapshot the generation as soon as Phase II finishes.**  The harness
restores the pristine kit at the start of every run, so an unguarded rerun
destroys a result that costs ~15 minutes to reproduce.  Copy `m40/` and the
target drives aside (`m40.gen/`), together with the `sysgen.py` that
produced them.

## Once one generation completes

SYSGEN writes `SYSSAVED.CMD`, the saved answer file.  From then on the
whole dialogue can be replayed from it (question 7, "Use an input saved
answer file?"), which removes the console race entirely.  Getting one
complete generation is therefore worth the iteration cost.

## Installing the FPS software onto the target RK07

`fps_install.ini` does it in ONE simulator session, which is not a style
choice -- see the SimH container traps below.  Result, from RSX's own
directory listing:

    Total of 12735./12735. blocks in 182. files

All 182 files of the 1981 distribution, on `DM0:USAGI0`.

The sequence is `INS $PIP`, `INS $INI`, `ALL DM0:`,
`INI DM0:USAGI0/BAD=[NOAUTO]`, `MOU DM0:USAGI0`, `UFD DM0:[200,200]`,
then mount each transfer volume and `PIP DM0:[200,200]/NV=DLn:[200,200]*.*`.

**RSX initialises the RK07; ods1make does not.**  RSX places the index
file at the volume midpoint on large disks -- an RSX-initialised RK07 has
`H.IBLB=26895` (= 53790/2) and `H.FMAX=3308`, where ods1make writes
`H.IBLB=2`.  So the target disk is formatted by `INI` and the files are
carried in on RL02-geometry volumes, which ods1make builds correctly and
which RSX mounts and lists.

**`/BAD=[NOAUTO]`** is required.  An RK07 carries a factory bad-sector
file in its last track and `INI` reads it; a SimH container has none, so
plain `INI` fails with "Manufacturer's bad sector file corrupt".  The
keyword is NOAUTO (not OVR) and the brackets are part of the syntax --
both are in the kit's own `INITIAL.MAC` switch table.

**Split the package by its ON-VOLUME size, not by file size.**  ODS-1
stores text as variable-length records with a 2-byte length per line, so
files GROW: the tape's 182 files are 12,736 blocks on a volume against
about 11,700 bytes-on-disk.  Size the split with `textrecs()`.

### SimH HK container traps, all of which cost a run here

- **`set hkN noautosize` makes `att -n` create a 210-BLOCK STUB** instead
  of a 53,791-block RK07, whatever order it is issued in.  `INI` then
  "succeeds" while writing nothing past block 209 and the volume will not
  mount ("IE.NSF - no such file").  Do not use it; give each unit its type
  and let autosize alone.
- **A correctly sized RK07 container cannot be RE-ATTACHED.**  SimH
  reports the device capacity in blocks but measures the container in
  words, so a 27.5 MB image is rejected as 256x too large:
  "The disk container is larger than simulated device (13MW > 53KW)".
  A container SimH itself created comes back as "incompatible with the HK
  device".  Hence: create with `att -n` and do all the work in that one
  session.
- Because of the two above, any experiment that re-attached an RK07 was
  testing a broken drive, and conclusions drawn from those runs are void.

### SimH expect: it is a LITERAL match

Without `-r`, `.` is NOT a wildcard.  `expect "INS .PIP"` never matches
`INS $PIP`, and `expect "PIP DM0:.200,200./NV=DL2"` never matches its own
echo.  Use a plain distinctive substring (`NV=DL2`).  Also note `after=`
is capped near 2.1e9; `4000000000` is rejected outright with
`%SIM-ERROR: Invalid After Value`, and the rule then never arms.

## Installing FORTRAN IV on the generated system

The V4.0 kit ships no compiler, so a freshly generated system cannot build
FPS software -- the whole toolchain was validated on the V3.1 pack for
that reason.  `fortran_install.cmd` fixes that, and the result compiles:

    >INS $FOR
    >FOR HELLO,HELLO=HELLO
    HELLO

producing `HELLO.OBJ` and `HELLO.LST`.  `FOR.TSK` comes out at 252 blocks
from the kit's own `FOR11M.CMD`.

**Mount the DEC kit volume; do NOT convert its files host-side.**  RSX
object files and libraries are RECORD-structured, not raw block images.
Extracting them with `ods1make.py -x` and rebuilding a volume from the
result destroys the format, and RSX says so exactly:

    TKB -- *FATAL*-Module FROOT  not in library      (records wrapped as text)
    TKB -- *FATAL*-File FOR.OLB;1 has illegal format (written as raw blocks)
    LBR -- *FATAL*-Invalid format, input file FOROTS.OBJ;1

The kit image is an RK05 (4800 blocks) and attaches happily to an RL02
drive -- SimH allows a container SMALLER than the device -- so mount it
and `PIP` from it.  Its files are in `[11,41]` and `[11,42]`.

Note `ods1make.py` now writes `.OLB/.OBJ/.TSK/.STB/.SYS` verbatim as fixed
512-byte records rather than through `textrecs()`, which is right for
carrying a PRE-BUILT binary in.  It still cannot round-trip one out and
back, because the extractor decodes records to lines; both halves would
have to preserve record structure for that.

## Self-hosting the target: DONE except one link symbol

FORTRAN IV is installed and COMPILES on the generated system
(`FOR HELLO,HELLO=HELLO` -> `HELLO.OBJ`, `HELLO.LST`).  Building ASM100
there gets all the way through the compiles, the libraries and the task
build, but the link leaves exactly ONE symbol undefined:

    TKB -- *DIAG*-1 undefined symbols segment .MAIN.
    ...  Undefined references:   $VIRIN

and the task then traps at `PC = 000002` the first time that path runs --
TKB writes an image despite the diagnostic, so the build LOOKS fine.

What is established:

- `$VIRIN` is FORTRAN's virtual-array initialisation entry.  A RAD50
  search of the kit shows it lives in `FOREIS.OBJ` (and in FOREAE, FORFIS,
  FORNHD -- the arithmetic OTS variants), NOT in `FOROTS.OBJ`.
- The V3.1 pack's SYSLIB contains it (8 RAD50 hits); a pristine V4.0
  system contains none.  So it genuinely has to be merged in.
- **`LBR /RP` is the wrong switch.**  It REPLACES modules that already
  exist; the OTS module names are not in SYSLIB, so it matched nothing and
  inserted nothing -- silently, with no diagnostic.  Use `/IN`.  With
  `/RP` the count was 570 undefined symbols; the OTS merge took it to 1.
- `SHORT.OBJ` is NOT the virtual-array stub.  It is the short-error-text
  alternative to a FOROTS module and collides:
  `LBR -- *FATAL*-Duplicate entry point name "$ERTXT"`.
- With `/IN` both merges run clean and silent (LBR says nothing on
  success), yet `$VIRIN` is still unresolved at link time.

Next thing to check: whether the modules really landed, with
`LBR TI:/LE=LB:[1,1]SYSLIB` (the switch goes on the OUTPUT side; `LBR
TI:=...SYSLIB/LE` is rejected as an illegal switch).  If they are present,
the question becomes why TKB's default library search does not reach them
from the root of an overlaid task.

None of this affects any result in this repository: the whole toolchain is
validated on the V3.1 pack, where ASM100 reproduces nine shipped libraries
byte-for-byte.  Self-hosting the 11/44 is convenience, not correctness.

## SimH: an RK07 container cannot be RE-ATTACHED

Worth knowing before planning any persistent RK07 image.  A container SimH
itself created with `att -n` comes back as

    %SIM-ERROR: HK0: RK07 container created by the PDP-11 simulator is
                incompatible with the HK device on the PDP-11 simulator

and its own suggested `ATTACH HK0 -C new old` conversion fails the same
way.  The container also ends up 107,581 blocks for a 53,790-block drive.
So an RK07 built by running SimH is a SINGLE-SESSION artifact: create it
with `att -n` and do all the work in that one run.  Any experiment that
re-attached one was testing a broken drive.
