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
]


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
        libs = ["AMLLIB", "APFLIB", "BAALIB", "BABLIB", "DGNLIB",
                "IPRLIB", "SIGLIB", "UTLLIB", "SYMLIB"]
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
        for f in (out, out.replace(".LM", ".HSR")):
            p = os.path.join(REFS, f)
            if os.path.exists(p):
                os.remove(p)
    if self_test:
        print("self-test: %s" % ("DETECTED the mutation" if total else
                                 "FAILED TO DETECT A MUTATION"))
        return 0 if total else 1
    print("%d hardware references, total differing: %d" % (len(JOBS), total))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
