#!/bin/sh
# asm_listing.sh <ROUTINE> [workdir]
#
# Assemble ONE basic-math routine with the INSTALLED ASM100 on the 11/44
# replica and keep the LISTING, which is the only reliable PS-address-to-
# source mapping.  refs/listings/VDIV.LST and VSQRT.LST were made by hand;
# this makes it repeatable.
#
# Two extraction traps, both hit while producing VDIV.LST:
#   - cut the block on $TITLE boundaries, NOT on a guessed line count; a
#     short cut assembles only the prologue and looks like a whole routine.
#     Check the abstract's "SIZE: n LOCATIONS" against the last PS address.
#   - a `$END` pattern also matches `$ENDIF`, truncating at the conditional
#     assembly block.  Cut on the NEXT $TITLE instead.
set -e
R=${1:?usage: asm_listing.sh <ROUTINE> [workdir]}
here=$(cd "$(dirname "$0")" && pwd)
root=$here/../..
work=${2:-./asmlst-work}
mkdir -p "$work" && cd "$work"
tr -d '\r' < "$root/software/fps100sw/[327,010]BAASRC.APS" |
  awk -v R="$R" '$0 ~ ("\\$TITLE +" R "$"){f=1} f&&/\$TITLE/&&!/'"$R"'$/{exit} f{print}' > RTN.APS
printf '        $END\n' >> RTN.APS
echo "extracted $(wc -l < RTN.APS) lines for $R"
cp "$here/fps.installed/sysbig.dsk" .
cp "$here/fps.installed/usagi0.dsk" .
python3 "$here/ods1make.py" -n ASMSRC asmsrc.dsk RTN.APS
cp "$here/asm_listing.ini" run.ini
rm -f asmlst.log
# The .ini has no `quit` after ASSEMBLY COMPLETED -- this SimH build's
# `expect` takes `; continue` and stopping cleanly from a rule is awkward
# (`; once` is not valid here, see CLAUDE.md).  So the run is bounded by
# this timeout instead; the assembly itself finishes well inside it.
timeout 420 "$root/simh/BIN/pdp11" run.ini >/dev/null 2>&1 || true
pkill -x pdp11 || true
grep -E 'ERROR\(S\)|ASSEMBLY COMPLETED' asmlst.log || true
mkdir -p out && (cd out && python3 "$here/ods1make.py" -x ../asmsrc.dsk . >/dev/null)
if [ -f out/RTN.LST ]; then
  mkdir -p "$root/ap120dg/refs/listings"
  cp out/RTN.LST "$root/ap120dg/refs/listings/$R.LST"
  echo "wrote refs/listings/$R.LST ($(wc -l < out/RTN.LST) lines)"
fi
