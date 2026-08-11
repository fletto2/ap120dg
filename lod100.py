#!/usr/bin/env python3
"""lod100.py — FPS AP-120B / FPS-100 Loader

Replacement for the lost LOD100 utility.  Reads APO object modules (produced
by ASM100, or taken from the FPS library archives), links and locates them,
and produces the load modules that are transferred to the FPS-100 and
executed, plus the HASI host-callable interface routines.

LOD100.FTN was deleted from the distribution disk during installation
(PDS100.CMD: "PIP LOD100.FTN;1,LOD100.MAP;*/DE") and is not present on the
FPS-100 software tape.  This is a reimplementation from the published
specification.

PROVENANCE — every format detail below is taken from one of:
  [M]  FPS-100 Loader (LOD100) Reference Manual, 860-7423-000, Sept 1979
       chapter 4 "Output From LOD100" (load module), chapter 2 (commands)
  [F]  FDAPEX.FTN, subroutine FSLMLD — the host-resident load module loader
       that actually consumes these blocks.  Where [M] and [F] disagree on
       naming, [F] wins: it is the code that reads the file.
  [L]  lnk100.py — APO parsing and symbol resolution, reused directly.

LOAD MODULE FORMAT
------------------
A load module is a sequence of blocks.  Each block is an 8-word header
followed by data records of any length.  All words are host integers; on a
16-bit host (PDP-11, Nova) they are 16-bit two's complement. [M 4.2]

FSLMLD dispatches on TTYPE = word0 + 1 [F]:

  type 0  code / overlay map / 32-bit MD data
          header: [0, cnt, addr, pg, dest, 0, 0, 0]
            cnt   number of host words in the data record that follows
            addr  destination address in the FPS-100
            pg    main-data page (used only when dest=1)
            dest  0 = program source memory, 1 = main data memory
          For dest=0 FSLMLD calls LOADPS(buf, addr, cnt*PAKFAC/4), so on a
          16-bit host one 64-bit PS instruction occupies 4 words. [F 1010]
          For dest=1 it calls APPUT(buf, addr, cnt*PAKFAC/2, 0), so one MD
          value occupies 2 words. [F 1400]

  type 1  data block
          header: [1, cnt, 0, pg, 0, 0, 0, 0]   cnt = number of records
          record: [valtyp, repcnt, addr, 0, va, vb, vc, vd]
            valtyp 1 = 16-bit integer   (APPUT mode 1)
                   2 = host real        (APPUT mode 2)
                   3 = complex          (rejected by FSLMLD)
                   4 = 38-bit triple    (APPUT mode 0, taken from vb) [F 2300]
          For valtyp 4, [M 4.2.2] assigns va = bits 0-5, vb = bits 6-21,
          vc = bits 22-37; FSLMLD passes &vb onward, i.e. the top 32 bits.

  type 2  information block
          header: [2, ppaad, ppaend, lmid, init, 0, 0, 0]
          FSLMLD stores these into /APLDCM/ as IPPAAD, IPPAND, IDLM; if
          init is non-zero it is APPUT to address 1 as 2 integer words. [F 600]
          [M 4.2.3] calls words 2/4/5 ppasz/ovlen/ovaddr; the loader treats
          word 2 as the parameter-passing-area END address.

  type 3  end block
          [3, 0, ...] logical end — FSLMLD calls OMASK(15) and returns.
          [3, 1, ...] terminating end, last record of the module. [M 4.2.4]

OUTPUT FORMS
------------
  binary       raw 16-bit little-endian words, loaded with APLMLD(id,arr,size)
  host         a FORTRAN subroutine of DATA statements ending in
               CALL FSLMLD(id, CODE) — the default form. [M 4.2.5, fig 4-1]
  HASI         host FORTRAN subroutines matching the FPS-100 entry points in
               name and formal parameters. [M 4.3]

Usage:
  python3 lod100.py [options] input.APO [input.APO ...]
  python3 lod100.py -c commands.cmd

  -o FILE        write binary load module
  -H FILE        write host-resident FORTRAN load module
  -A FILE        write HASI interface routines
  -m FILE        write load map (default: stderr with -M)
  -i N           load module identifier (LMID, default 1)
  -e NAME        primary entry point
  -c FILE        read LOD100 commands from FILE ('-' for stdin)
  --psoff N      offset applied to all program source addresses
  --mdoff N      offset applied to all main data addresses
  --mode ADC|UDC HASI calling convention (default ADC)
  -M             print the load map
"""

import sys, os, struct, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lnk100 import parse_apo, Linker, parse_octal

# ── Load module construction ────────────────────────────────────────

DEST_PS = 0
DEST_MD = 1

VALTYP_INT    = 1
VALTYP_REAL   = 2
VALTYP_TRIPLE = 4


def _signed16(v):
    """Coerce to the 16-bit two's complement value a 16-bit host stores."""
    v &= 0xFFFF
    return v - 0x10000 if v >= 0x8000 else v


class LoadModule:
    """Builds the block sequence described in [M 4.2] / consumed by [F]."""

    def __init__(self, lmid=1):
        self.lmid = lmid
        self.words = []          # host words, still unsigned
        self._ended = False

    def _header(self, t, w1=0, w2=0, w3=0, w4=0):
        self.words.extend([t, w1, w2, w3, w4, 0, 0, 0])

    def add_code_ps(self, instrs, addr=0):
        """Code block to program source memory.  4 host words per instruction."""
        if not instrs:
            return
        data = []
        for ins in instrs:
            data.append((ins >> 48) & 0xFFFF)
            data.append((ins >> 32) & 0xFFFF)
            data.append((ins >> 16) & 0xFFFF)
            data.append(ins & 0xFFFF)
        # cnt counts host words, and FSLMLD derives the instruction count as
        # cnt/4 -- so cnt must be the word count, not the instruction count.
        self._header(0, len(data), addr, 0, DEST_PS)
        self.words.extend(data)

    def add_code_md(self, values, addr=0, page=0):
        """32-bit values into main data memory (overlay maps, packed tables)."""
        if not values:
            return
        data = []
        for v in values:
            data.append((v >> 16) & 0xFFFF)
            data.append(v & 0xFFFF)
        self._header(0, len(data), addr, page, DEST_MD)
        self.words.extend(data)

    def add_code_image(self, instrs, addr=0, page=0):
        """An overlay segment's PS image, staged in main data.

        FSLMLD moves it with APPUT(...,(CNT*PAKFAC)/2,0) under the comment
        "32 BITS OF HOST PER MD WORD", and advances IPTR by CNT -- so CNT is
        a host-word count here exactly as it is on the PS path, and one MD
        word holds two host words.  A 64-bit instruction therefore needs
        FOUR host words and occupies TWO MD words.

        add_code_md() must not be used for this: it packs each value into
        32 bits, which silently discards the top half of every instruction.
        """
        if not instrs:
            return
        data = []
        for ins in instrs:
            data.append((ins >> 48) & 0xFFFF)
            data.append((ins >> 32) & 0xFFFF)
            data.append((ins >> 16) & 0xFFFF)
            data.append(ins & 0xFFFF)
        self._header(0, len(data), addr, page, DEST_MD)
        self.words.extend(data)

    def add_dbib_block(self, recs, page=0):
        """One data block per ***DBIB block, values already encoded."""
        self._header(1, len(recs), 0, page, 0)
        for dt, rpt, addr, vals in recs:
            self.words.extend([dt, rpt, addr, 0] + [v & 0xFFFF for v in vals[:4]])

    def add_code_image_words(self, words, addr=0, page=0):
        """Main-data words written as a type-0 block, two host words each.

        This is FINISH's "WRTLM(0,0,4,addr,0,1,...)" followed by one data
        record: a 4-host-word block is TWO main-data words.
        """
        data = []
        for w in words:
            data.append((w >> 16) & 0xFFFF)
            data.append(w & 0xFFFF)
        self._header(0, len(data), addr, page, DEST_MD)
        # FINISH writes the payload with WRTLM MODE 1, which emits REC(8) --
        # a full EIGHT-word record whatever the header count says.  That is
        # why these blocks sit 16 words apart in the load module even though
        # they carry only two main-data words.
        self.words.extend(data + [0] * (8 - len(data)))

    def add_data_block(self, records, page=0):
        """Data block: each record is (valtyp, repcnt, addr, value)."""
        if not records:
            return
        self._header(1, len(records), 0, page, 0)
        for valtyp, repcnt, addr, value in records:
            if valtyp == VALTYP_TRIPLE:
                # [M 4.2.2] va=bits 0-5, vb=bits 6-21, vc=bits 22-37.
                va = value & 0x3F
                vb = (value >> 6) & 0xFFFF
                vc = (value >> 22) & 0xFFFF
                vd = 0
            elif valtyp == VALTYP_REAL:
                va, vb, vc, vd = struct.unpack('<4H',
                                               struct.pack('<f', float(value)) + b'\0\0\0\0')
            else:
                va, vb, vc, vd = value & 0xFFFF, 0, 0, 0
            self.words.extend([valtyp, repcnt, addr, 0, va, vb, vc, vd])

    def add_info(self, ppa_addr=0, ppa_end=0, ovlen=0, ovaddr=0):
        """Information block. [M 4.2.3] names words 5/6 ovlen/ovaddr, and
        FSLMLD does APPUT(LMBUF(IPTR+4),1,2,1) when word 5 is non-zero --
        i.e. it copies the (ovlen, ovaddr) pair into main data addresses 1-2,
        which is where the supervisor's overlay loader looks for the map."""
        self.words.extend([2, ppa_addr, ppa_end, self.lmid, ovlen, ovaddr, 0, 0])

    def end(self, terminating=False):
        """Logical end block.

        [M 4.2.4] documents two end blocks, logical `3 0` and terminating
        `3 1`, the latter "the last record in the module" -- but Figure
        4-1's SAMPLE HOST-RESIDENT MODULE ends

            DATA CODE( 77),CODE( 78),CODE( 79),CODE( 80)/  3, 0, 0, 0/
            DATA CODE( 81),CODE( 82),CODE( 83),CODE( 84)/  0, 0, 0, 0/
            CALL FSLMLD ( 1,CODE)

        with the LOGICAL end as its last record and no terminating one,
        which is also what the recovered LOD100 emits: ENDLNK's
        `IF (.NOT.TASKFL) CALL WRTLM (0,3,0,0,...)` and nothing after it.
        So the terminating block belongs to the binary /D module, not to
        the host-resident default, and it is off unless asked for.

        The same figure confirms the info record's shape -- `2, 3, -5, 1`
        is type, PPA ADDRESS, PPA SIZE (negative, i.e. a large unsigned
        count of the remaining main data), LMID.
        """
        if self._ended:
            return
        self._header(3, 0)
        if terminating:
            self._header(3, 1)
        self._ended = True

    # ── emitters ────────────────────────────────────────────────────

    def to_binary(self):
        return b''.join(struct.pack('<H', w & 0xFFFF) for w in self.words)

    def write_binary(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.to_binary())
        return len(self.words)

    def write_host_resident(self, filename, per_sub=2000):
        """FORTRAN subroutine of DATA statements ending in CALL FSLMLD [M fig 4-1].

        Split across several subroutines when the array would exceed per_sub
        words, because some host compilers cap the number of DATA statements
        -- the manual notes LOD100 does exactly this.
        """
        chunks = [self.words[i:i + per_sub]
                  for i in range(0, len(self.words), per_sub)] or [[]]
        with open(filename, 'w') as f:
            for seq, chunk in enumerate(chunks, start=1):
                name = "L%d" % (self.lmid * 100 + seq)
                f.write("      SUBROUTINE %s\n" % name)
                f.write("      INTEGER CODE(%6d)\n" % len(chunk))
                for i in range(0, len(chunk), 4):
                    group = chunk[i:i + 4]
                    idx = ",".join("CODE(%6d)" % (i + j + 1) for j in range(len(group)))
                    f.write("      DATA %s/\n" % idx)
                    f.write("     *%s/\n" % ",".join("%7d" % _signed16(w) for w in group))
                f.write("      CALL FSLMLD(%6d,CODE)\n" % self.lmid)
                f.write("      RETURN\n      END\n")
        return len(chunks)


# ── Overlay structures ──────────────────────────────────────────────
#
# [M 2.8]  Tasks consist of overlay segments held in main data memory and
# copied into program source memory to run.  The start of each segment
# defines a PS partition boundary; a partition is the smallest division of
# PS, and at most one segment may occupy a partition at a time.
#
# LOD100 builds one overlay table per task (.MPnnn) plus ISRMAP for the
# interrupt service routines, and a PS partition table initialised to zero.

MD_WORDS_PER_INSTR = 2   # a 64-bit instruction spans two 38-bit MD words
# The recovered code calls this OVMESZ, the overlay-map entry size in MD
# words.  OVMESZ is READ twice in LINKS -- "IVAL(3)=OVPTR*OVMESZ" for the
# info record's ovlen, and "OVPDTA(OVPPTR,1)=DBBRK+(I-1)*OVMESZ" for each
# entry's address -- and SET NOWHERE, so like OVFLG, LUNMAP, CMPFLG and
# PARMAX it belongs to the lost mainline.  Its value is fixed by the code
# itself: the stride must match LINKS' J advance, which is 8 host words
# (4 MD words) in general and 16 (8 MD words) when building tasks.
OVT_ENTRY_WORDS = 8          # [M table 2-1] -- task mode
OVT_ENTRY_WORDS_FLAT = 4     # without tasks; see build_overlay_table
# TCB lengths from SYSDEF.DAT, the supervisor's own definition file, NOT
# from Loader table 2-2.  SYSDEF ends the chain with "MINTCB = SRS+15." and
# "MAXTCB = FLAGS+3", which evaluate to 62 and 147, so the lengths are 63 and
# 148; KERNEL.S reads MINTCB+1 as the start of the maximum save area.  Table
# 2-2 says 64 and 150 -- it lists "27-31 DPX(0) - DPX(3)", five word numbers
# for four registers, and runs one high from there, two by the end.
TCB_WORDS = 148              # through the maximum save area
PSPMAX = 50                  # PS partition table size; the mainline sets it,
                             # and FINISH emits "4, 50, <break>" to zero it
TCB_MIN_WORDS = 63           # through the minimum save area only; /M


class OverlaySegment:
    def __init__(self, num, parent=None):
        self.num = num
        self.parent = parent
        self.children = []
        self.inputs = []         # object modules loaded into this segment
        self.libs = []           # of those, the ones a LIB command brought in
        self.force_at = []       # FORCE names in effect when each input was named
        self.noload_at = []      # NOLOAD names likewise
        self.linker = None
        self.ps_addr = 0
        self.md_addr = 0
        self.length = 0
        self.task_id = 0
        self.first_partition = 0
        self.n_partitions = 0

    def __repr__(self):
        return "OverlaySegment(%d, ps=%d, len=%d)" % (
            self.num, self.ps_addr, self.length)


def parse_tree(spec):
    """Parse a TREE structure-spec into OverlaySegment roots. [M 2.3.8]

    '(' starts a new overlay level, ')' rescinds one, and bare numbers name
    the segments contained in the current level.  A segment introduced in a
    level nested inside another segment's level is that segment's child:

        TREE ( (1 (2) (3) ) (4) (5) )

    gives roots 1, 4, 5 with 2 and 3 subordinate to 1.
    """
    toks = spec.replace('(', ' ( ').replace(')', ' ) ').split()
    roots, stack, last = [], [], []
    # `last` tracks the most recently seen segment at each open level, which
    # is what a deeper level attaches to.
    for t in toks:
        if t == '(':
            stack.append(last[-1] if last else None)
            last.append(None)
        elif t == ')':
            if not stack:
                raise ValueError("TREE: unbalanced ')'")
            stack.pop()
            last.pop()
        else:
            try:
                num = int(t)
            except ValueError:
                raise ValueError("TREE: expected overlay number, got %r" % t)
            parent = stack[-1] if stack else None
            seg = OverlaySegment(num, parent)
            if parent is None:
                roots.append(seg)
            else:
                parent.children.append(seg)
            if last:
                last[-1] = seg
            else:
                last.append(seg)
    if stack:
        raise ValueError("TREE: unbalanced '('")
    return roots


def walk_segments(roots):
    out = []

    def rec(seg):
        out.append(seg)
        for c in seg.children:
            rec(c)
    for r in roots:
        rec(r)
    return out


def allocate_overlays(roots, psoff=0):
    """Assign PS addresses.  A root starts at psoff; a child starts where its
    parent ends, so siblings share a start address and exclude one another --
    the standard tree overlay policy the partition table describes."""
    def rec(seg, base):
        seg.ps_addr = base
        for c in seg.children:
            rec(c, base + seg.length)
    for r in roots:
        rec(r, psoff)


def compute_partitions(segments):
    """Derive the PS partition table boundaries and fill in each segment's
    first-partition index and partition count. [M 2.8]

    Boundaries are the distinct segment start addresses; the table is closed
    by the highest end address.  A segment occupies every partition its own
    [start, start+length) range intersects -- which is how the manual gets
    3 partitions for a segment spanning 100-200 over boundaries 100/150/175.
    """
    if not segments:
        return []
    starts = sorted({s.ps_addr for s in segments})
    end = max(s.ps_addr + s.length for s in segments)
    bounds = starts + [end]
    for s in segments:
        s_end = s.ps_addr + s.length
        covered = [i for i in range(len(bounds) - 1)
                   if bounds[i] < s_end and bounds[i + 1] > s.ps_addr]
        s.first_partition = (covered[0] + 1) if covered else 0
        s.n_partitions = len(covered)
    return bounds[:-1]


def db_addr_of(blocks, name):
    for n, addr, length in blocks:
        if n == name:
            return addr
    return None


def emit_dbib(lm, modules, block_addr):
    """Turn each ***DBIB block into a load-module data block, as DTALNK does.

    DTALNK reads a record as

        dbid  reladdr  DT  rptcnt  value... [relocation triplet]

    with dbid, reladdr, DT and rptcnt in RADIX but the VALUE in DECIMAL
    (label 8100 uses radix 10 explicitly), resolves the address as the named
    block's base plus reladdr, and emits

        CALL WRTLM (1,DT,RPTCNT,ADDR,0,VALVEC(1),...,VALVEC(4),...)

    i.e. the eight-word record [DT, rptcnt, addr, 0, v1, v2, v3, v4].  DT
    above 16 means RELOCATABLE: DT=DT-16 and DTAREL consumes the trailing
    triplet, of which type 3 is a data-block reference whose argument is
    another dbid -- that is how "$DATA RDYQUE(1) RDYQUE" gets the block's
    own base as its value.

    A type-1 value occupies one word, a type-4 (38-bit triple) three.
    """
    for mod, addrs in modules:
        for block in mod.dbib:
            recs = []
            for tok in block:
                if len(tok) < 4:
                    continue
                dbid = parse_octal(tok[0])
                rel = parse_octal(tok[1])
                dt = parse_octal(tok[2])
                reloc = dt > 16
                if reloc:
                    dt -= 16
                rpt = parse_octal(tok[3])
                nval = 3 if dt == 4 else 1
                vals = [int(x) for x in tok[4:4 + nval]]
                rest = tok[4 + nval:]
                if reloc and len(rest) >= 3:
                    rtype, rarg = parse_octal(rest[1]), parse_octal(rest[2])
                    if rtype == 3 and rarg in addrs:
                        # WHICH word the relocation lands on depends on the
                        # type.  DTALNK relocates VALVEC(1) for an integer at
                        # label 8100 but VALVEC(3) at 8460, the tail of the
                        # 38-bit-triple path -- and [M 4.2.2] puts bits 22-37
                        # in vc, so the address rides in the third word.
                        k = 2 if dt == 4 else 0
                        vals[k] = (vals[k] + addrs[rarg]) & 0xFFFF
                base = addrs.get(dbid)
                if base is None:
                    continue
                vals += [0] * (4 - len(vals))
                recs.append((dt, rpt, base + rel, vals))
            if recs:
                lm.add_dbib_block(recs)


def build_overlay_table(segments, partition_table_addr, task_mode=False,
                        page=0):
    """One main-data entry per segment. [M table 2-1]

    The field ORDER is the manual's, and the recovered LINKS confirms it
    word for word -- it fills BUFFER two host words per MD word, high half
    then low:

        BUFFER(J)   = (OVDTA(I,6)&15)*8   BUFFER(J+1) = OVDTA(I,1)  segment
        BUFFER(J+2) = (OVDTA(I,6)&15)     BUFFER(J+3) = OVDTA(I,3)  MD addr
        BUFFER(J+4) = 0                   BUFFER(J+5) = OVDTA(I,2)  PS addr
        BUFFER(J+6) = 0                   BUFFER(J+7) = OVDTA(I,4)>>1  length

    so the MD PAGE rides in the HIGH half of the first two words, as
    page*8 and page.  OVDTA(,4) holds the length doubled, because
    elsewhere it is used as an MD-word count and a PS instruction occupies
    two MD words; the table wants PS words, hence the shift.

    THE ENTRY IS FOUR MD WORDS UNLESS TASKS ARE BEING BUILT.  LINKS
    advances J by 8 host words in general and by 8 TWICE under
    "IF (.NOT.TASKFL) GO TO 6540", so task id, residency, partition
    pointer and partition count exist only in task mode.  This wrote all
    eight unconditionally.

    Residency is not left to the supervisor either: LINKS sets
    BUFFER(J+11)=1 when I.EQ.1, under the comment "SHOULD BE RESIDENT" --
    the FIRST segment, i.e. the root, is marked resident.
    """
    words = []
    for i, s in enumerate(segments):
        words.extend([
            ((page * 8) << 16) | (s.num & 0xFFFF),   # 1 segment number
            (page << 16) | (s.md_addr & 0xFFFF),     # 2 MD address
            s.ps_addr,                               # 3 PS address
            s.length,                                # 4 length in PS words
        ])
        if not task_mode:
            continue
        words.extend([
            s.task_id,                               # 5 task id
            1 if i == 0 else 0,                      # 6 resident (root only)
            # 7 and 8 are ZERO.  The manual names them the first partition
            # entry and the partition count, but that describes the table the
            # SUPERVISOR maintains -- LINKS writes "BUFFER(J+12)=0 ...
            # BUFFER(J+15)=0" and leaves both for it to fill in.
            0,                                       # 7 first partition entry
            0,                                       # 8 partitions required
        ])
    return words


# THE LOADER WRITES ONLY RLINK AND LLINK INTO A TCB.
#
# [M 2.9] table 2-2 lists all sixteen fields, and an earlier version of this
# file built the whole 148-word block from it -- ovlptr, ovlcnt, dpri, status,
# taddr, the save areas.  None of it was ever emitted, and FPS's own FINISH
# says why: per task it writes one 4-host-word data block at the TCB address,
#
#     CALL WRTLM(0,0,4,TSKDTA(I,8),0,1,...)      header, 4 host words
#     CALL WRTLM(1,0,TSKDTA(J,8),0,TSKDTA(K,8),...)   RLINK then LLINK
#
# and nothing else.  Table 2-2 documents the TCB's LAYOUT, not the loader's
# output; the remaining fields are the supervisor's to fill.  The loader's
# only other TCB duty is to RESERVE the space, which is what TCB_WORDS and
# TCB_MIN_WORDS above are for.
#
# KERNEL.S's INSERT explains why the links are the two that matter: it
# refuses to queue a TCB whose RLINK does not point at itself
# ("IF NEW DOESN'T POINT TO SELF (UNLINKED) THEN ERROR"), so the link words
# are the one part of a TCB that must be correct before the supervisor runs.


def write_hasi(linker, filename, lmid=1, mode='ADC', entries=None):
    """Host FORTRAN interface routines for host-callable FPS-100 entries.

    ADC (auto directed calls) moves parameters and common blocks automatically;
    UDC (user directed calls) omits the parameter marshalling and expects the
    caller to have placed the data and to pass main-data addresses. [M 4.3]
    """
    mode = mode.upper()
    if mode not in ('ADC', 'UDC'):
        raise ValueError("HASI mode must be ADC or UDC")

    wanted = entries or {}
    lines = []
    for name, addr in sorted(wanted.items()):
        mod = linker_module_for(linker, name)
        params = parse_fpb(mod.pb_data) if mod else []
        n = len(params)

        # The SUBROUTINE statement and its continuation, exactly as
        # [M figure 4-3] has them: the name alone on the first line, the
        # parameter list on a continuation, and parameters called "P n".
        lines.append("      SUBROUTINE %s" % name[:6])
        if n:
            args = ",".join("P%3d" % (i + 1) for i in range(n))
            lines.append("     * (%s)" % args)
        # Type by PARDTA's low four bits: 1 integer, 2 real, 3 complex.  An
        # array parameter is dimensioned "(1)" -- SRC1's comment says DEC10
        # requires it -- and in UDC every parameter is an INTEGER address.
        for i, (ptype, dest, size) in enumerate(params):
            word = {1: "INTEGER", 2: "REAL", 3: "COMPLEX"}.get(ptype, "INTEGER")
            if mode == 'UDC':
                word = "INTEGER"
            dim = "(1)" if (size > 0 and mode == 'ADC') else ""
            lines.append("      %s P%3d%s" % (word, i + 1, dim))
        lines.append("      COMMON /APLDCM/ IPAV( 33),NU2,IDLM,NU1,IPPAAD,"
                     "IPPAND,IOVS(33),")
        lines.append("     * LMT(10,3),LMTE")
        # The load module is fetched once, by the host-resident subroutine
        # L<lmid*100+1> that write_host_resident emits.
        lines.append("      IF (IDLM.NE.%3d) CALL L%3d" % (lmid, lmid * 100 + 1))
        if mode == 'ADC':
            # Parameter passing: stage each argument's main-data address in
            # IPAV and move it down.  The IPAV element a call reads must be
            # set BEFORE the call -- its length argument is
            # IPAV(k+1)-IPAV(k).
            lines.append("      IPAV(1)=%5d" % n)
            lines.append("      IPA=IPPAAD")
            if n:
                lines.append("      IPAV(%3d)=IPA" % 2)
            for i, (ptype, dest, size) in enumerate(params):
                k = i + 2
                elem = 2 if ptype == 3 else 1
                lines.append("      IPA=IPA+%5d * %5d" % (1, elem))
                lines.append("      IPAV(%3d)=IPA" % (k + 1))
                lines.append("      CALL APPUT (P%3d,IPAV(%3d),IPAV(%3d)"
                             "-IPAV(%3d),1)" % (i + 1, k, k + 1, k))
        lines.append("      CALL APRUN (%6d,1,1,0,13)" % addr)
        lines.append("      CALL APWD")
        lines.append("      CALL APEXC")
        lines.append("      RETURN")
        lines.append("      END")
    # One BLOCK DATA for the file, initialising /APLDCM/ [M figure 4-3].
    if wanted:
        lines.append("      BLOCK DATA")
        lines.append("      COMMON /APLDCM/ IPAV( 33),NU2,IDLM,NU1,IPPAAD,"
                     "IPPAND,IOVS(33),")
        lines.append("     * LMT(10,3),LMTE")
        lines.append("      DATA NU2,IDLM,NU1,IPPAAD,IOVS(2),LMTE")
        lines.append("     * /0,0,0,0,0,0/")
        lines.append("      END")
    with open(filename, 'w') as f:
        f.write("\n".join(lines) + "\n")
    return len(wanted)


def linker_module_for(linker, name):
    for mod in linker.modules:
        if name in mod.aentries or name in mod.entries:
            return mod
    return None


# ── Load map ────────────────────────────────────────────────────────

def _write_warnings(linker, out, segments):
    """An overlaid job is reported against the ROOT segment's linker, so a
    child's unresolved references would otherwise never be shown and the job
    would look clean while shipping a reference patched to zero."""
    warnings = list(linker.warnings)
    for s in segments or []:
        if s.linker is not None and s.linker is not linker:
            warnings += ["segment %d: %s" % (s.num, w) for w in s.linker.warnings]
    if warnings:
        out.write("\nWARNINGS\n")
        for w in warnings:
            out.write("  %s\n" % w)


def write_map(linker, lm, out, psoff=0, mdoff=0, segments=None):
    out.write("FPS-100 LOAD MAP -- load module %d\n" % lm.lmid)
    out.write("PS offset %d   MD offset %d\n\n" % (psoff, mdoff))
    if segments:
        out.write("OVERLAY SEGMENTS\n")
        out.write("  SEG  TASK  PS ADDR  LENGTH   MD ADDR  PART  NPART\n")
        for s in segments:
            out.write("  %3d  %4d  %7d  %6d  %8d  %4d  %5d\n"
                      % (s.num, s.task_id, s.ps_addr, s.length,
                         s.md_addr, s.first_partition, s.n_partitions))
        out.write("\n")
        for s in segments:
            out.write("SEGMENT %d MODULES\n" % s.num)
            for mod in s.linker.modules:
                out.write("  %-10s %8d %7d\n"
                          % (mod.name[:10], mod.base_addr, len(mod.code)))
        out.write("\n")
        _write_warnings(linker, out, segments)
        return
    out.write("MODULE      PS BASE   WORDS  ENTRIES\n")
    for mod in linker.modules:
        names = ",".join(sorted(set(list(mod.aentries) + list(mod.entries))))
        out.write("%-10s %8d %7d  %s\n"
                  % (mod.name[:10], mod.base_addr, len(mod.code), names))
    out.write("\nENTRY POINTS\n")
    # NO psoff here.  The linker is constructed with origin=psoff, so every
    # address it reports already carries it -- adding it again shifted the
    # whole map by 16, and shifted ABSOLUTE symbols too: !ONE printed as
    # 4113 for a symbol whose value is 4097 and which no origin may move.
    # Same class as the linker bug where a code-less module's symbols were
    # biased by the base address.
    for name, addr in sorted(linker.entry_points.items()):
        out.write("  %-8s %8d\n" % (name, addr))
    out.write("\n%d instructions, %d load module words\n"
              % (len(linker.linked_code), len(lm.words)))
    if getattr(lm, 'data_blocks', None):
        out.write("\nDATA BLOCKS\n")
        for name, addr, length in lm.data_blocks:
            out.write("  %-10s MD %6d  %5d words\n" % (name, addr, length))
    _write_warnings(linker, out, segments)


# ── LOD100 command language ─────────────────────────────────────────

class _Phase(object):
    """One LINK's worth of a session: it answers like a Session for the
    fields build() reads, taking the per-phase ones by value and the rest
    from the session it came from."""

    def __init__(self, sess):
        for f in Session.PHASE_FIELDS:
            setattr(self, f, getattr(sess, f))
        self._sess = sess

    def __getattr__(self, name):
        return getattr(self._sess, name)


class Session:
    """The LOD100 command set [M 2.3].

    Single-level jobs, multi-level (overlaid) jobs, and multitasking jobs are
    all supported.  ISR (interrupt service routine) segments are parsed and
    given an ISRMAP overlay table, but the supervisor-side vector wiring is
    left to APX100."""

    UNSUPPORTED = set()

    def __init__(self):
        self.inputs = []
        self.output = None
        self.host_output = None
        self.hasi_output = None
        self.map_output = None
        self.lmid = 1
        self.mode = 'ADC'
        self.radix = 8
        # PS 0-15 is RESERVED; a job starts at 16.  That is FPS's default,
        # from LOD100's own INIT:
        #     IF (CMPFLG .EQ. 0) PSLOW=16
        #     IF (CMPFLG .NE. 0) PSLOW=0
        # CMPFLG is read in four places and SET IN NONE of the recovered
        # modules, so like the file numbers and the table limits it belongs
        # to the lost mainline and is 0 unless something sets it -- which
        # makes 16 the behaviour, not the exception.  A PSOFF command still
        # overrides it.
        self.psoff = 16
        # MD 0 is reserved: LOD100's INIT sets MDLOW=1 (line 1988), beside
        # the PSLOW=16 that reserves PS 0-15.  DBST=MDLOW and DBBRK=DBST,
        # so the data break starts at 1.
        self.mdoff = 1
        self.ppa = 0
        self.entry = None
        self.libs = []
        self.noload = set()
        self.force = set()
        self.linked = False     # a LINK command was seen [M 2.3.23]
        # [M 2.7.1] a supervisor job LINKs more than once into ONE load
        # module -- "LOAD ... LINK / MODE TASK / TREE / OV / LOAD / LINK" --
        # so each LINK closes a PHASE.  The main-data break carries across;
        # everything a phase collects does not.
        self.phases = []
        # [M 2.3.13] FORCE "does not affect libraries loaded previously", and
        # [M 2.3.14] NOLOAD "has no effect on routines loaded prior to the
        # entry of this command" -- both are ordered and sticky from the point
        # they appear, not properties of the whole job.  Applying the union to
        # every LOAD/LIB puts modules in the wrong overlay segment: a routine
        # FORCEd after segment 1's LIB was still pulled into segment 1.
        self.force_at = []
        self.noload_at = []
        # overlay / task state
        self.roots = []              # OverlaySegment roots from TREE
        self.segments = {}           # overlay number → OverlaySegment
        self.current = None          # segment selected by OVERLAY/OV
        self.tasks = []              # (id, opts) in declaration order
        self.pending_task = None
        self.callable = {}           # entry name → wants APOVLD call
        # THERE IS NO "ISR" COMMAND.  [M 2.3.1]-[M 2.3.25] documents the
        # whole command set and has none, and the recovered COMAND's CMNDS
        # table has no slot for one.  An ISR reaches the loader ONLY as
        # object block 16 -- "16 index ***ISR", [M 3.14] -- which LOAD1
        # label 10000 handles by synthesising a TREE and an OV for it.
        # An "ISR" command was invented here and its list never read.
        self.readyq = False
        self.bufsize = 0

    def number(self, tok):
        return int(tok, self.radix) if self.radix != 10 else int(tok, 10)

    PHASE_FIELDS = ('inputs', 'libs', 'force_at', 'noload_at',
                    'roots', 'segments', 'current', 'tasks', 'pending_task')

    def close_phase(self):
        """Snapshot what this LINK covers, then start collecting afresh.

        A phase owns the modules it loaded and the overlay/task structure it
        declared.  Carried across: the load-module identity and output files,
        the radix and offsets, the sticky FORCE/NOLOAD sets, and -- in
        build() -- the main-data break.
        """
        if not (self.inputs or self.libs or self.roots or self.tasks):
            return
        ph = _Phase(self)
        self.phases.append(ph)
        self.inputs, self.libs = [], []
        self.force_at, self.noload_at = [], []
        self.roots, self.segments, self.current = [], {}, None
        self.tasks, self.pending_task = [], None
        # FORCE is CONSUMED, not permanent.  Its whole mechanism is to
        # insert the name into EXTDTA, the unsatisfied-external table --
        #     6080  IF (SRCST (EXTDTA,1,-1,SYM,6) .NE. 0) GOTO 6050
        #           ID=INSST (EXTDTA,-1,SYM,6)
        # -- and once a load satisfies it, it is gone.  It stays in effect
        # across the LOADs and LIBs of its own phase ([M 2.3.13]: it "does
        # not affect libraries loaded previously"), but a later LINK does
        # not re-force it.  Carrying the set forward made phase 3 re-load
        # phase 2's VCLR, which the recovered LOD100 does not.
        self.force = set()

    def execute(self, text):
        it = iter(text.splitlines())
        for raw in it:
            line = raw.split(';')[0].strip()
            if not line:
                continue
            # Commas separate arguments, but not inside a bracketed RSX UIC
            # such as [327,010]FOO.APO.
            flat, depth = [], 0
            for ch in line:
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth = max(0, depth - 1)
                flat.append(' ' if (ch == ',' and depth == 0) else ch)
            parts = "".join(flat).split()
            cmd, args = parts[0].upper(), parts[1:]
            if cmd in ('TREE', 'T'):
                # structure-spec may be continued on following lines, so
                # accumulate until the parentheses balance.
                spec = " ".join(args)
                while spec.count('(') > spec.count(')'):
                    nxt = next(it, None)
                    if nxt is None:
                        break
                    spec += " " + nxt.split(';')[0].strip()
                self.roots = parse_tree(spec)
                self.segments = {s.num: s for s in walk_segments(self.roots)}
                self.current = None
            elif cmd in ('OVERLAY', 'OV'):
                num = self.number(args[0])
                if num not in self.segments:
                    raise ValueError("OVERLAY %d not declared in TREE" % num)
                self.current = self.segments[num]
                if self.pending_task is not None:
                    self.current.task_id = self.pending_task[0]
            elif cmd == 'TASK':
                tid = self.number(args[0])
                opts = {'minimal': False, 'priority': 100,
                        'front': False, 'slaved': False}
                for a in args[1:]:
                    u = a.upper()
                    if u == '/M':
                        opts['minimal'] = True
                    elif u == '/I':
                        opts['front'] = True
                    elif u == '/S':
                        opts['slaved'] = True
                    else:
                        # Priority is decimal 1-255 [ASM100 M 3.4.1], not
                        # subject to the RADIX command -- self.number() would
                        # read 200 as octal and yield 128.
                        opts['priority'] = int(a.lstrip('/'))
                # [M 2.3.7] TASK "designates the next object module and the
                # object modules which follow it to be loaded as a supervisor
                # task".  When it comes AFTER an OVERLAY those modules go into
                # the segment already current, so that segment belongs to the
                # task -- the recovered LOD100's overlay table entry for a
                # "OV 1 / TASK 5" job carries task id 5.  pending_task still
                # covers the other order, TASK before OV.
                if self.current is not None:
                    self.current.task_id = tid
                self.pending_task = (tid, opts)
                self.tasks.append((tid, opts))
            elif cmd == 'PRI':
                if not self.tasks:
                    raise ValueError("PRI with no preceding TASK")
                tid, opts = self.tasks[-1]
                for a in args:
                    u = a.upper()
                    if u == '/I':
                        opts['front'] = True
                    elif u == '/S':
                        opts['slaved'] = True
                    else:
                        opts['priority'] = int(a)   # decimal, see TASK above
            elif cmd in ('CALL', 'C'):
                # entry names, each optionally followed by '/' meaning the
                # HASI routine should contain an APOVLD call [M 2.3.10]
                joined = " ".join(args)
                for tok in joined.replace('/', ' / ').split():
                    if tok == '/':
                        if self.callable:
                            self.callable[list(self.callable)[-1]] = True
                    else:
                        self.callable[tok.upper()] = False

            elif cmd in ('MARK', 'PURGE'):
                # MARK records the loader state; PURGE restores it.  With a
                # one-pass load these only affect which externals stay
                # outstanding, which we already scope per segment.
                pass
            elif cmd == 'INPUT':
                self.inputs.extend(args)
            elif cmd in ('OUTPUT', 'O'):
                # OUTPUT </size> hasifile lmfile-a </D> <lmfile-b/D>
                # [M 2.3.2].  The FIRST file named is the HASI file and the
                # SECOND is the load module -- "OUTPUT HASI LMOD1" writes
                # HASIs to HASI and a host-resident load module to LMOD1.
                # /D on a load module name selects the disk-resident binary
                # form, the only one SIM100/DBG100 can use; without it the
                # host-resident FORTRAN form is produced, which is the
                # default.  A leading /size sets the run-time transfer
                # buffer size and must be a multiple of eight.
                rest = list(args)
                if rest and rest[0].startswith('/') and rest[0][1:].isdigit():
                    n = int(rest.pop(0)[1:])
                    self.bufsize = n - (n % 8)
                if rest:
                    self.hasi_output = rest.pop(0)
                for a in rest:
                    if a.upper().endswith('/D'):
                        self.output = a[:-2]
                    else:
                        self.host_output = a
            elif cmd == 'LMID':
                self.lmid = self.number(args[0])
            elif cmd == 'MODE':
                self.mode = args[0].upper()
            elif cmd == 'RADIX':
                self.radix = int(args[0])
            elif cmd == 'PSOFF':
                self.psoff = self.number(args[0])
            elif cmd == 'MDOFF':
                self.mdoff = self.number(args[0])
            elif cmd == 'PPA':
                self.ppa = self.number(args[0])
            elif cmd in ('LIB', 'LOAD', 'L'):
                # Inside an OVERLAY the modules belong to that segment;
                # otherwise they form the flat single-level job.
                target = self.current.inputs if self.current is not None \
                    else (self.libs if cmd == 'LIB' else self.inputs)
                target.extend(args)
                snapf, snapn = frozenset(self.force), frozenset(self.noload)
                owner = self.current if self.current is not None else self
                for _ in args:
                    owner.force_at.append(snapf)
                    owner.noload_at.append(snapn)
                # LIB gets as many passes as it needs, LOAD exactly one
                # [M 2.3.11/2.3.12], and that distinction has to survive
                # inside an OVERLAY too -- a segment's inputs alone cannot
                # say which command brought them in.
                if cmd == 'LIB' and self.current is not None:
                    self.current.libs.extend(args)
            elif cmd == 'NOLOAD':
                self.noload.update(a.upper() for a in args)
            elif cmd == 'FORCE':
                self.force.update(a.upper() for a in args)
            elif cmd == 'MAP':
                self.map_output = args[0] if args else '-'
            elif cmd in ('MMAX', 'PMAX', 'INIT'):
                pass                    # accepted, no effect on a flat load
            elif cmd in ('LINK', 'LI'):
                # [M 2.3.23] "This command causes object code to be linked,
                # relocated, and written to the load module.  Space is also
                # allocated for the TCB (if tasks are loaded), the overlay
                # map, and any local data blocks..."  It takes NO argument --
                # this was setting the entry point from args[0], which is a
                # different command entirely.  Every documented load sequence
                # ends with it (2.7.1, 2.7.2), and EXIT implies it, which is
                # why jobs without it still produce a load module here and on
                # the real machine.  "Object modules cannot be loaded after
                # this command is entered unless task mode has been
                # specified" -- not yet enforced; a job that does so would be
                # accepted where LOD100 would reject it.
                self.linked = True
                self.close_phase()
            elif cmd == 'EXIT':
                # [M 2.3.25] EXIT closes files and returns to the operating
                # system; it does NOT link.  LINK is what writes the load
                # module [M 2.3.23], and both documented sequences end
                # "LINK" then "EXIT" (2.4 single-level, 2.5 multi-level).
                # The recovered mainline used to link here too, so a job
                # with an explicit LINK wrote the module twice.
                if not self.linked:
                    print("lod100: warning -- no LINK command; the real "
                          "LOD100 would write no load module", file=sys.stderr)
                break
            else:
                raise ValueError("unknown LOD100 command: %s" % cmd)


# ── Driver ──────────────────────────────────────────────────────────

def mod_words(linker, base, start, count):
    """The linked words of one ***CODE block.

    `linked_code` is the whole job laid out at its final addresses, and a
    module sits at `base_addr`, so a block that begins `start` words into
    the module starts at `base_addr + start` in that array.
    """
    off = base - linker.origin + start
    return linker.linked_code[off:off + count]


def _names(mod):
    """Every name this module defines: its title and all its entry points."""
    n = {mod.name.upper()}
    n.update(k.upper() for k in mod.entries)
    n.update(k.upper() for k in mod.aentries)
    return n


def _load(paths, origin, noload=(), force=(), libs=(), inherited=None,
          inherited_types=None, force_at=None, noload_at=None):
    """Link the modules a real LOD100 would load, in its order.

    A module that did NOT come from a library is loaded unconditionally.
    A LIBRARY MEMBER is loaded only if it satisfies an outstanding
    external reference, or was named in a FORCE command -- Loader 2.3.11
    for LOAD, 2.3.12 for LIB, and LOD100.FTN's LOAD1 label 5500, which
    sets LIBFLG=1 on the library start block and routes every subsequent
    module through SKPSUB.

    The two commands differ only in how many passes they get: LOAD is
    "a one-pass load" and "a library may have to be loaded more than once
    to ensure that all the proper externals are satisfied", while LIB
    "causes as many load passes to occur on the library as are necessary".
    `libs` names the paths that arrived via LIB.

    Loading everything regardless -- which is what this did, and what the
    FORTRAN reconstruction did before it was replaced by the recovered
    LOAD1 -- makes the two implementations agree with each other and with
    neither the manual nor FPS.
    """
    noload = {n.upper() for n in noload}
    force = {n.upper() for n in force}
    libset = {str(p) for p in libs}

    inherited = dict(inherited or {})
    linker = Linker(origin=origin, inherited=inherited,
                    inherited_types=inherited_types)
    # A name an ancestor segment already defines is satisfied, so a library
    # member must not be pulled into the child a second time.
    defined, taken = {n.upper() for n in inherited}, []
    # FORCE is not a separate concept: it FABRICATES AN EXTERNAL
    # REFERENCE.  LOD100's FORCE clears the no-load bit on any matching
    # ENTDTA entry and then does
    #     IF (SRCST (EXTDTA,1,-1,SYM,6) .NE. 0) GOTO 6050
    #     ID=INSST (EXTDTA,-1,SYM,6)
    # -- insert the name into EXTDTA, the unsatisfied-external table, if
    # it is not already there.  Selection then picks it up through the
    # ordinary reference test, which is why the manual can say FORCE
    # loads a routine "if and when" it is encountered.
    wanted = set() if force_at else set(force)

    def take(mod):
        taken.append(mod)
        linker.add_modules([mod])
        defined.update(_names(mod))
        wanted.update(e.upper() for e in mod.externs)

    for ipath, path in enumerate(paths):
        # [M 2.3.13/2.3.14] FORCE and NOLOAD take effect from where they
        # appear and do not reach back to libraries already loaded, so each
        # input is loaded under the state in force when IT was named.
        if force_at:
            wanted.update(n.upper() for n in force_at[ipath])
        skip = ({n.upper() for n in noload_at[ipath]} if noload_at else noload)
        # stop_at_leb=False: LOAD1 label 5600 reads on past a library end
        # block, which is what lets a concatenated APLIB work at all.
        mods = [m for m in parse_apo(path, stop_at_leb=False)
                if m.name.upper() not in skip]
        pending = [m for m in mods if m.from_library]
        for mod in mods:
            if not mod.from_library:
                take(mod)
        # One pass for LOAD, repeat to a fixed point for LIB.
        while True:
            progress = False
            for mod in list(pending):
                # Selection is by ENTRY POINT, not by module title, and
                # that goes for FORCE too.  LOAD1 tests each entry name as
                # it reads the entry records:
                #     IF (SRCST (EXTDTA,1,-1,SYM,6) .NE. 0) LIBFG2=1
                # EXTDTA being the unsatisfied-external table, and FORCE
                # puts its names into ENTDTA, the ENTRY table.  DGNLIB
                # proves it: SLFCHK is the one module whose title is not
                # an entry (its entries are FCHK and FGRN), and it is
                # exactly the one the hybrid does NOT load when all
                # eleven titles are FORCEd.
                ents = {k.upper() for k in mod.entries}
                ents.update(k.upper() for k in mod.aentries)
                if not (ents & (wanted - defined)):
                    continue
                pending.remove(mod)
                take(mod)
                progress = True
            if not progress or str(path) not in libset:
                break

    linker.link()
    return linker


MD_LIMIT = 65534


def finish_tail(lm, data_blocks, brk):
    """FINISH's output, emitted once at EXIT.

        DO 300 I=1,OVPPTR
          CALL WRTLM(0,0,4,OVPDTA(I,1)+6,0,1,...)   patch each map entry
          CALL WRTLM(1,0,DBBRK+J-1,0,PCNT,...)
        CALL WRTLM (0,1,1,0,0,...) / CALL WRTLM (1,4,PSPMAX,DBBRK,...)
        DO 400 I=1,TSKPTR
          CALL WRTLM(0,0,4,TSKDTA(I,8),0,1,...)     the ready-queue ring
    """
    for entry in getattr(lm, 'ovt_entries', []):
        lm.add_code_image_words([brk, 1], addr=entry + 6)
    if getattr(lm, 'ovt_entries', None):
        lm.add_data_block([(VALTYP_TRIPLE, PSPMAX, brk, 0)])
    # TWO ORDERS ARE IN PLAY HERE AND THEY ARE NOT THE SAME ONE.
    #
    # FINISH emits the blocks in TABLE order -- "DO 400 I=1,TSKPTR" walks
    # TSKDTA as declared -- while the LINKS come from TSKLNK's sort, which it
    # leaves behind in columns 6 and 7 as neighbour INDICES.  So the ring is
    # priority-ordered but the records appear in declaration order.  Sorting
    # the records themselves put the two task blocks the wrong way round
    # against the 11/44 while every link word still matched, which is exactly
    # what an over-applied fix looks like.
    #
    # TSKLNK's key is the priority, wrapped once above 255, plus 256 for /I --
    # so an /I task outranks every ordinary one whatever its own priority --
    # sorted descending, ties keeping table order ("IF (PI .GE. PJ) GO TO 210"
    # does not swap).  [M 2.10] states the same ordering independently: RLINK
    # is "the next lower priority task", LLINK "the next higher", and /I tasks
    # go "ahead of the highest priority task, regardless of their own
    # priorities".
    tasks = list(getattr(lm, 'task_tcbs', []))
    head = db_addr_of(getattr(lm, 'data_blocks', []), 'READYQ')
    if head is None or not tasks:
        return

    def _key(k):
        _addr, pri, front = tasks[k]
        if pri > 255:
            pri -= 255
        return pri + (256 if front else 0)

    # Entry 0 is the queue header, as TSKDTA row 1 is; the sorted tasks
    # follow it round the ring.
    order = [0] + [1 + k for k in
                   sorted(range(len(tasks)), key=lambda k: -_key(k))]
    addrs = [head] + [t[0] for t in tasks]
    nxt = {}
    prv = {}
    for n, slot in enumerate(order):
        nxt[slot] = order[(n + 1) % len(order)]
        prv[slot] = order[(n - 1) % len(order)]
    for slot, addr in enumerate(addrs):
        lm.add_code_image_words([addrs[nxt[slot]], addrs[prv[slot]]],
                                addr=addr)


def build(inputs, lmid=1, psoff=0, mdoff=0, ppa=0, entry=None, noload=(),
          sess=None):
    """Produce (linker, load_module, segments), running each LINK in turn.

    A session with more than one LINK writes several modules into ONE output
    file, the main-data break carrying from each to the next -- that is how
    [M 2.7.1]'s supervisor sequence puts the supervisor and its tasks in one
    load module.  Each phase is built by _build_phase; a session with a
    single LINK, which is every job here until now, is just the one call.
    """
    phases = list(getattr(sess, 'phases', []) or [])
    if sess is not None:
        sess.close_phase()                 # anything after the last LINK
        phases = list(sess.phases)
    if not phases:
        return _build_phase(inputs, lmid, psoff, mdoff, ppa, entry, noload,
                            sess, None, None)
    lm = LoadModule(lmid)
    md = mdoff
    last = (None, lm, [])
    for ph in phases:
        last = _build_phase(inputs, lmid, psoff, md, ppa, entry, noload,
                            ph, lm, None)
        md = lm.md_break
    finish_tail(lm, getattr(lm, 'data_blocks', []), md)
    return last


def _build_phase(inputs, lmid=1, psoff=0, mdoff=0, ppa=0, entry=None,
                 noload=(), sess=None, lm=None, _unused=None):
    """Produce (linker, load_module, segments).

    Without a TREE this is a flat single-level job: all code goes straight to
    program source memory.  With a TREE each overlay segment is linked at its
    own PS origin but *loaded into main data memory*, because the supervisor
    copies segments from MD into PS at run time via APOVLD [M 2.8].
    """
    sess = sess or Session()
    # A phase appends to the caller's module when there is one, so several
    # LINKs share a single output file.
    lm = lm if lm is not None else LoadModule(lmid)

    md_used = 0
    flat_blocks = []
    if not sess.roots:
        linker = _load(inputs, psoff, noload,
                       force=getattr(sess, 'force', ()),
                       libs=getattr(sess, 'libs', ()),
                       force_at=getattr(sess, 'force_at', None),
                       noload_at=getattr(sess, 'noload_at', None))
        # ONE load-module code block per ***CODE block, at that block's own
        # address.  LOD100 does not concatenate: LINKUP reads a code header
        # off the scratch file and calls WRTLM for it,
        #     IF (LNKLVL .EQ. 0) CALL WRTLM (0,0,RECCNT*PACK,VAL,...)
        # so a module with two ***CODE blocks yields two -- DGNLIB's APFET
        # is exactly that, "0 40 0" then "0 26 40".  Emitting one block for
        # the whole job produces a different file even when every
        # instruction in it is right.
        for mod in linker.modules:
            if not mod.code:
                continue
            base = mod.base_addr
            for start, count, loc in mod.code_blocks:
                if count <= 0:
                    continue
                lm.add_code_ps(mod_words(linker, base, start, count),
                               addr=base + loc)
        # The PPA fields are an ADDRESS and a SIZE, and with no PPA command
        # the size is ALL REMAINING MAIN DATA.  ENDLNK:
        #     IVAL(1)=DBBRK
        #     IF (PPASZ .EQ. -1) PPASZ=ISUB16 (PGINFO(DBPG,1),DBBRK)
        #     CALL WRTLM (0,2,IVAL(1),PPASZ,LMID,...)
        # DBBRK is the main data break, which starts at MDLOW -- and INIT
        # sets MDLOW=1, beside its PSLOW=16, so MD 0 is reserved just as
        # PS 0-15 is.  The MD limit is PGINFO(1,1), 65534.
        # Named data blocks are allocated at the main-data break during
        # loading, exactly as in the overlaid path below.
        db_md = mdoff + md_used
        dbib_mods = []
        for mod in linker.modules:
            addrs = {}
            for n, (name, dbmod, length, local, items) in enumerate(mod.dbdb, 1):
                if length > 0:
                    flat_blocks.append((name, db_md, length))
                    addrs[n] = db_md          # dbid is 1-based within the module
                    db_md += length
            if addrs and mod.dbib:
                dbib_mods.append((mod, addrs))
        md_used = db_md - mdoff
        emit_dbib(lm, dbib_mods, None)
        ppa_addr = ppa or (mdoff + md_used)
        # PPASZ IS COMPUTED ONCE AND STICKS.  ENDLNK guards it --
        #     IF (PPASZ .EQ. -1) PPASZ=ISUB16 (PGINFO(DBPG,1),DBBRK)
        # -- so a second LINK reports the size worked out at the FIRST, not
        # one derived from its own break.
        ppa_size = getattr(lm, 'ppa_size', None)
        if ppa_size is None:
            ppa_size = (MD_LIMIT - ppa_addr) & 0xFFFF
            lm.ppa_size = ppa_size
        lm.add_info(ppa_addr=ppa_addr, ppa_end=ppa_size)
        lm.end()
        lm.data_blocks = getattr(lm, 'data_blocks', []) + flat_blocks
        lm.md_break = ppa_addr
        return linker, lm, []

    segments = walk_segments(sess.roots)

    # Pass 1: link each segment at a provisional origin so its length is
    # known, then re-link once the tree layout is settled.  Lengths do not
    # depend on the origin, so one relink is enough.
    def _ancestor_symbols(seg):
        """Every symbol defined by seg's ancestor chain, nearest first.

        [M 1.7.1] a segment is co-resident with its whole branch back to
        the root, so it may reference what those segments define -- and
        only those; a sibling branch shares the same program store and
        must stay invisible.
        """
        syms, types, chain = {}, {}, []
        p = seg.parent
        while p is not None:
            chain.append(p)
            p = p.parent
        for anc in reversed(chain):          # root first, nearest wins
            if getattr(anc, 'linker', None) is None:
                continue
            for name, (_i, _o, addr) in anc.linker.symbol_table.items():
                syms[name] = addr
            syms.update(anc.linker.entry_points)
            types.update(anc.linker.symbol_types)
        return syms, types

    for seg in segments:
        _anc = _ancestor_symbols(seg)
        seg.linker = _load(seg.inputs or inputs, 0, noload,
                           force=sess.force, libs=seg.libs,
                           inherited=_anc[0], inherited_types=_anc[1],
                           force_at=seg.force_at or None,
                           noload_at=seg.noload_at or None)
        seg.length = len(seg.linker.linked_code)
    allocate_overlays(sess.roots, psoff)
    for seg in segments:
        _anc = _ancestor_symbols(seg)
        seg.linker = _load(seg.inputs or inputs, seg.ps_addr, noload,
                           force=sess.force, libs=seg.libs,
                           inherited=_anc[0], inherited_types=_anc[1],
                           force_at=seg.force_at or None,
                           noload_at=seg.noload_at or None)
        seg.length = len(seg.linker.linked_code)

    # Lay out main data: segment images, then the overlay table, then the
    # PS partition table, then one TCB per task.
    # NAMED DATA BLOCKS COME FIRST, at the main-data break, in load order.
    # LOAD1 label 6000 places each at DBBRK as it reads the ***DBDB header
    # and label 3930 advances the break by the block's length, so they are
    # allocated during LOADING -- before any segment image is placed.  The
    # task load module the recovered LOD100 wrote bears that out: the
    # supervisor's blocks occupy main data from the break upward and the
    # task's segment images start after them, at 694.
    # TCBs FIRST.  TASKY allocates a task's TCB when the TASK command is
    # processed -- [M 2.9] "for each task the user defines, LOD100 creates a
    # task communication block, a common block named TCBnnn" -- and in every
    # documented sequence TASK precedes the segment's LOADs, so the TCB sits
    # below the data blocks.  The recovered LOD100 bears it out: allocating
    # it moved the whole module up by exactly 150 words, segment images from
    # MD 694 to 844, and put the task's queue links at MD 1.
    md = mdoff
    tcb_addrs = {}
    for tid, opts in sess.tasks:
        tcb_addrs[tid] = md
        md += TCB_MIN_WORDS if opts.get('minimal') else TCB_WORDS
    data_blocks = []                 # (name, addr, length)
    seen_db = {}
    dbib_mods = []
    for seg in segments:
        for mod in seg.linker.modules:
            addrs = {}
            for n, (name, dbmod, length, local, items) in enumerate(mod.dbdb, 1):
                key = "%s.%s" % (mod.name.strip(), name) if local else name
                if length <= 0:
                    continue
                if key in seen_db:
                    addrs[n] = seen_db[key][0]
                    continue
                seen_db[key] = (md, length)
                data_blocks.append((key, md, length))
                addrs[n] = md
                md += length
            if addrs and mod.dbib:
                dbib_mods.append((mod, addrs))
    emit_dbib(lm, dbib_mods, None)
    for seg in segments:
        seg.md_addr = md
        md += seg.length * MD_WORDS_PER_INSTR
    ovmesz = OVT_ENTRY_WORDS if sess.tasks else OVT_ENTRY_WORDS_FLAT
    ovt_addr = md
    md += ovmesz * len(segments)
    # The PS partition table belongs to the supervisor/task environment
    # [M 2.8]; LINKS allocates it only under TASKFL, alongside the overlay
    # entry's task-mode fields.  Emitting it for a plain overlaid job added a
    # block the recovered LOD100 does not write and pushed the PPA past the
    # data break.
    # The PS partition table is NOT pre-allocated here: FINISH places it at
    # the data break after the info record and advances the break by PSPMAX
    # itself, so reserving space now put the PPA one word too high.
    part_bounds = compute_partitions(segments) if sess.tasks else []
    part_addr = md

    # Emit: each segment image into MD, then the tables.
    for seg in segments:
        # ONE MD BLOCK PER ***CODE BLOCK, at its own address -- the same rule
        # the PS path follows, and the recovered LOD100 does it here too: the
        # task module holds 40 host words at MD 694, 32 at 714 and 108 at 730,
        # which is VCLR, SPUFLT and RESLVE separately, not one image of 180.
        # A PS instruction occupies TWO MD words, so a module at PS offset k
        # from the segment origin sits at seg.md_addr + 2k.
        for mod in seg.linker.modules:
            if not mod.code:
                continue
            base = mod.base_addr
            for start, count, loc in mod.code_blocks:
                if count <= 0:
                    continue
                off = (base + loc - seg.ps_addr) * MD_WORDS_PER_INSTR
                lm.add_code_image(mod_words(seg.linker, base, start, count),
                                  addr=seg.md_addr + off)
    lm.add_code_md(build_overlay_table(segments, part_addr,
                                       task_mode=bool(sess.tasks)),
                   addr=ovt_addr)

    # The PPA is placed at the main-data break once everything else has been
    # allocated, and its size defaults to the rest of main data -- the same
    # rule the flat path already follows, from ENDLNK:
    #     IVAL(1)=DBBRK
    #     IF (PPASZ .EQ. -1) PPASZ=ISUB16 (PGINFO(DBPG,1),DBBRK)
    # This path left both fields at zero unless a PPA command was given.  The
    # recovered LOD100 writes 93 and -95 for the two-segment job (segment
    # images at MD 1 and 55, overlay table at 85, eight MD words, break 93;
    # 65534-93 = 65441, i.e. -95 as a signed 16-bit word).
    ppa_addr = ppa or md
    # PPASZ IS COMPUTED ONCE AND STICKS.  ENDLNK guards it --
    #     IF (PPASZ .EQ. -1) PPASZ=ISUB16 (PGINFO(DBPG,1),DBBRK)
    # -- so a second LINK reports the size worked out at the FIRST, not one
    # derived from its own break.  The two-LINK module says so: its second
    # info record carries -696, which is 65534-694, phase 1's break, while
    # its own break is 942.
    ppa_size = getattr(lm, 'ppa_size', None)
    if ppa_size is None:
        ppa_size = (MD_LIMIT - ppa_addr) & 0xFFFF
        lm.ppa_size = ppa_size
    # IN TASK MODE THE INFO RECORD'S ovlen AND ovaddr ARE ZERO.  LINKS has
    #     IF (OVFLG .EQ. 0) GOTO 6650
    #     IF (TASKFL) GO TO 6650
    # and 6650 is "IV=0 / IV2=0", so a task job reports neither -- the
    # overlay map is reached through the TCB instead.  The task load module
    # the recovered LOD100 wrote confirms it: "2, 792, -696, 1, 0, 0, 0, 0".
    if sess.tasks:
        lm.add_info(ppa_addr=ppa_addr, ppa_end=ppa_size, ovlen=0, ovaddr=0)
    else:
        lm.add_info(ppa_addr=ppa_addr, ppa_end=ppa_size,
                    ovlen=ovmesz * len(segments), ovaddr=ovt_addr)

    # ---- FINISH's tail -----------------------------------------------------
    #
    # FINISH runs ONCE, at EXIT, not per LINK.  The two-task module shows it:
    # phase 2's info is immediately followed by phase 3's code, and the whole
    # tail -- both map patches, the partition record and a THREE-element
    # ready-queue ring -- appears after the last phase.  So each phase only
    # records what the tail will need.
    lm.ovt_entries = getattr(lm, 'ovt_entries', [])
    lm.task_tcbs = getattr(lm, 'task_tcbs', [])
    if sess.tasks:
        for n, seg in enumerate(segments):
            lm.ovt_entries.append(ovt_addr + n * ovmesz)
        for tid, _o in sess.tasks:
            if tcb_addrs.get(tid) is not None:
                lm.task_tcbs.append((tcb_addrs[tid],
                                     _o.get('priority', 100),
                                     bool(_o.get('front', False))))
    brk = ppa_addr
    # NO END BLOCK IN TASK MODE.  FINISH guards it -- "IF (.NOT.TASKFL)
    # CALL WRTLM (0,3,...)" -- so a task job's module simply stops after the
    # ready queue, and the recovered LOD100's is 2,060 words with none.
    if not sess.tasks:
        lm.end()

    lm.data_blocks = getattr(lm, 'data_blocks', []) + data_blocks
    lm.md_break = brk if sess.tasks else ppa_addr
    # Report against the root segment's linker so callers see a symbol table.
    return segments[0].linker, lm, segments


def main():
    p = argparse.ArgumentParser(
        description="FPS-100 loader (LOD100 replacement)")
    p.add_argument('inputs', nargs='*', help='APO object modules')
    p.add_argument('-c', '--commands', help="LOD100 command file ('-' for stdin)")
    p.add_argument('-o', '--output', help='binary load module')
    p.add_argument('-H', '--host', help='host-resident FORTRAN load module')
    p.add_argument('-A', '--hasi', help='HASI interface routines')
    p.add_argument('-m', '--map-file', help='write load map to FILE')
    p.add_argument('-M', '--map', action='store_true', help='print load map')
    p.add_argument('-i', '--lmid', type=int, default=1, help='load module id')
    p.add_argument('-e', '--entry', help='primary entry point')
    p.add_argument('--psoff', type=int, default=0)
    p.add_argument('--mdoff', type=int, default=0)
    p.add_argument('--ppa', type=int, default=0)
    p.add_argument('--mode', default='ADC', choices=['ADC', 'UDC', 'adc', 'udc'])
    args = p.parse_args()

    sess = Session()
    if args.commands:
        text = sys.stdin.read() if args.commands == '-' \
            else open(args.commands).read()
        try:
            sess.execute(text)
        except NotImplementedError as e:
            print("lod100: %s" % e, file=sys.stderr)
            return 2
        except ValueError as e:
            print("lod100: %s" % e, file=sys.stderr)
            return 2

    inputs = list(sess.inputs) + list(sess.libs) + list(args.inputs)
    seg_inputs = [f for s in walk_segments(sess.roots) for f in s.inputs]
    # A LINK moves everything it covered into a phase, so the session's own
    # lists are empty by now for any job that used one.
    for _ph in sess.phases:
        inputs += list(_ph.inputs) + list(_ph.libs)
        seg_inputs += [f for s in walk_segments(_ph.roots) for f in s.inputs]
    if not inputs and not seg_inputs:
        p.error("no input object modules")

    lmid = args.lmid if args.lmid != 1 else sess.lmid
    psoff = args.psoff or sess.psoff
    mdoff = args.mdoff or sess.mdoff
    ppa = args.ppa or sess.ppa
    entry = args.entry or sess.entry
    mode = (args.mode or sess.mode).upper()

    linker, lm, segments = build(inputs, lmid=lmid, psoff=psoff, mdoff=mdoff,
                                 ppa=ppa, entry=entry, noload=sess.noload,
                                 sess=sess)

    out_bin = args.output or sess.output
    out_host = args.host or sess.host_output
    if not out_bin and not out_host:
        out_host = None
        out_bin = None

    if out_bin:
        n = lm.write_binary(out_bin)
        print("lod100: wrote %s (%d words, %d instructions)"
              % (out_bin, n, len(linker.linked_code)), file=sys.stderr)
    if out_host:
        n = lm.write_host_resident(out_host)
        print("lod100: wrote %s (%d subroutine%s)"
              % (out_host, n, "" if n == 1 else "s"), file=sys.stderr)
    if args.hasi or sess.hasi_output:
        path = args.hasi or sess.hasi_output
        # [M 2.3.10] "LOD100 creates a HASI routine for each routine declared
        # with this command" -- the CALL'd entries, not every entry point.
        # LOAD1 agrees: bit 16 of the ENTDTA flags word is what sets FCLFLG
        # and drives SRC1/SRCN, and nothing in an object module sets it.
        if entry:
            wanted = {entry: linker.get_entry_address(entry)}
        else:
            wanted = {}
            for name in sess.callable:
                addr = linker.get_entry_address(name)
                if addr is None:
                    print("lod100: CALL %s -- no such entry point" % name,
                          file=sys.stderr)
                    continue
                wanted[name] = addr
        n = write_hasi(linker, path, lmid=lmid, mode=mode, entries=wanted)
        print("lod100: wrote %s (%d HASI %s routine%s)"
              % (path, n, mode, "" if n == 1 else "s"), file=sys.stderr)

    mapdest = args.map_file or (sess.map_output if sess.map_output != '-' else None)
    if mapdest:
        with open(mapdest, 'w') as f:
            write_map(linker, lm, f, psoff, mdoff, segments)
    elif args.map or sess.map_output == '-':
        write_map(linker, lm, sys.stdout, psoff, mdoff, segments)

    return 0


if __name__ == '__main__':
    sys.exit(main())
