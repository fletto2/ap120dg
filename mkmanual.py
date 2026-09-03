#!/usr/bin/env python3
"""Build a routine reference from an FPS .APS library source.

    ./mkmanual.py ../software/fps100sw/'[327,010]AMLSRC.APS' > AMLLIB.md

FPS shipped a manual for the BASIC math library (860-7288-004) and for the
signal-processing routines, but not for the ADVANCED math library -- it is
absent from bitsavers, from archive.org and from every manual in this
archive.  What IS present is the complete commented assembly source, so
the reference can be reconstructed from it rather than lamented.

Everything emitted here is quoted or derived from the source: the $TITLE,
the $ENTRY and its parameter count, the $EQU block that names the s-pad
parameters, and the header comment lines that carry the abstract, the
FORMULA and the size.  Nothing is inferred about behaviour -- where a
routine does not state its formula, this says so rather than guessing,
because an invented calling sequence in a reference document is worse
than an absent one.
"""

import os
import re
import sys

# A routine's header comments are the lines beginning with a quote before
# its code starts.  ASM100 uses " as the comment character.
COMMENT = re.compile(r'^\s*"(.*)$')
TITLE = re.compile(r'^\s*\$TITLE\s+(\S+)')
ENTRY = re.compile(r'^\s*\$ENTRY\s+([A-Z0-9]+)\s*,?\s*([0-9]*)\.?')
EQU = re.compile(r'^\s*([A-Z][A-Z0-9]*)\s+\$EQU\s+([0-9]+)(\.?)\s*(?:"(.*))?')
RADIX = re.compile(r'^\s*\$RADIX\s+([0-9]+)')
# Lines worth surfacing verbatim from the header block.
KEYED = re.compile(r'(FORMULA|ABSTRACT|SIZE|ACCURACY|DOES|CALL |EQUIPMENT'
                   r'|SCRATCH|S-PAD PARAMETERS'
                   # A routine may describe its MODES in prose instead of a
                   # formula -- CVMUL has no FORMULA line at all, only
                   # "F = 1:  COMPLEX MULTIPLY" / "F = - 1:  ... CONJUGATE"
                   # and the lines under them.  Those are the only statement
                   # of what its flag does, so a reference that drops them
                   # omits the routine's actual behaviour.
                   r'|^\s*[A-Z] *= *-? *[0-9])', re.I)


def routines(path):
    """Split the source into (title, [lines]) blocks on $TITLE."""
    cur, name = [], None
    with open(path, errors="replace") as f:
        for raw in f:
            line = raw.replace("\r", "").rstrip("\n")
            m = TITLE.match(line)
            if m:
                if name:
                    yield name, cur
                name, cur = m.group(1), []
            elif name:
                cur.append(line)
    if name:
        yield name, cur


def describe(name, lines):
    """Everything the source states about one routine."""
    entry, nparam, spads, notes = None, None, [], []
    radix, carry = 10, 0
    for line in lines[:400]:
        r = RADIX.match(line)
        if r:
            radix = int(r.group(1))
            continue            # the header block, not the code
        m = ENTRY.match(line)
        if m and entry is None:
            entry, nparam = m.group(1), m.group(2) or None
            continue
        m = EQU.match(line)
        if m:
            # XADC is a conditional-assembly switch, not a parameter, and
            # it appears in every routine -- it would be noise here.
            if m.group(1) != "XADC":
                # $EQU IS READ IN THE PREVAILING RADIX, and these sources
                # are `$RADIX 8` -- so `$EQU 10` is s-pad EIGHT, not ten.
                # 0-7 read the same either way, which is why this went
                # unnoticed until CVMA, whose N and F are $EQU 10 and 11.
                # This project already records the same trap for VDIV
                # ("TBLADR is s-pad 10 octal = 8").
                # Some sources carry an $EQU value that is not legal in
                # the prevailing radix (an `$EQU 8` under `$RADIX 8`), so
                # fall back to decimal and SAY SO rather than crash or
                # silently mis-state the number.
                # A TRAILING DOT IS ASM100's EXPLICIT DECIMAL MARKER,
                # whatever the prevailing radix -- VMMA writes
                # "E $EQU 8." / "M $EQU 9." / "N $EQU 10." under $RADIX 8,
                # and the same convention appears as "$ENTRY MMUL, 9." and
                # "IT(17.)" throughout.  Without this the dotted values
                # were only right by accident, via the invalid-octal
                # fallback below.
                if m.group(3) == ".":
                    v, note = int(m.group(2)), ""
                else:
                    try:
                        v, note = int(m.group(2), radix), ""
                    except ValueError:
                        v, note = int(m.group(2)), " (not valid in radix %d; "
                        note = note % radix + "read as decimal)"
                spads.append((v, m.group(1),
                              (m.group(4) or "").strip() + note))
            continue
        m = COMMENT.match(line)
        if m:
            t = m.group(1).strip()
            if KEYED.search(t):
                if t and t not in notes:
                    notes.append(t)
                # A FORMULA is often CONTINUED on the next comment line --
                # CVMA's ends in a bare "+" -- and the continuation carries
                # no keyword, so a keyword-only filter truncates it and the
                # reader silently gets half an equation.  Take the following
                # lines while the formula is plainly unfinished.
                # Continue while the equation is plainly unfinished (it
                # ends in an operator, as CVMA's does) OR while it is a
                # MULTI-CASE formula -- VCLIP's is three lines of
                # "D(ML) = x IF <condition>", each a separate arm, and
                # none ends in an operator.
                carry = 3 if (t.rstrip().endswith(("+", "-", "*", "/", "=",
                                                   "(", ","))
                              or " IF " in t.upper()) else 0
            elif carry and t and ("=" in t or " IF " in t.upper()):
                # Only take lines that look like part of the equation, so a
                # prose paragraph following a formula is not swept in.
                notes.append(t)
                carry -= 1
            else:
                carry = 0
    return entry, nparam, spads, notes


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    lib = os.path.basename(path).split("]")[-1].replace(".APS", "")

    out = []
    out.append("# %s -- routine reference\n" % lib)
    out.append("**Reconstructed from `%s`.**  FPS published no manual for\n"
               "this library that survives in any archive searched (bitsavers,\n"
               "archive.org, and the ten manuals transcribed in `docs/ocr/`).\n"
               "Every line below is quoted or derived from the shipped source;\n"
               "where a routine does not state something, this says so rather\n"
               "than guessing.\n" % os.path.basename(path))

    seen, bodies = [], []
    for name, lines in routines(path):
        entry, nparam, spads, notes = describe(name, lines)
        seen.append((name, entry, nparam, len(spads)))
        b = ["\n## %s\n" % name]
        if entry:
            b.append("`$ENTRY %s%s`\n" %
                     (entry, ", %s" % nparam if nparam else ""))
        else:
            b.append("_No `$ENTRY` in the header block -- probably an "
                     "internal helper rather than a user entry._\n")
        if spads:
            b.append("\n| s-pad | name | meaning |\n|---|---|---|")
            for n, nm, cm in sorted(spads):
                b.append("| %d | `%s` | %s |" % (n, nm, cm))
            b.append("")
        else:
            b.append("\n_No `$EQU` parameter block found._\n")
        if notes:
            b.append("")
            for t in notes:
                b.append("    %s" % t)
            b.append("")
        else:
            b.append("\n_The header states no formula, size or abstract._\n")
        bodies.append("\n".join(b))

    out.append("\n## Contents\n")
    out.append("| routine | entry | parameters | s-pads documented |")
    out.append("|---|---|---|---|")
    for name, entry, nparam, ns in seen:
        out.append("| [%s](#%s) | %s | %s | %d |"
                   % (name, name.lower(), entry or "-", nparam or "-", ns))
    out.append("\n%d routines.\n" % len(seen))
    out.extend(bodies)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
