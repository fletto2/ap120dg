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
OVT_ENTRY_WORDS = 8          # [M table 2-1]
TCB_WORDS = 150              # [M table 2-2], through the maximum save area


class OverlaySegment:
    def __init__(self, num, parent=None):
        self.num = num
        self.parent = parent
        self.children = []
        self.inputs = []         # object modules loaded into this segment
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


def build_overlay_table(segments, partition_table_addr):
    """One 8-word main-data entry per segment. [M table 2-1]

    Only the 32 bits the loader can reach (HM+LM) are written; the
    currently-resident bit in word 6 lives in the exponent portion and is
    maintained by the supervisor, so it is left zero.
    """
    words = []
    for s in segments:
        words.extend([
            s.num,                                   # 1 segment number
            s.md_addr,                               # 2 MD address
            s.ps_addr,                               # 3 PS address
            s.length,                                # 4 length in PS words
            s.task_id,                               # 5 task id / TCB address
            0,                                       # 6 residency bits
            partition_table_addr + s.first_partition - 1 if s.first_partition
            else partition_table_addr,               # 7 first partition entry
            s.n_partitions,                          # 8 partitions required
        ])
    return words


def build_tcb(task_id, ovl_ptr, ovl_count, priority=100, minimal=False,
              front=False, slaved=False, ready_queue=False,
              ps_addr=0, md_addr=0, term_addr=0, tcb_addr=0):
    """A task communication block, initialised per [M 2.9] table 2-2."""
    tcb = [0] * TCB_WORDS
    tcb[2] = priority                     # 3  RPRI
    tcb[4] = TCB_WORDS                    # 5  LENGTH
    tcb[6] = task_id                      # 7  ID
    tcb[7] = ovl_ptr                      # 8  OVLPTR
    tcb[8] = ovl_count                    # 9  OVLCNT
    tcb[9] = priority                     # 10 DPRI
    status = 0
    if not minimal:
        status |= 0o004000                # full machine resources
    if slaved:
        status |= 0o010000
    if ready_queue:
        status |= 0o001000
    tcb[10] = status                      # 11 STATUS
    tcb[15] = md_addr                     # 16 TADDR
    # "RCLOCK and LCLOCK are set to the address of RCLOCK" [M 2.9] -- both
    # point at word 13 of this very TCB, so the clock list starts empty.
    tcb[12] = tcb_addr + 12               # 13 RCLOCK
    tcb[13] = tcb_addr + 12               # 14 LCLOCK
    tcb[42] = 0                           # 43 APSTAT2: FP exception disabled
    tcb[47] = 0o55260                     # 48 APSTAT3
    tcb[48] = term_addr                   # 49 SRS(0) termination routine
    tcb[49] = ps_addr                     # 50 SRS(1) task entry
    return tcb


def link_ready_queue(tcbs, tcb_addrs):
    """RLINK/LLINK chain, highest priority first, /I tasks at the front. [M 2.10]"""
    order = sorted(range(len(tcbs)),
                   key=lambda i: (not tcbs[i][1].get('front'),
                                  -tcbs[i][1].get('priority', 100)))
    for pos, idx in enumerate(order):
        nxt = order[(pos + 1) % len(order)]
        prv = order[(pos - 1) % len(order)]
        tcbs[idx][0][0] = tcb_addrs[nxt]      # RLINK
        tcbs[idx][0][1] = tcb_addrs[prv]      # LLINK
    return order


# ── HASI generation ─────────────────────────────────────────────────

def parse_fpb(pb_data):
    """Decode a formal parameter block into (type, dest, ndim) tuples.

    [M 3.11] record = type dest size, followed by one (p-a, p-b) sub-record
    per dimension.  lnk100 flattens the whole block into a word list, so walk
    it with that structure.
    """
    params, i = [], 0
    while i + 2 < len(pb_data) + 1 and i + 3 <= len(pb_data):
        ptype, dest, size = pb_data[i], pb_data[i + 1], pb_data[i + 2]
        i += 3
        i += 2 * size                       # skip dimension sub-records
        if ptype not in (1, 2):
            break                           # not a well-formed record; stop
        params.append((ptype, dest, size))
    return params


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
        args = ["A%d" % (n + 1) for n in range(len(params))]
        arglist = ("(" + ",".join(args) + ")") if args else ""
        lines.append("      SUBROUTINE %s%s" % (name[:6], arglist))
        for n, (ptype, dest, size) in enumerate(params):
            decl = "INTEGER" if ptype == 1 else "REAL"
            lines.append("      %s A%d" % (decl, n + 1))
        lines.append("C     FPS-100 entry %s at PS address %d" % (name, addr))
        lines.append("      CALL APLLI0")
        if mode == 'ADC':
            # Move each input parameter down, run, then retrieve the outputs.
            for n, (ptype, dest, size) in enumerate(params):
                if dest in (1, 3):
                    lines.append("      CALL APPUT(A%d,%d,1,%d)" % (n + 1, n, ptype))
            lines.append("      CALL APRUN(%d,0,1,0,0)" % addr)
            lines.append("      CALL APWAIT")
            for n, (ptype, dest, size) in enumerate(params):
                if dest in (2, 3):
                    lines.append("      CALL APGET(%d,A%d,1,%d)" % (n, n + 1, ptype))
        else:
            lines.append("      CALL APRUN(%d,0,2,0,0)" % addr)
            lines.append("      CALL APWAIT")
        lines.append("      RETURN")
        lines.append("      END")
    with open(filename, 'w') as f:
        f.write("C     HASI %s routines for load module %d\n" % (mode, lmid))
        f.write("C     Generated by lod100.py\n")
        f.write("\n".join(lines) + "\n")
    return len(wanted)


def linker_module_for(linker, name):
    for mod in linker.modules:
        if name in mod.aentries or name in mod.entries:
            return mod
    return None


# ── Load map ────────────────────────────────────────────────────────

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
        return
    out.write("MODULE      PS BASE   WORDS  ENTRIES\n")
    for mod in linker.modules:
        names = ",".join(sorted(set(list(mod.aentries) + list(mod.entries))))
        out.write("%-10s %8d %7d  %s\n"
                  % (mod.name[:10], mod.base_addr + psoff, len(mod.code), names))
    out.write("\nENTRY POINTS\n")
    for name, addr in sorted(linker.entry_points.items()):
        out.write("  %-8s %8d\n" % (name, addr + psoff))
    out.write("\n%d instructions, %d load module words\n"
              % (len(linker.linked_code), len(lm.words)))
    if linker.warnings:
        out.write("\nWARNINGS\n")
        for w in linker.warnings:
            out.write("  %s\n" % w)


# ── LOD100 command language ─────────────────────────────────────────

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
        # overlay / task state
        self.roots = []              # OverlaySegment roots from TREE
        self.segments = {}           # overlay number → OverlaySegment
        self.current = None          # segment selected by OVERLAY/OV
        self.tasks = []              # (id, opts) in declaration order
        self.pending_task = None
        self.callable = {}           # entry name → wants APOVLD call
        self.isr_segments = []       # overlay numbers declared as ISRs
        self.readyq = False
        self.bufsize = 0

    def number(self, tok):
        return int(tok, self.radix) if self.radix != 10 else int(tok, 10)

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
                # TASK designates the modules that FOLLOW it [M 2.3.7], so it
                # must not retag the segment already selected.
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
            elif cmd == 'ISR':
                self.isr_segments.extend(self.number(a) for a in args)
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
            elif cmd == 'NOLOAD':
                self.noload.update(a.upper() for a in args)
            elif cmd == 'FORCE':
                self.force.update(a.upper() for a in args)
            elif cmd == 'MAP':
                self.map_output = args[0] if args else '-'
            elif cmd in ('MMAX', 'PMAX', 'INIT'):
                pass                    # accepted, no effect on a flat load
            elif cmd == 'LINK':
                self.entry = args[0] if args else self.entry
            elif cmd == 'EXIT':
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


def _load(paths, origin, noload=(), force=(), libs=()):
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

    linker = Linker(origin=origin)
    defined, taken = set(), []
    # FORCE is not a separate concept: it FABRICATES AN EXTERNAL
    # REFERENCE.  LOD100's FORCE clears the no-load bit on any matching
    # ENTDTA entry and then does
    #     IF (SRCST (EXTDTA,1,-1,SYM,6) .NE. 0) GOTO 6050
    #     ID=INSST (EXTDTA,-1,SYM,6)
    # -- insert the name into EXTDTA, the unsatisfied-external table, if
    # it is not already there.  Selection then picks it up through the
    # ordinary reference test, which is why the manual can say FORCE
    # loads a routine "if and when" it is encountered.
    wanted = set(force)

    def take(mod):
        taken.append(mod)
        linker.add_modules([mod])
        defined.update(_names(mod))
        wanted.update(e.upper() for e in mod.externs)

    for path in paths:
        mods = [m for m in parse_apo(path) if m.name.upper() not in noload]
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


def build(inputs, lmid=1, psoff=0, mdoff=0, ppa=0, entry=None, noload=(),
          sess=None):
    """Produce (linker, load_module, segments).

    Without a TREE this is a flat single-level job: all code goes straight to
    program source memory.  With a TREE each overlay segment is linked at its
    own PS origin but *loaded into main data memory*, because the supervisor
    copies segments from MD into PS at run time via APOVLD [M 2.8].
    """
    sess = sess or Session()
    lm = LoadModule(lmid)

    md_used = 0
    if not sess.roots:
        linker = _load(inputs, psoff, noload,
                       force=getattr(sess, 'force', ()),
                       libs=getattr(sess, 'libs', ()))
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
        ppa_addr = ppa or (mdoff + md_used)
        ppa_size = (MD_LIMIT - ppa_addr) & 0xFFFF
        lm.add_info(ppa_addr=ppa_addr, ppa_end=ppa_size)
        lm.end()
        return linker, lm, []

    segments = walk_segments(sess.roots)

    # Pass 1: link each segment at a provisional origin so its length is
    # known, then re-link once the tree layout is settled.  Lengths do not
    # depend on the origin, so one relink is enough.
    for seg in segments:
        seg.linker = _load(seg.inputs or inputs, 0, noload)
        seg.length = len(seg.linker.linked_code)
    allocate_overlays(sess.roots, psoff)
    for seg in segments:
        seg.linker = _load(seg.inputs or inputs, seg.ps_addr, noload)
        seg.length = len(seg.linker.linked_code)

    # Lay out main data: segment images, then the overlay table, then the
    # PS partition table, then one TCB per task.
    md = mdoff
    for seg in segments:
        seg.md_addr = md
        md += seg.length * MD_WORDS_PER_INSTR
    ovt_addr = md
    md += OVT_ENTRY_WORDS * len(segments)
    part_bounds = compute_partitions(segments)
    part_addr = md
    md += len(part_bounds)

    tcb_addrs, tcb_blocks = {}, []
    for tid, opts in sess.tasks:
        tcb_addrs[tid] = md
        md += TCB_WORDS
    for tid, opts in sess.tasks:
        owned = [s for s in segments if s.task_id == tid]
        first = owned[0] if owned else None
        tcb = build_tcb(
            tid,
            ovl_ptr=ovt_addr + OVT_ENTRY_WORDS * segments.index(first) if first else 0,
            ovl_count=len(owned),
            priority=opts.get('priority', 100),
            minimal=opts.get('minimal', False),
            front=opts.get('front', False),
            slaved=opts.get('slaved', False),
            ready_queue=sess.readyq,
            ps_addr=first.ps_addr if first else 0,
            md_addr=first.md_addr if first else 0,
            tcb_addr=tcb_addrs[tid])
        tcb_blocks.append((tcb, opts))
    if sess.readyq and tcb_blocks:
        link_ready_queue(tcb_blocks, [tcb_addrs[t] for t, _ in sess.tasks])

    # Emit: each segment image into MD, then the tables.
    for seg in segments:
        lm.add_code_image(seg.linker.linked_code, addr=seg.md_addr)
    lm.add_code_md(build_overlay_table(segments, part_addr), addr=ovt_addr)
    if part_bounds:
        lm.add_code_md([0] * len(part_bounds), addr=part_addr)   # zeroed [M 2.8]
    for (tcb, _), (tid, _o) in zip(tcb_blocks, sess.tasks):
        lm.add_code_md(tcb, addr=tcb_addrs[tid])

    ppa_end = ppa + sum(s.length for s in segments) if ppa else 0
    lm.add_info(ppa_addr=ppa, ppa_end=ppa_end,
                ovlen=OVT_ENTRY_WORDS * len(segments), ovaddr=ovt_addr)
    lm.end()

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
        wanted = ({entry: linker.get_entry_address(entry)}
                  if entry else dict(linker.entry_points))
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
