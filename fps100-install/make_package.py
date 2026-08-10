#!/usr/bin/env python3
"""Build the FPS-100 install package: the tape, plus what was lost, minus
the deletions.

The 1981 distribution installs itself by destroying its own sources as it
goes.  Nine files are missing from the surviving tape image and six of
them are named by a "PIP ... /DE" in one of the install command files.
This package is the distribution as it would look if it had never done
that:

  * every file that is on the tape, byte-for-byte apart from the two
    repairs noted below;
  * the files that were lost, either recovered verbatim from INSTAL.TXT
    or reimplemented and marked as such;
  * every source-destroying deletion commented out rather than removed,
    so the original text is still readable and the change is reversible.

Run:  python3 make_package.py [-o OUTDIR]
"""
import argparse
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TAPE = os.path.join(HERE, "..", "..", "software", "fps100sw")
RECON = os.path.join(HERE, "..", "reconstructed")

# Distribution file types.  A deletion naming one of these destroys
# something the package is meant to keep.  Everything else (.OBJ, .MAP,
# .TSK, .STB, .OLB, .LIB, .LST) is a build intermediate and its deletion
# is left alone -- those are hygiene, not loss.
SRC_EXT = ("FTN", "MAC", "APS", "APO", "HSR", "CMD", "DAT", "INP", "TXT",
           "ODL", "NAM", "S", "B")

MARK = ";RM;"

def is_dist_token(tok):
    """A deletion target that names a distribution file.

    Two idioms appear on the tape.  A named source extension --
    "ASM100.FTN;1" -- and a wildcard against version ONE --
    "IAPEX.*;1", "FDUTIL.*;1".  Version 1 is what came off the tape, so
    ";1" means the distribution copy; ";*" is used for libraries and
    build intermediates and is left alone.  Missing this second idiom
    first time round left the very deletion that removed FDUTIL in
    place."""
    t = tok.upper()
    if re.search(r"\.\*\s*;\s*1\b", t):
        return True
    return any(re.search(r"\.%s\s*;" % e, t) for e in SRC_EXT)


def is_source_deletion(line):
    if "/DE" not in line.upper():
        return False
    return any(is_dist_token(t) for t in line.split(","))

def split_deletion(line):
    """Return the deletion restricted to build intermediates, or None."""
    m = re.match(r"^(\s*)PIP\s+(.*?)/DE\s*$", line.rstrip(), re.I)
    if not m:
        return None
    indent, body = m.group(1), m.group(2)
    keep = [t for t in body.split(",") if not is_dist_token(t)]
    keep = [t.rstrip("/DE").rstrip() if t.upper().endswith("/DE") else t
            for t in keep]
    keep = [t for t in keep if t.strip()]
    if not keep:
        return None
    return "%sPIP %s/DE" % (indent, ",".join(keep))

def strip_nulls(data):
    """Tape records are NUL padded; FORTRAN reads the padding as a
    spurious .MAIN. program unit and fails on line 1."""
    return data.rstrip(b"\x00")

def patch_cmd(raw):
    """Comment out every deletion that would destroy a distribution file,
    and answer the interactive DELETE prompts with no."""
    text = raw.decode("latin-1").replace("\r\n", "\n")
    lines, changed = text.split("\n"), 0
    for i, l in enumerate(lines):
        if is_source_deletion(l):
            repl = split_deletion(l)
            lines[i] = "%s %s" % (MARK, l.strip())
            if repl:
                lines[i] += "\n" + repl
            changed += 1
        elif re.match(r"^\s*\.ASK\s+\w+\s+DELETE", l, re.I):
            var = l.split()[1]
            lines[i] = "%s %s\n .SETF %s" % (MARK, l.strip(), var)
            changed += 1
    if not changed:
        return raw, 0
    return "\n".join(lines).replace("\n", "\r\n").encode("latin-1"), changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--outdir", default=os.path.join(HERE, "src"))
    args = ap.parse_args()
    out = args.outdir
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)

    manifest, ndel, nnul = [], 0, 0

    for name in sorted(os.listdir(TAPE)):
        if not name.startswith("["):
            continue
        clean = name.split("]", 1)[1]
        data = open(os.path.join(TAPE, name), "rb").read()
        stripped = strip_nulls(data)
        if stripped != data:
            nnul += 1
        note = "tape"
        if clean.upper().endswith(".CMD"):
            stripped, changed = patch_cmd(stripped)
            if changed:
                ndel += changed
                note = "tape, %d deletion(s) commented out" % changed
        open(os.path.join(out, clean), "wb").write(stripped)
        manifest.append((clean, note))
        continue

    # --- what the tape lost -------------------------------------------
    recovered = {
        # Reproduced VERBATIM by INSTAL.TXT.  These are not guesses.
        "LIB100.CMD": ("recovered verbatim from INSTAL.TXT 9.6", None),
        "LNK10.CMD":  ("recovered verbatim from INSTAL.TXT 9.13", None),
        "LOD10.CMD":  ("recovered from INSTAL.TXT 9.14; the inline overlay "
                       "descriptor is replaced by the reconstruction's own, "
                       "because the module decomposition differs", None),
        # Genuinely gone.  Reimplementations, not recovered source.
        "FDUTIL.FTN": ("REIMPLEMENTATION -- validated: the original ASM100, "
                       "linked against a LIB100 carrying it, reproduces all "
                       "nine shipped .APO libraries", RECON),
        "LNK100.FTN": ("REIMPLEMENTATION -- E module matches lnk100.py, and "
                       "its linked VADD+SPUFLT is byte-identical to the "
                       "shipped BAAHSR block", RECON),
        "LOD100.FTN": ("REIMPLEMENTATION -- load module matches lod100.py, "
                       "1160 of 1160 words", RECON),
        "LOD100.ODL": ("overlay descriptor for the reimplementation's own "
                       "module decomposition, not a copy of FPS's", RECON),
    }
    for fn, (note, src) in recovered.items():
        cand = os.path.join(src, fn) if src else os.path.join(HERE, "recovered", fn)
        if os.path.exists(cand):
            data = open(cand, "rb").read()
            if fn.upper().endswith(".CMD"):
                data, ch = patch_cmd(data)
                if ch:
                    note += "; %d deletion(s) commented out" % ch
            open(os.path.join(out, fn), "wb").write(data)
            manifest.append((fn, note))

    # DEVTABLE.MAC: the manifest and DRV100.CMD both call for DEVTABLE, but
    # the tape holds the name truncated to DEVTAB.MAC.  Supply both.
    dt = os.path.join(out, "DEVTAB.MAC")
    if os.path.exists(dt):
        shutil.copy(dt, os.path.join(out, "DEVTABLE.MAC"))
        manifest.append(("DEVTABLE.MAC",
                         "copy of the tape's DEVTAB.MAC under the name "
                         "DRV100.CMD and the distribution index both use"))

    with open(os.path.join(HERE, "MANIFEST.txt"), "w") as f:
        f.write("FPS-100 install package -- file manifest\n")
        f.write("=" * 66 + "\n\n")
        for n, note in sorted(manifest):
            f.write("%-16s %s\n" % (n, note))
    print("%d files, %d deletions commented out, %d NUL-padded sources trimmed"
          % (len(manifest), ndel, nnul))

if __name__ == "__main__":
    main()
