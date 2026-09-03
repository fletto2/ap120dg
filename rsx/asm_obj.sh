#!/bin/sh
# asm_obj.sh <source.S|.APS> [workdir] -- assemble ONE source with the
# INSTALLED ASM100 and keep the OBJECT.  Sibling of asm_listing.sh, which
# keeps the listing and sends the object to NL:.
set -e
src=$(readlink -f "${1:?usage: asm_obj.sh <source> [workdir] [inserts...]}")
here=$(cd "$(dirname "$0")" && pwd)
root=$here/../..
# EVERY input must be made absolute BEFORE the cd below, not just $1.  The
# insert arguments were left relative, so `asm_obj.sh refs/X.S wk refs/X.DAT`
# failed with "cannot stat refs/X.DAT" on a file that is plainly there --
# the same relative-path-across-a-cd trap already recorded for refjob.sh.
_ins=""
for _i in "$@"; do _ins="$_ins $(readlink -f "$_i" 2>/dev/null || echo "$_i")"; done
set -- $_ins
work=${2:-./asmobj-work}
mkdir -p "$work" && cd "$work"
# Tape sources carry trailing NULs and CR-LF; both must go, or FORTRAN and
# ASM100 read a spurious record (see CLAUDE.md).
tr -d '\000' < "$src" | tr -d '\r' > RTN.APS
cp "$here/fps.installed/sysbig.dsk" . ; cp "$here/fps.installed/usagi0.dsk" .
# $INSERT files must be staged alongside the source under their OWN
# names -- FPS's SEQV1.S does "$INSERT SEQV1.DAT", and FDUTIL supplies the
# .DAT extension when a name carries none.
extra="RTN.APS"
shift 2 2>/dev/null || shift $# 
for i in "$@"; do cp "$i" . ; extra="$extra $(basename "$i")"; done
python3 "$here/ods1make.py" -n ASMSRC asmsrc.dsk $extra
cp "$here/asm_obj.ini" run.ini
rm -f asmobj.log
timeout 420 "$root/simh/BIN/pdp11" run.ini >/dev/null 2>&1 || true
pkill -x pdp11 || true
grep -aE 'ERROR\(S\)|ASSEMBLY COMPLETED' asmobj.log || true
mkdir -p out && (cd out && python3 "$here/ods1make.py" -x ../asmsrc.dsk . >/dev/null)
ls -l out/RTN.APO 2>/dev/null
