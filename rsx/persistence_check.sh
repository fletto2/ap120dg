#!/bin/sh
# Cold-boot the INSTALLED packs and list what survived -- WITHOUT modifying
# them.
#
# `fps_persistence_check.ini` attaches `fps.installed/sysbig.dsk` directly,
# and booting RSX from a pack WRITES to it: measured, `sysbig.dsk` comes
# back different while `usagi0.dsk` is byte-identical (the system device is
# mounted, the work disk merely read).  A persistence check that alters the
# artifact it is checking is not evidence about that artifact, so this
# copies both packs to a scratch directory and boots the copies.
#
#     ./persistence_check.sh [scratch-dir]
#
# The simulator writes its console transcript to a LOG FILE, not stdout --
# the .ini does `set console log=`.  Reading stdout shows nothing at all and
# is indistinguishable from a hung simulator; this script prints the log.

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
SCRATCH=${1:-/tmp/fps_persist}
PDP11="$HERE/../../simh/BIN/pdp11"

for f in sysbig.dsk usagi0.dsk; do
    [ -f "$HERE/fps.installed/$f" ] || { echo "missing $f" >&2; exit 1; }
done

mkdir -p "$SCRATCH"
cp "$HERE/fps.installed/sysbig.dsk" "$HERE/fps.installed/usagi0.dsk" "$SCRATCH/"
sed -e "s#att hk0 .*#att hk0 $SCRATCH/sysbig.dsk#" \
    -e "s#att hk1 .*#att hk1 $SCRATCH/usagi0.dsk#" \
    "$HERE/fps_persistence_check.ini" > "$SCRATCH/check.ini"

( cd "$SCRATCH" && timeout 900 "$PDP11" check.ini >/dev/null 2>&1 || true )
pkill -x pdp11 2>/dev/null || true

LOG=$(ls -t "$SCRATCH"/*.log 2>/dev/null | head -1)
[ -n "$LOG" ] || { echo "no console log written -- did the boot start?" >&2; exit 1; }

echo "=== what survived the cold boot ==="
grep -aE 'RSX-11M|MAPPED|\.OLB;|\.LIB;|\.TSK;|Total of' "$LOG" || true

echo
echo "=== promoted packs unchanged? ==="
for f in sysbig.dsk usagi0.dsk; do
    if cmp -s "$SCRATCH/$f" "$HERE/fps.installed/$f"; then
        echo "  $f  unchanged by the boot"
    else
        echo "  $f  MUTATED by the boot (expected for the system pack)"
    fi
done
echo "  fps.installed/ itself was never attached, so it is untouched."
