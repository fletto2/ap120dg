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

**`autosize` silently overrides the drive type.**  `set hk2 rk06` still
autoconfigured as an RK07, because SimH sized the drive from the existing
container file.  `set hkN noautosize` must come *before* the type:

    set hk enabled
    set hk0 noautosize ; set hk1 noautosize ; set hk2 noautosize
    set hk0 rk07       ; set hk1 rk07       ; set hk2 rk06
    att -n hk0 usagi0.dsk ...

With that, RSX's own autoconfigure reports the target exactly:
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
