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
DEFAULT = ["VADD", "VSUB", "VMUL", "VSMUL", "VMOV", "VCLR",
           "VNEG", "VSQ"]


def ieee_from_octal(hi, lo):
    """Two 16-bit octal host words, high then low, as an IEEE 32-bit float."""
    return struct.unpack('>f', struct.pack('>I', (hi << 16) | lo))[0]


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
    return (got == want), "expected %s, got %s" % (want, got)


def main():
    routines = sys.argv[1:] or DEFAULT
    bad = 0
    for r in routines:
        ok, detail = run(r)
        if ok:
            print("PASS  %-6s %s" % (r, detail.split(", got")[0]
                                     .replace("expected ", "")))
        else:
            bad += 1
            print("FAIL  %-6s %s" % (r, detail))
    print("%d of %d routines execute correctly from the shipped libraries"
          % (len(routines) - bad, len(routines)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
