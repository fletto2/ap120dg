#!/bin/sh
# fetch_kits.sh -- download the PDP-11 FORTRAN kits from bitsavers.
#
# The DEC images are not redistributed in this repository; this script
# fetches them from bitsavers and verifies them against the checksums
# recorded in README.md.
#
# Usage:  ./fetch_kits.sh [destination-directory]   (default: this directory)

set -e
DEST="${1:-$(dirname "$0")}"
BASE="http://www.bitsavers.org/bits/DEC/pdp11/discimages/rk05"

FILES="AN-1822C-BC_F4RSX_V2.2.dsk.gz rsx31wStr11andFtn.dsk.gz pdp11-f77-rsx-v40-bin.rk.gz"

cd "$DEST"

for f in $FILES; do
    if [ -f "$f" ]; then
        echo "have    $f"
    else
        echo "fetch   $f"
        if command -v curl >/dev/null 2>&1; then
            curl -fL -O "$BASE/$f"
        else
            wget "$BASE/$f"
        fi
    fi
done

echo
echo "Verifying:"
sha256sum -c - <<'EOF'
689aaec104dff33072dcdb4182e7ca7254899ea5a5477aef9b40ce02adda53ad  AN-1822C-BC_F4RSX_V2.2.dsk.gz
f6367a7ffa312c52fd1dc2f2b08daba0542d87c68c0ba66421d2645fef529602  pdp11-f77-rsx-v40-bin.rk.gz
bc025ae416b2d1728974ec0d89158ee90692d535d728bc769441a77111881291  rsx31wStr11andFtn.dsk.gz
EOF

echo
echo "Decompressing:"
for f in $FILES; do
    out=$(basename "$f" .gz)
    [ -f "$out" ] || gunzip -k "$f"
    echo "  $out"
done

echo
echo "Done. To boot the ready-built FORTRAN system:"
echo "    pdp11 boot_rsx.ini"
