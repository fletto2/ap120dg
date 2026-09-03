#!/bin/sh
# refjob.sh <job.cmd> [libs...]   -- run one reference job through the
# INSTALLED recovered LOD100 and extract whatever it wrote.
#
# Uses the tools already on the promoted packs, so there is no 12-minute
# rebuild: LODHYB.TSK is at DM1:[100,100].  The job is staged as JOB.CMD on
# a transfer volume mounted DM2: with ASN DM2:=SY:, so the dialogue needs no
# device prefixes.
set -e
job=${1:?usage: refjob.sh <job.cmd> [libs...]}; shift
# Resolve every input to an ABSOLUTE path BEFORE cd-ing into the work
# directory -- otherwise a relative "refs/hasi.cmd" stops resolving the
# moment we move, which is exactly how the first run failed.
job=$(readlink -f "$job")
libs=""
for l in "$@"; do libs="$libs $(readlink -f "$l")"; done
set -- $libs
here=$(cd "$(dirname "$0")" && pwd)
root=$here/../..
work=${WORKDIR:-./refjob-work}
mkdir -p "$work" && cd "$work"
cp "$job" JOB.CMD
files="JOB.CMD"
for l in "$@"; do cp "$l" . ; files="$files $(basename "$l")"; done
cp "$here/fps.installed/sysbig.dsk" .
cp "$here/fps.installed/usagi0.dsk" .
python3 "$here/ods1make.py" -n REFDATA refdata.dsk $files
cp "$here/refjob.ini" run.ini
rm -f refjob.log
timeout 420 "$root/simh/BIN/pdp11" run.ini >/dev/null 2>&1 || true
pkill -x pdp11 || true
sed -n '/RUN DM1/,$p' refjob.log | head -40
mkdir -p out && (cd out && python3 "$here/ods1make.py" -x ../refdata.dsk . >/dev/null)
ls -l out/
