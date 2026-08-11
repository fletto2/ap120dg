#!/usr/bin/env python3
"""Link VADD from the shipped .APO and diff it against FPS's own linked output.

This is the strongest check in the project, because both sides come from FPS:
the input is the relocatable `VADD.APO` bundle as shipped, and the expected
result is the already-linked microcode block embedded in `BAAHSR.MAC`.  Nothing
here is compared against another of our own implementations, so the two cannot
be "wrong the same way" -- the failure mode this project has hit repeatedly.

It exercises, in one shot, every part of the relocation path:

  * absolute symbols (`!ONE` from SYMLIB) must NOT be biased by a base address
  * relocatable symbols (`SPUFLT`) must be made PC-relative -- LINKUP's
    `IF (RELTYP .NE. 0 .AND. TYPEN .NE. 2) VAL=ISUB16 (VAL,LOCCUR)`
  * the fixup is ADDITIVE -- LINKUP's `CODE(4)=IADD16 (CODE(4),VAL)`

`VADD.APO` is not a usable library (it opens `***LSB` and never emits
`***LEB`, and no command file references it) but it is a self-contained
bundle: VADD 14 words including the 2-word FVADD auto-call entry, SPUFLT 8,
RESLVE 27.  The BAAHSR block holds VADD proper followed by SPUFLT, 20 words,
so the comparison skips the FVADD entry that precedes it.

Run after ANY change to lnk100.py's parser or relocation handling, alongside
gen_apo_test.py, which executes the result on the emulator.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lnk100 import parse_apo, Linker

SW = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  '..', 'software', 'fps100sw')


def _read(name):
    with open(os.path.join(SW, name), 'rb') as f:
        return f.read().replace(b'\0', b'').decode('latin1')


def linked_vadd():
    """VADD then SPUFLT, linked from the shipped relocatable object.

    SYMLIB is linked FIRST here only because that is how the bundle resolves
    !ONE; the absolute-symbol bias defect that once hid in this ordering is
    covered separately by the DGNLIB-first regression.
    """
    linker = Linker(origin=0)
    mods = []
    for f in ('[327,010]SYMLIB.APO', '[327,010]VADD.APO'):
        mods += parse_apo(os.path.join(SW, f), stop_at_leb=False)
    linker.add_modules(mods)
    linker.link()
    parts = sorted((m.base_addr, m.name.strip(), m.code) for m in linker.modules
                   if m.name.strip() in ('VADD', 'SPUFLT'))
    return [w for _, _, code in parts for w in code]


def shipped_vadd():
    """The already-linked VADD block embedded in BAAHSR.MAC.

    Format is four octal 16-bit words per 64-bit instruction, preceded by
    "CODE: n." giving the instruction count.
    """
    txt = _read('[327,010]BAAHSR.MAC')
    m = re.search(r'\bVADD\b.*?CODE:\s*(\d+)\.', txt, re.S)
    if not m:
        raise SystemExit("could not find VADD's CODE: block in BAAHSR.MAC")
    count = int(m.group(1))
    quads = re.findall(r'([0-7]{6}),([0-7]{6}),([0-7]{6}),([0-7]{6})',
                       txt[m.end():])[:count]
    if len(quads) != count:
        raise SystemExit("BAAHSR VADD block short: %d of %d instructions"
                         % (len(quads), count))
    return [(int(a, 8) << 48) | (int(b, 8) << 32) | (int(c, 8) << 16) | int(d, 8)
            for a, b, c, d in quads]


def main():
    hsr = shipped_vadd()
    # The linked bundle opens with the 2-word FVADD auto-call entry, which the
    # HSR block does not carry; VADD proper starts after it.
    ours = linked_vadd()[2:2 + len(hsr)]
    if len(ours) != len(hsr):
        print("FAIL: linked %d instructions, shipped block has %d"
              % (len(ours), len(hsr)))
        return 1
    bad = [i for i, (a, b) in enumerate(zip(ours, hsr)) if a != b]
    if bad:
        print("FAIL: %d of %d instructions differ" % (len(bad), len(hsr)))
        for i in bad[:8]:
            print("  [%2d] linked=%016x  shipped=%016x" % (i, ours[i], hsr[i]))
        return 1
    print("PASS: linked VADD+SPUFLT is identical to the shipped BAAHSR "
          "block, %d of %d instructions" % (len(hsr), len(hsr)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
