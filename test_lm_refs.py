#!/usr/bin/env python3
"""Compare lod100.py against every load module the recovered LOD100 wrote.

    ./test_lm_refs.py

Each reference was produced by the recovered LOD100 running on the 11/44
replica and extracted from its volume; the job that produced it is in
`jobs/`.  This is the check behind the claim that the two tools agree, so
it is written to FAIL LOUDLY rather than to pass quietly:

  * a missing or empty output is an error, not "nothing differs";
  * a length mismatch is an error, counted in full;
  * only then are the words compared.

That matters because the obvious form of this test -- comparing
`min(len(a), len(b))` words -- reports ZERO differences when one side is
empty, which is exactly what a crashed or unwritten run looks like.  The
sibling harness `test_apo_exec.py` had a bug of that shape: its expected
values were parsed with a regex that could not match a minus sign, so the
first routine with negative results compared an empty list against an
empty list and reported PASS.

Run `--self-test` to confirm the comparison still detects a difference; it
mutates a reference in memory and expects a failure.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")

# (command file, output file, reference, label)
JOBS = [
    ("at.cmd",  "AT.LM", "VATAN.LM",   "VATAN"),
    # The FIRST job to use CALL, and therefore the first to exercise HASI
    # generation at all.  It found lod100.py's HASI path crashing outright
    # (parse_fpb was never written) -- see CLAUDE.md.
    ("hasi.cmd","HASI.LM","HASICALL.LM","CALL / HASI generation"),
    # CVADD's FPB carries DIMENSION records (ndim=2), which VADD's does
    # not -- so this is the job that exercises parse_fpb's record walk.
    ("hasi2.cmd","HASI2.LM","HASI2CALL.LM","CALL CVADD / FPB dimensions"),
    # FPS's own HASI TEST ROUTINE: a COMMON block and an entry with NO
    # ***FPB, so it covers the AENTRY parameter count, the suppressed
    # APPUT body and the common-block declarations -- none of which any
    # shipped library routine can reach.
    # NOT ENABLED: the HASI half matches exactly (28 lines) but the load
    # module differs in 2 words -- a type-3 data-block relocation resolving
    # to 0 where the hardware has 1.  See CLAUDE.md.
    ("hasi3.cmd","HASI3.LM","HASI3CALL.LM","CALL SUBR1 / common block"),
    # Floating $DATA in a data block: the load-module encoding is
    # (IEEE_hi + 0x100, IEEE_lo, 0), measured over six values.
    ("hasi5.cmd","HASI5.LM","HASI5CALL.LM","CALL / floating $DATA"),
    ("hasi6.cmd","HASI6.LM","HASI6CALL.LM","CALL / float mantissa hi"),
    ("hasi7.cmd","HASI7.LM","HASI7CALL.LM","CALL / float mantissa lo"),
    ("v2.cmd",  "V2.LM", "VADD4.LM",   "VADD, four libraries"),
    ("n9.cmd",  "N9.LM", "NINE.LM",    "nine separate LIBs"),
    ("apl.cmd", "A.LM",  "APLIB.LM",   "APLIB concatenated"),
    ("ovh.cmd", "OV.LM", "OVERLAID.LM", "overlaid, 2 segments"),
    ("tk2.cmd", "K2.LM", "TASK1.LM",   "task job, single LINK"),
    ("tl.cmd",  "TL.LM", "TASK2.LM",   "task job, two LINKs"),
    ("t2.cmd",  "P2.LM", "TWOTASK.LM", "two tasks, three LINKs"),
    # DECLARED LOW PRIORITY FIRST, WITH /I ON THE SECOND.  Every other job
    # here declares its tasks in descending priority, so the ready queue came
    # out right whether or not anything sorted it, and both the ring order and
    # the switch parsing were unverified.  This one separates them: it caught
    # lod100.py emitting the TCB records in priority order (FINISH emits in
    # TABLE order and only the LINKS follow TSKLNK's sort) and the hybrid
    # reading TASK switches positionally, which made "/I" set the /M bit and
    # gave an /I task a 63-word TCB instead of 148.
    ("pq.cmd",  "PQ.LM", "PRIORDER.LM", "priority order, /I"),
    # THE ISR PATH.  RTCISR.S is the tape's own real-time-clock handler,
    # "$ISR 5.", assembled by the installed ASM100; RTCISR.APO is that
    # object.  It is the only job here that exercises object block 16, the
    # synthesised TREE/OV, ENDLNK's suppression under ISRFL, and a type-3
    # (data block) relocation -- RTCCOM's address, which is what the one
    # differing word was before type 3 was implemented.
    ("isr.cmd", "IS.LM", "ISR.LM",   "ISR, block 16 + type-3 reloc"),
    # LIB THEN LOAD, and the same file named twice.  This job could not run
    # at all until LIBFLG was cleared for a plain LOAD (it gave ERROR 25,
    # NOT A LIBRARY), and once it did it found two more gaps: no
    # duplicate-module guard, and code emitted BEFORE the data blocks in
    # the flat path.  It is the only reference with both data blocks and
    # code on the flat path.
    ("l1.cmd",  "L1.LM", "LIBLOAD.LM", "LIB then LOAD, duplicate file"),
    # MDOFF AND PPA, the first job to exercise either.  PPA was a no-op in
    # the mainline until PPAY was written; MDOFF is FPS's own and had never
    # been run.  "MDOFF 100 / PPA 500" is octal, so the info record must
    # read ppa_addr=64 and ppa_size=320.
    ("py.cmd",  "PY.LM", "PPAMD.LM",   "MDOFF + PPA"),
    # LMID with a NON-DEFAULT id.  Every other job says "LMID 1", which is
    # the default -- so a no-op handler produced the right answer and the
    # gap survived.  "LMID 7" is what a no-op cannot fake.
    ("pz.cmd",  "PZ.LM", "LMIDPPA.LM", "LMID 7 + MDOFF + PPA"),
    # A CODE MODULE AHEAD OF THE ISR.  isr.cmd cannot exercise the ordering
    # rule because TABLES.APO is data blocks only; these two put APFET (two
    # ***CODE blocks) and RGEN (one) before the ISR object.  LOAD1 builds the
    # ISR's tree when it READS block 16, so anything loaded earlier stays
    # flat and its blocks are PREPENDED, MD-destined, at doubled addresses.
    ("ix.cmd",  "IX.LM", "ISRCODE.LM",  "code before ISR, 2 blocks"),
    ("iy.cmd",  "IY.LM", "ISRCODE2.LM", "code before ISR, 1 block"),
]

# JOBS THE RECOVERED LOD100 REFUSES.  These cannot be word-for-word
# comparisons -- their correct outcome is a FATAL error and NO output file --
# so they get their own assertion.  Both were run on the 11/44 and both stop
# with the documented error and write nothing:
#
#   hasi4.cmd  ERROR 31  IMPROPER USE OF TRIPLE -- a $TRIPLE item in the
#              $COMMON of a CALLed routine.  Isolated with a variant keeping
#              the declaration but dropping its $DATA, which is STILL refused.
#   e18.cmd    ERROR 18  ENTRY POINT DECLARED CALLABLE IS NOT RELOCATABLE --
#              CALL on SYMLIB's absolute !ONE.
#
# A tool that ACCEPTS what the loader refuses is the wrong direction for a
# compliance claim, and lod100.py did for both until this session.
REJECT = [
    ("hasi4.cmd", "HASI4.LM", 31, "CALL with a $TRIPLE item"),
    ("e18.cmd",   "E18.LM",   18, "CALL on an absolute symbol"),
    # ERROR 15: two DIFFERENTLY-TITLED modules declaring /COMM/ at different
    # sizes.  The obvious pair (SEQV1 + FLTEST) cannot test this -- they share
    # a title, so LOAD1's duplicate guard skips the second before the commons
    # are compared -- so CMTST.APO exists purely to be a second declarer.
    ("e15.cmd",   "E15.LM",   15, "unmatched common block"),
    # ERROR 14: NOEND.APO is CMTST.APO truncated before its ***END -- no
    # assembly needed, and the recovered loader stops on it.
    ("e14.cmd",   "E14.LM",   14, "object module with no ***END"),
    # ERROR 13: DBLTTL.APO carries its ***TITLE block twice.  Checked BEFORE
    # the missing-END test, because a doubled title also leaves the first
    # module unterminated -- the machine reports 13, not 14.
    ("e13.cmd",   "E13.LM",   13, "doubled ***TITLE block"),
    # ERROR 36: an ISR object loaded WITHOUT TABLES.APO, which is what
    # declares ISRMAP.  The three ISR references all load it, so they are
    # the guard against this check false-firing -- it did, twice.
    ("e36.cmd",   "E36.LM",   36, "ISR with no ISRMAP"),
    # ERROR 37: BADMAP.APO is TABLES.APO with ISRMAP declared 64 words
    # instead of 120 (ISRLEN).  Rides on the same check as 36.
    ("e37.cmd",   "E37.LM",   37, "ISRMAP the wrong size"),
    # ERROR 35: a task job with TABLES.APO removed, so nothing declares
    # READYQ.  FINISH is a RECOVERED module, so this is real ground truth
    # -- unlike error 38, whose site TASKY is a reconstruction.
    ("e35.cmd",   "E35.LM",   35, "task job with no READYQ"),
]


def hasi_norm(path):
    """Normalise generated FORTRAN, removing ONLY the formatting variation
    the manual permits: continuation lines joined onto their statement,
    blank lines dropped, runs of spaces collapsed."""
    lines = []
    for raw in open(path, errors="replace"):
        t = raw.rstrip("\n").rstrip()
        if not t.strip():
            continue
        cont = len(t) > 5 and t[5] not in " \t"
        # FIXED-FORM FORTRAN IGNORES BLANKS outside character constants, so
        # "P 7" and "P7", or "L 101" and "L101", are the SAME identifier --
        # and the two generators differ in exactly that way, because the
        # recovered LOD100 wraps its parameter list MID-TOKEN and pads its
        # RPLIS fields differently.  Removing blanks entirely is therefore
        # the semantically correct comparison, not a loosening of it: a
        # wrong count, type, order or address still differs.
        body = "".join(t.split())
        if cont and lines:
            lines[-1] += body.lstrip("*")
        else:
            lines.append(body)
    return lines


def words_of(path):
    """The CODE array of a host-resident load module, in order."""
    with open(path) as f:
        text = f.read()
    out = []
    for line in text.split("\n"):
        if line.startswith("     *"):
            out += [int(x) for x in line[6:].strip().rstrip("/").split(",")]
        else:
            m = re.match(r"^\s*(-?\d+)\s*$", line)
            if m:
                out.append(int(m.group(1)))
    return out


def compare(got, want, label):
    if not want:
        return "%-24s REFERENCE EMPTY OR UNREADABLE" % label, 1
    if not got:
        return "%-24s NO OUTPUT -- the run produced nothing" % label, 1
    if len(got) != len(want):
        return ("%-24s LENGTH %d against %d" % (label, len(got), len(want)),
                abs(len(got) - len(want)))
    bad = sum(1 for a, b in zip(got, want) if a != b)
    if bad:
        return "%-24s %4d words, differing %d" % (label, len(got), bad), bad
    return "%-24s %4d words, identical" % (label, len(got)), 0


def ensure_inputs():
    """The jobs name their inputs relatively, so make them present.

    APLIB.APO is what APEEL builds -- the nine shipped libraries
    concatenated -- and TABLES.APO is the supervisor's system commons as
    ASM100 assembles them from TABLES.S; a copy is kept beside the
    references because reproducing it needs the PDP-11.
    """
    src = os.path.join(HERE, "..", "software", "fps100sw")
    apl = os.path.join(REFS, "APLIB.APO")
    if not os.path.exists(apl):
        # FPS'S OWN ORDER, from APL100.CMD -- not alphabetical.  APEEL is
        # called once per library in this sequence, and selective loading
        # takes the FIRST module that satisfies a reference, so the order
        # is part of the library's meaning:
        #     APE 'NO',AMLLIB / IPRLIB / TMRLIB / SIGLIB
        #     APE 'NO',BAALIB / BABLIB / UTLLIB / APFLIB
        #     APE 'NO',SYMLIB / APE 2,DGNLIB
        # TMRLIB is the AP-120-TMR option and is not on the tape.
        libs = ["AMLLIB", "IPRLIB", "SIGLIB", "BAALIB", "BABLIB",
                "UTLLIB", "APFLIB", "SYMLIB", "DGNLIB"]
        with open(apl, "wb") as out:
            for lib in libs:
                with open(os.path.join(src, "[327,010]%s.APO" % lib), "rb") as f:
                    out.write(f.read().replace(b"\0", b""))


def main():
    self_test = "--self-test" in sys.argv
    ensure_inputs()
    total = 0
    for cmd, out, ref, label in JOBS:
        refpath = os.path.join(REFS, ref)
        if not os.path.exists(refpath):
            print("%-24s reference missing: %s" % (label, refpath))
            total += 1
            continue
        subprocess.run([sys.executable, os.path.join(HERE, "lod100.py"),
                        "-c", cmd],
                       capture_output=True, cwd=REFS)
        outp = os.path.join(REFS, out)
        got = words_of(outp) if os.path.exists(outp) else []
        want = words_of(refpath)
        if self_test and want:
            want = list(want)
            want[len(want) // 2] ^= 1        # one bit, mid-module
        line, bad = compare(got, want, label)
        print("  " + line)
        total += bad
        # Compare the HASI too when a reference exists.  [M] says outright
        # that "the HASI routine generated may vary from system to system",
        # so textual identity is NOT the target: the recovered LOD100 wraps
        # its parameter list at a different column and writes "CALL L 101"
        # where lod100.py writes "CALL L101", both from RPLIS field widths.
        # Normalising joins continuation lines (a '*' in column 6), drops
        # blanks, and collapses runs of spaces -- which removes exactly the
        # variation the manual permits and nothing else, so a wrong
        # parameter count, type, order or address still differs.
        hp = os.path.join(REFS, ref.replace(".LM", ".HSR"))
        if os.path.exists(hp):
            gp = os.path.join(REFS, out.replace(".LM", ".HSR"))
            gh = hasi_norm(gp) if os.path.exists(gp) else []
            wh = hasi_norm(hp)
            if self_test and wh:
                wh = list(wh); wh[len(wh) // 2] += "X"
            if gh and gh == wh:
                print("  %-24s HASI %d lines, identical" % (label, len(gh)))
            else:
                n = sum(1 for i in range(min(len(gh), len(wh)))
                        if gh[i] != wh[i]) + abs(len(gh) - len(wh))
                print("  %-24s HASI %d vs %d lines, %d differing"
                      % (label, len(gh), len(wh), n))
                total += max(n, 1)
        for f in (out, out.replace(".LM", ".HSR")):
            p = os.path.join(REFS, f)
            if os.path.exists(p):
                os.remove(p)
    if self_test:
        print("self-test: %s" % ("DETECTED the mutation" if total else
                                 "FAILED TO DETECT A MUTATION"))
        return 0 if total else 1
    # THE REJECTION CASES.  A fatal must (a) fail and (b) leave NO output --
    # lod100.py originally raised ERROR 31 during HASI generation, which runs
    # AFTER the load module is written, so a partial .LM survived a fatal.
    # Both halves are asserted here.
    for cmd, out, errno, label in REJECT:
        outp = os.path.join(REFS, out)
        if os.path.exists(outp):
            os.remove(outp)
        r = subprocess.run([sys.executable, os.path.join(HERE, "lod100.py"),
                            "-c", cmd], capture_output=True, cwd=REFS, text=True)
        msg = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0:
            print("%-24s ACCEPTED a job the loader refuses" % label)
            total += 1
        elif ("ERROR %d" % errno) not in msg:
            print("%-24s failed, but not with ERROR %d" % (label, errno))
            total += 1
        elif os.path.exists(outp):
            print("%-24s ERROR %d raised but %s was still written"
                  % (label, errno, out))
            total += 1
            os.remove(outp)

    print("%d hardware references + %d rejections, total differing: %d"
          % (len(JOBS), len(REJECT), total))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
