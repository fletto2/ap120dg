#!/usr/bin/env python3
"""ods1make.py -- build an ODS-1 (Files-11 Level 1) disk image from host files.

Creates an RK05 (or other size) volume that RSX-11M can MOUNT, containing the
files you name. Written to get reconstructed FPS-100 sources onto an RSX
system: the FORTRAN pack in this directory was SYSGEN'd with only RK05 disks
and terminals -- DEV shows no magtape and no paper tape -- so FLX has no
device to read from, and the SimH console send queue is far too small to
type a 20 KB source file in.

    python3 ods1make.py out.dsk LNK100.FTN [more files...]
    python3 ods1make.py -x out.dsk [destdir]      # read files back out
    # then, in RSX:  MOU DK1:XFER  /  PIP *.*=DK1:[200,200]*.*

EVERY STRUCTURE HERE WAS DERIVED BY READING A WORKING VOLUME
(rsx31wStr11andFtn.dsk) RATHER THAN FROM A SPEC, AND EACH WAS CHECKED
AGAINST IT:

  home block (LBN 1)
      0   H.IBSZ  index file bitmap size, blocks
      2   H.IBLB  index file bitmap LBN -- TWO words, high then low.
                  (Getting this wrong shifts every later field by 2 and
                  makes the volume name land at offset 12.)
      6   H.FMAX  maximum number of files
      8   H.SBCL  storage bitmap cluster factor
     10   H.DVTY  device type
     12   H.VLEV  structure level, 0401 for ODS-1
     14   H.VNAM  volume name, 12 bytes ASCII
     30   H.VOWN  owner UIC
     32   H.VPRO  volume protection
     58   H.CHK1  checksum of words 0..28
    472   volume name label, 12 ASCII
    484   owner label, 12 ASCII
    496   format label, "DECFILE11A  "
    510   H.CHK2  checksum of words 0..254

  file headers: one 512-byte block each, starting at LBN IBLB+IBSZ,
  file N at LBN IBLB+IBSZ+N-1.
      0   H.IDOF  ident area offset in WORDS (23 -> byte 46)
      1   H.MPOF  map area offset in WORDS   (46 -> byte 92)
      2   H.FNUM / 4 H.FSEQ / 6 H.FLEV (0401) / 8 H.FOWN / 10 H.FPRO
     12   H.UCHA, H.SCHA
     14   H.UFAT, 32 bytes of FCS attributes:
            0 RTYP (1 fixed, 2 variable), 1 RATT (2 = implied carriage
            control), 2 RSIZ longest record, 4 HIBK (2 words, blocks
            allocated), 8 EFBK (2 words, last block holding data),
            12 FFBY (bytes used in that block)
     46   ident: name 3 words RAD50, type 1 word, version 1 word, dates
     92   map: ESQN,ERVN,EFNU,EFSQ, CTSZ=1, LBSZ=3, USE, MAX, pointers
    510   checksum of words 0..254

  retrieval pointer, 4 bytes, for CTSZ=1 / LBSZ=3:
      byte 0  high-order LBN bits
      byte 1  block count - 1
      byte 2-3 low-order LBN, little endian
    The byte order matters and is not what you would guess: reading it the
    other way round puts BITMAP.SYS at LBN 65817 on a 4800-block volume.

  storage bitmap: 1 = FREE, 0 = allocated. Preceded by a one-block SCB.

  directory entry, 16 bytes: file number, sequence, relative volume,
  name 3 words RAD50, type 1 word, version.

NOTE ON TKB: volumes built here are fully readable and writable. RSX
creates ordinary files on them (the FORTRAN compiler writes its .OBJ) and
CONTIGUOUS files too -- "PIP DK1:CTG.TMP/CO=DK1:LNK100.OBJ" produced a
114-block contiguous file, which is proof the storage bitmap and SCB are
sound.

The task builder nonetheless reports

    TKB -- *DIAG*-ALLOCATION FAILURE ON FILE xxx.TSK

and the cause is NOT in this tool. Ruled out by experiment:
  - target volume space          4,452 free in ONE contiguous run
  - contiguous allocation        PIP /CO succeeds on the same volume
  - SY0: total free space        failed at 3, at 509 and at 1,413 blocks
  - SY0: fragmentation           failed at longest-run 186 and at 376
  - task size                    failed with a 45,898-byte object, having
                                 previously SUCCEEDED with a 55,392-byte one
TKB did build this task successfully earlier in the same session, so it is
something about TKB state or the RSX configuration rather than the volume.
Still unexplained. Build task images on the system pack meanwhile.

  file contents for RTYP=2: a continuous stream of
  [2-byte length][data][pad to even]. Records DO span block boundaries --
  verified on FORRES.MAC, whose record at offset 496 continues into the
  following block.
"""

import sys, os, struct

R50 = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$.?0123456789"
BLK = 512


def r50(s):
    s = (s + "   ")[:3].upper()
    v = 0
    for c in s:
        i = R50.find(c)
        if i < 0:
            i = R50.find('?')
        v = v * 40 + i
    return v


def r50name(name):
    """Three RAD50 words. RSX-11M filenames are NINE characters, not six --
    the directory entry and the header ident area both carry 3 words. Using
    2 words shifts the type and version fields and MOU still succeeds, but
    PIP then reports CANNOT FIND DIRECTORY FILE."""
    n = (name + "         ")[:9].upper()
    return [r50(n[0:3]), r50(n[3:6]), r50(n[6:9])]


def pad12(s, fill=b' '):
    """Exactly 12 bytes. Slice assignment into a bytearray silently resizes
    it if the source is shorter, which corrupts every later offset."""
    b = s.encode() if isinstance(s, str) else s
    return (b + fill * 12)[:12]


def cksum(buf, nwords):
    s = 0
    for i in range(nwords):
        s = (s + struct.unpack_from('<H', buf, 2 * i)[0]) & 0xFFFF
    return s


class Volume:
    def __init__(self, nblocks=4800, fmax=128, vname="XFER",
                 uic=(0o200, 0o200)):
        self.nblocks = nblocks
        self.fmax = fmax
        self.vname = vname
        self.uic = uic
        self.disk = bytearray(nblocks * BLK)
        self.ibsz = (fmax + 4095) // 4096
        self.iblb = 2
        self.hdr0 = self.iblb + self.ibsz          # LBN of file 1's header
        self.files = {}                            # fnum -> dict
        self.next_free = None
        self.next_fnum = 1

    # ---- block-level helpers -------------------------------------------

    def put(self, lbn, data, off=0):
        self.disk[lbn * BLK + off: lbn * BLK + off + len(data)] = data

    def alloc(self, n):
        lbn = self.next_free
        self.next_free += n
        if self.next_free > self.nblocks:
            raise RuntimeError("volume full")
        return lbn

    # ---- file headers ---------------------------------------------------

    def header(self, fnum, name, ext, ufat, extents, owner=None, ver=1,
               ucha=0, scha=0):
        h = bytearray(BLK)
        h[0] = 23                                   # H.IDOF, words
        h[1] = 46                                   # H.MPOF, words
        struct.pack_into('<3H', h, 2, fnum, fnum, 0o401)
        own = owner if owner is not None else (self.uic[1] << 8) | self.uic[0]
        struct.pack_into('<H', h, 8, own)
        struct.pack_into('<H', h, 10, 0o160000)     # H.FPRO
        h[12] = ucha
        h[13] = scha
        h[14:14 + len(ufat)] = ufat
        # ident area
        i = 46
        n = r50name(name)
        struct.pack_into('<5H', h, i, n[0], n[1], n[2], r50(ext), ver)
        h[i + 12:i + 19] = b'07AUG86'               # I.RVDT
        h[i + 19:i + 25] = b'120000'                # I.RVTI
        h[i + 25:i + 32] = b'07AUG86'               # I.CRDT
        h[i + 32:i + 38] = b'120000'                # I.CRTI
        h[i + 38:i + 45] = b'       '               # I.EXDT
        # map area
        m = 92
        struct.pack_into('<4H', h, m, 0, 0, 0, 0)   # ESQN/ERVN/EFNU/EFSQ
        h[m + 6] = 1                                # M.CTSZ
        h[m + 7] = 3                                # M.LBSZ
        h[m + 8] = 2 * len(extents)                 # M.USE, in words
        h[m + 9] = 204                              # M.MAX
        o = m + 10
        for count, lbn in extents:
            if count > 256:
                raise RuntimeError("extent too long for CTSZ=1")
            h[o] = (lbn >> 16) & 0xFF
            h[o + 1] = count - 1
            struct.pack_into('<H', h, o + 2, lbn & 0xFFFF)
            o += 4
        struct.pack_into('<H', h, 510, cksum(h, 255))
        self.put(self.hdr0 + fnum - 1, h)

    # ---- content encoding ------------------------------------------------

    @staticmethod
    def textrecs(data):
        """Encode as FCS variable-length records (RTYP=2)."""
        out = bytearray()
        longest = 0
        text = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        for line in text.split(b'\n'):
            if len(line) > 255:
                line = line[:255]
            longest = max(longest, len(line))
            out += struct.pack('<H', len(line)) + line
            if len(line) & 1:
                out += b'\0'
        return bytes(out), longest

    # ---- volume construction ---------------------------------------------

    def build(self, userfiles):
        # Reserve: boot, home, index bitmap, and one header block per file.
        self.next_free = self.hdr0 + self.fmax

        bitmap_blocks = (self.nblocks + 4095) // 4096
        scb_lbn = self.alloc(1)
        bm_lbn = self.alloc(bitmap_blocks)
        mfd_lbn = self.alloc(1)
        ufd_lbn = self.alloc(1)

        # ---- system files ------------------------------------------------
        # 1 INDEXF.SYS covers boot + home + index bitmap + all headers.
        idx_total = self.hdr0 + self.fmax
        ext = []
        lbn = 0
        left = idx_total
        while left > 0:
            n = min(256, left)
            ext.append((n, lbn))
            lbn += n
            left -= n
        self.header(1, "INDEXF", "SYS", self.contig_ufat(idx_total), ext,
                    owner=0o401, ucha=0o200)
        self.header(2, "BITMAP", "SYS",
                    self.contig_ufat(1 + bitmap_blocks),
                    [(1 + bitmap_blocks, scb_lbn)], owner=0o401, ucha=0o200)
        self.header(3, "BADBLK", "SYS", self.contig_ufat(0), [],
                    owner=0o401, ucha=0o200)
        self.header(4, "000000", "DIR", self.dir_ufat(1), [(1, mfd_lbn)],
                    owner=0o401, ucha=0o200)
        self.header(5, "CORIMG", "SYS", self.contig_ufat(0), [],
                    owner=0o401, ucha=0o200)
        udir = "%03o%03o" % (self.uic[1], self.uic[0])
        self.header(6, udir, "DIR", self.dir_ufat(1), [(1, ufd_lbn)],
                    owner=(self.uic[1] << 8) | self.uic[0], ucha=0o200)
        self.next_fnum = 7

        # ---- user files --------------------------------------------------
        ufd = bytearray()
        for path in userfiles:
            base = os.path.basename(path).upper()
            name, _, ext_s = base.partition('.')
            data = open(path, 'rb').read()
            recs, longest = self.textrecs(data)
            nblk = (len(recs) + BLK - 1) // BLK
            lbn = self.alloc(max(1, nblk))
            self.put(lbn, recs)
            ufat = bytearray(32)
            ufat[0] = 2                                   # RTYP variable
            ufat[1] = 2                                   # RATT implied CC
            struct.pack_into('<H', ufat, 2, longest)      # RSIZ
            struct.pack_into('<H', ufat, 6, max(1, nblk))  # HIBK low word
            struct.pack_into('<H', ufat, 10, max(1, nblk))  # EFBK low word
            ffby = len(recs) % BLK
            struct.pack_into('<H', ufat, 12, ffby)        # FFBY
            fn = self.next_fnum
            self.next_fnum += 1
            self.header(fn, name, ext_s, ufat, [(max(1, nblk), lbn)])
            ufd += self.direntry(fn, name, ext_s)
            print("  %-14s file %3d  LBN %5d  %3d blocks  %5d bytes"
                  % (base, fn, lbn, max(1, nblk), len(recs)))

        # ---- directories ---------------------------------------------------
        mfd = bytearray()
        for fn, nm, ex in ((1, "INDEXF", "SYS"), (2, "BITMAP", "SYS"),
                           (3, "BADBLK", "SYS"), (4, "000000", "DIR"),
                           (5, "CORIMG", "SYS"), (6, udir, "DIR")):
            mfd += self.direntry(fn, nm, ex)
        self.put(mfd_lbn, bytes(mfd))
        self.put(ufd_lbn, bytes(ufd))

        # ---- bitmaps --------------------------------------------------------
        # index file bitmap: bit N-1 set = file N in use
        ib = bytearray(self.ibsz * BLK)
        for fn in range(1, self.next_fnum):
            ib[(fn - 1) >> 3] |= 1 << ((fn - 1) & 7)
        self.put(self.iblb, bytes(ib))

        # storage bitmap: 1 = free
        sb = bytearray(bitmap_blocks * BLK)
        for b in range(self.next_free, self.nblocks):
            sb[b >> 3] |= 1 << (b & 7)
        self.put(bm_lbn, bytes(sb))
        # Storage control block. The layout is not fully understood; these
        # bytes are taken from a working 4800-block RK05 volume and patched
        # with our geometry. Byte 3 is the bitmap block count and the word at
        # 14 is the volume size, both of which match that volume exactly.
        scb = bytearray(BLK)
        scb[3] = bitmap_blocks
        scb[5] = 16
        scb[9] = 16
        struct.pack_into('<H', scb, 14, self.nblocks & 0xFFFF)
        self.put(scb_lbn, bytes(scb))

        self.homeblock()

    @staticmethod
    def contig_ufat(nblk):
        u = bytearray(32)
        u[0] = 1
        struct.pack_into('<H', u, 2, BLK)
        struct.pack_into('<H', u, 6, nblk)
        struct.pack_into('<H', u, 10, nblk)
        return u

    @staticmethod
    def dir_ufat(nblk):
        u = bytearray(32)
        u[0] = 1
        struct.pack_into('<H', u, 2, 16)
        struct.pack_into('<H', u, 6, nblk)
        struct.pack_into('<H', u, 10, nblk + 1)
        return u

    @staticmethod
    def direntry(fnum, name, ext, ver=1):
        n = r50name(name)
        return struct.pack('<8H', fnum, fnum, 0, n[0], n[1], n[2], r50(ext), ver)

    def homeblock(self):
        h = bytearray(BLK)
        struct.pack_into('<H', h, 0, self.ibsz)
        struct.pack_into('<H', h, 2, self.iblb >> 16)
        struct.pack_into('<H', h, 4, self.iblb & 0xFFFF)
        struct.pack_into('<H', h, 6, self.fmax)
        struct.pack_into('<H', h, 8, 1)              # SBCL
        struct.pack_into('<H', h, 10, 0)             # DVTY
        struct.pack_into('<H', h, 12, 0o401)         # VLEV
        h[14:26] = pad12(self.vname, b'\0')
        struct.pack_into('<H', h, 30, (self.uic[1] << 8) | self.uic[0])
        struct.pack_into('<H', h, 32, 0)             # VPRO
        struct.pack_into('<H', h, 34, 0)             # VCHA
        struct.pack_into('<H', h, 36, 0o160000)      # DFPR
        h[44] = 7                                    # H.WISZ window size
        h[45] = 5                                    # H.FIEX default extend
        h[46] = 3                                    # H.LRUC dir LRU
        struct.pack_into('<H', h, 58, cksum(h, 29))
        h[472:484] = pad12(self.vname)
        h[484:496] = pad12("[%03o,%03o]" % (self.uic[1], self.uic[0]))
        h[496:508] = pad12("DECFILE11A")
        struct.pack_into('<H', h, 510, cksum(h, 255))
        self.put(1, bytes(h))

    def write(self, path):
        open(path, 'wb').write(bytes(self.disk))


def extract(img, outdir='.'):
    """Read files back out of an ODS-1 volume.

    Walks the same structures build() writes, so it doubles as a check on
    them. Text files (RTYP=2) are decoded from the variable-record stream
    back into lines.
    """
    d = open(img, 'rb').read()
    h = d[BLK:2 * BLK]
    W = lambda o: struct.unpack_from('<H', h, o)[0]
    ibsz, iblb, fmax = W(0), (W(2) << 16) | W(4), W(6)
    hdr0 = iblb + ibsz
    out = []
    for fn in range(1, fmax + 1):
        off = (hdr0 + fn - 1) * BLK
        if off + BLK > len(d):
            break
        b = d[off:off + BLK]
        fnum, fseq, flev = struct.unpack_from('<3H', b, 2)
        if flev != 0o401 or fnum != fn:
            continue
        i = b[0] * 2
        w = struct.unpack_from('<5H', b, i)
        name = (unr50(w[0]) + unr50(w[1]) + unr50(w[2])).strip()
        ext = unr50(w[3]).strip()
        if name in ('INDEXF', 'BITMAP', 'BADBLK', 'CORIMG') or ext == 'DIR':
            continue
        u = b[14:46]
        rtyp = u[0]
        efbk = (struct.unpack_from('<H', u, 8)[0] << 16) | struct.unpack_from('<H', u, 10)[0]
        ffby = struct.unpack_from('<H', u, 12)[0]
        mp = b[1] * 2
        use = b[mp + 8]
        raw = b[mp + 10:mp + 10 + 2 * use]
        data = b''
        for o in range(0, len(raw), 4):
            lbn = (raw[o] << 16) | struct.unpack_from('<H', raw, o + 2)[0]
            cnt = raw[o + 1] + 1
            data += d[lbn * BLK:(lbn + cnt) * BLK]
        n = (efbk - 1) * BLK + (ffby if ffby else BLK)
        data = data[:n] if n <= len(data) else data
        fname = "%s.%s" % (name, ext) if ext else name
        if rtyp == 2:
            text = bytearray()
            o = 0
            while o + 2 <= len(data):
                ln = struct.unpack_from('<H', data, o)[0]
                if ln == 0xFFFF or o + 2 + ln > len(data):
                    break
                text += data[o + 2:o + 2 + ln] + b'\n'
                o += 2 + ln + (ln & 1)
            data = bytes(text)
        open(os.path.join(outdir, fname), 'wb').write(data)
        out.append((fname, len(data)))
    return out


def unr50(w):
    if w >= 64000:
        return '???'
    return R50[w // 1600] + R50[(w // 40) % 40] + R50[w % 40]


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == '-x':
        for f, n in extract(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '.'):
            print("  %-14s %7d bytes" % (f, n))
        return 0
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    out = sys.argv[1]
    v = Volume()
    print("building %s (%d blocks, UIC [200,200]):" % (out, v.nblocks))
    v.build(sys.argv[2:])
    v.write(out)
    print("  free blocks: %d" % (v.nblocks - v.next_free))
    print("wrote", out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
