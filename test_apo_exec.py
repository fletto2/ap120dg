#!/usr/bin/env python3
"""Link each basic-math routine from the SHIPPED LIBRARIES and execute it.

    ./test_apo_exec.py [routine ...]

`gen_apo_test.py` proves the chain

    .APS --ASM100--> .APO --link--> PS --execute--> correct numbers

for ONE routine out of ONE bundle.  VADD.APO is the only bundle FPS
shipped, so every other routine has to come out of the real libraries the
way LOD100 does it -- FORCE the name, LIB each library, let selective
loading drag in the closure.  That is a far wider exercise of the linker:
the parameter blocks, the library selection, the relocation rules and the
symbol scoping all differ between routines.

This exists because "one routine proves one routine" has been true here
repeatedly.  Testing VADD alone hid three multiplier defects until VSUB
and VMUL were tried on the HSR path; the same widening on the .APO path
is what this runs.

Each routine's expected result and s-pad convention live in
gen_apo_test.py's ROUTINES table, taken from its $EQU block in BAASRC.APS.
"""

import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NOVA = os.path.join(HERE, "..", "simh", "BIN", "nova")
SCRIPT = "/tmp/test_hsr.simh"
# VDIV IS IN THE DEFAULT SET NOW THAT IT WORKS.  It is the only routine
# here that exercises the DIVIDER, table memory, the exponent construction
# (LDSPE/COM/MDPX) and the sign machinery -- the other nine are add and
# multiply on positive data and passed throughout the session in which
# every operand in main data was twice its nominal value.  VDIV1 and VDIV2
# are single-element cases that separate a scale error from a bias one.
DEFAULT = ["VADD", "VSUB", "VMUL", "VSMUL", "VMOV", "VCLR",
           "VNEG", "VSQ", "VSADD", "VDIV", "VDIV1", "VDIV2", "VABS", "VMA", "VLOG",
           "VSQRT", "VSQRT2",
           "VSIN", "VSIN2", "VSIN3", "VSIN4", "VSIN5", "VEXP", "VOR", "VAND", "VINT", "VCOS", "VALOG",
           "VATAN", "VATAN2", "MAXV", "DOTPR", "CVADD", "CVMUL", "CVMUL2", "VMAX", "MMUL", "CFFT", "CFFT4", "CFFTI", "MINV", "HANN", "HANN2", "VDBPWR", "VAVLIN", "ASPEC", "ASPEC1", "CSPEC", "TRANS", "CVCONJ", "CVNEG", "CVMOV", "CVFILL", "CVCOMB", "CVMAGS", "CRVMUL", "CRVDIV", "CRVADD", "CRVSUB", "CVMA", "VMIN", "VCLIP", "VLIM", "LVGT", "LVGE", "LVEQ", "LVNE", "LVNOT", "VLMERG", "VRAMP", "VFILL", "VLN", "VATN2", "VFRAC", "VSWAP", "VTSMUL", "VTSADD", "VSMA", "VAM", "VMSB", "VSBM", "VMMA", "VMMSB", "VAAM", "VSBSBM", "VSMSA", "MTRANS", "MVML3", "MATINV", "SOLVEQ", "EIGRS", "IMTQL2", "TRED2", "EIGRS3", "MATINV2", "SOLVEQ2", "VMAXMG", "CVRCIP", "ACORT", "CCORT", "ACORT4"]


def ieee_from_octal(hi, lo):
    """Two 16-bit octal host words, high then low, as an IEEE 32-bit float."""
    return struct.unpack('>f', struct.pack('>I', (hi << 16) | lo))[0]


SELF_TEST = "--self-test" in sys.argv


def run(routine):
    gen = subprocess.run([sys.executable, os.path.join(HERE, "gen_apo_test.py"),
                          routine], capture_output=True, text=True)
    if gen.returncode != 0:
        return None, "link failed: " + gen.stderr.strip().split("\n")[-1]
    try:
        sim = subprocess.run([NOVA, SCRIPT], capture_output=True, text=True,
                             timeout=180)
    except subprocess.TimeoutExpired:
        return None, "emulator timed out"
    finally:
        subprocess.run(["pkill", "-x", "nova"], capture_output=True)

    # The minus sign matters: without it VNEG's expected values do not match
    # at all, `want` comes back EMPTY, and an empty list equals an empty list
    # -- a vacuous PASS.  A test that cannot fail is worse than no test.
    want = [float(x) for x in re.findall(r'IEEE (-?[0-9.]+)', sim.stdout)]
    if not want:
            return None, "no expected values parsed from the harness output"
    # SimH COMPRESSES a run of identical words: an all-zero result prints
    # "620:\t000000" then "621: thru 625: same as above."  Reading only the
    # explicit lines reports one word where there are six, which looked like
    # a failed readback for VCLR -- whose answer is of course all zeros.
    words = []
    for line in sim.stdout.split("\n"):
        m = re.match(r'^\d+:\s+([0-7]+)', line)
        if m:
            words.append(int(m.group(1), 8))
            continue
        m = re.match(r'^(\d+): thru (\d+): same as above', line)
        if m and words:
            words.extend([words[-1]] * (int(m.group(2)) - int(m.group(1)) + 1))
    if len(words) < 2 * len(want):
        return None, "no readback (%d words for %d values)" % (len(words),
                                                              len(want))
    got = [ieee_from_octal(words[2 * i], words[2 * i + 1])
           for i in range(len(want))]
    # --self-test perturbs the EXPECTED value and requires the comparison to
    # notice.  Each harness here has to demonstrate it can fail: two of the
    # three had failure modes that produced green output.
    if SELF_TEST:
        want = list(want)
        want[0] += 1.0
    # THE DIVIDER IS ITERATIVE, so exact equality is the wrong test for it.
    # VDIV computes a reciprocal by Newton-Raphson -- its own header names
    # the series -- and converges to about 1e-7 of the true quotient.  The
    # add/multiply routines are exact and stay on an exact comparison; only
    # the divider gets a tolerance, and it is tight enough that the 2x, 4x
    # and 256x errors this file records would all still fail it.
    # The DIVIDER and the SERIES routines are iterative: VDIV converges by
    # Newton-Raphson and VLOG/VSQRT evaluate a polynomial, so exact equality
    # is the wrong test for them.  The add/multiply routines stay exact.
    # VDBPWR states its OWN accuracy in its header -- "ACCURACY: ERROR LESS
    # THAN +- 0.1 DB" -- and dB is an ABSOLUTE scale, so a relative bound is
    # the wrong test (its first element is 0 dB, where relative tolerance is
    # meaningless -- the same trap VCOS hit with cos(PI/2)).  Checked against
    # the routine's own spec, tightened 10x: the observed errors are 0.0019,
    # 0.0005 and 0.0014 dB.
    if routine == "VDBPWR":
        ok = len(got) == len(want) and all(
            abs(g - w) <= 0.01 for g, w in zip(got, want))
        return ok, "expected %s, got %s" % (want, got)
    if routine.startswith("VDIV") or routine in ("VLOG", "VSQRT", "VSQRT2", "VEXP",
                            "VSIN", "VSIN2", "VSIN3", "VSIN4", "VSIN5", "VCOS", "VALOG", "VATAN", "VATAN2", "HANN2", "TRANS", "CRVDIV", "VLN", "VATN2", "VFRAC", "EIGRS3"):
        ok = len(got) == len(want) and all(
            abs(g - w) <= 1e-6 * max(1.0, abs(w)) for g, w in zip(got, want))
        return ok, "expected %s, got %s" % (want, got)
    return (got == want), "expected %s, got %s" % (want, got)


def main():
    routines = [a for a in sys.argv[1:] if not a.startswith("-")] or DEFAULT
    bad = 0
    for r in routines:
        ok, detail = run(r)
        if ok:
            print("PASS  %-6s %s" % (r, detail.split(", got")[0]
                                     .replace("expected ", "")))
        else:
            bad += 1
            print("FAIL  %-6s %s" % (r, detail))
    if SELF_TEST:
        ok = bad == len(routines)
        print("self-test: %s" % ("DETECTED every mutation" if ok else
                                 "FAILED TO DETECT %d" % (len(routines) - bad)))
        return 0 if ok else 1
    print("%d of %d routines execute correctly from the shipped libraries"
          % (len(routines) - bad, len(routines)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
