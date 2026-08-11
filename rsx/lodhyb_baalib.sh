#!/bin/sh
# Build the recovered LOD100 hybrid on the 11/44 replica and run the
# production-math-library job that used to fail with ERROR 5 / ERROR 2:
# FORCE VADD across BAALIB + UTLLIB + APFLIB + SYMLIB.
#
# The expected result is a 236-word load module holding three code blocks --
# VADD 14 instructions at PS 16, SPUFLT 8 at PS 30, RESLVE 27 at PS 38 --
# which is byte-for-byte what lod100.py produces for the same job and is the
# same 49-instruction closure FPS's own VADD.APO ships.
#
# Note it refreshes FDUTIL in LB:[1,1]LIB100.OLB first.  The installed
# library is a THIRD copy of FDUTIL and does not track the source; a stale
# one makes every INFILE call fail with ERROR 32, INVALID LOGICAL UNIT
# NUMBER, which does not look like a stale-library problem at all.
set -e
here=$(cd "$(dirname "$0")" && pwd)
root=$here/../..
work=${1:-./lodhyb-work}
mkdir -p "$work" && cd "$work"
cp "$root/ap120dg/recovered/LOD100_HYBRID.FTN" LODHYB.FTN
cp "$root/ap120dg/recovered/LOD100_HYBRID.ODL" LODHYB.ODL
cp "$here/lod100_hybrid_tkb.cmd"               LODHYB.CMD
cp "$here/lodhyb_baalib.cmd"                   LODREC.CMD
cp "$here/lodhyb_vadd_job.cmd"                 VADD.CMD
cp "$root/ap120dg/reconstructed/FDUTIL.FTN"    FDUTIL.FTN
for f in BAALIB UTLLIB APFLIB SYMLIB; do
  tr -d '\000' < "$root/software/fps100sw/[327,010]$f.APO" > $f.APO
done
cp "$here/fps.installed/sysbig.dsk" .
cp "$here/lodhyb_baalib.ini" run.ini
python3 "$here/ods1make.py" -n LODREC lodrec.dsk LODHYB.FTN LODHYB.ODL \
    LODHYB.CMD LODREC.CMD VADD.CMD FDUTIL.FTN \
    BAALIB.APO UTLLIB.APO APFLIB.APO SYMLIB.APO
rm -f lodrec.log
timeout 1200 "$root/simh/BIN/pdp11" run.ini >/dev/null 2>&1 || true
pkill -x pdp11 || true
sed -n '/RUN LODHYB/,$p' lodrec.log
mkdir -p out && (cd out && python3 "$here/ods1make.py" -x ../lodrec.dsk .)
