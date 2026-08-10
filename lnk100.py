#!/usr/bin/env python3
"""lnk100.py — FPS AP-120B / FPS-100 APO Linker

Replacement for the lost LNK100 utility. Reads APO text files (produced by
ASM100 or from the FPS library archives), resolves external symbols, applies
relocations, and outputs a linked load module.

APO text format (all numbers are octal):
  6      ***LSB           Library start block
  3      ***TITLE          Module title follows
  NAME                     Module name
  12 N   ***PB/***FPB      Parameter block (N s-pad params)
  [PB data]
  13 C   ***AENTRY         Abstract entry: C entries follow
  NAME  ADDR LEN SCOPE     Entry definition
  4  C   ***ENTRY           Exported entry: C entries
  NAME  ADDR CNT SCOPE     Entry definition
  0  WC  RC  ***CODE        Code block: WC words, RC relocs
  [4 octal words per line; * prefix = relocation record]
  5  C   ***EXT             External references: C names follow
  NAME                     External symbol name
  1      ***END             Module end
  NAME                     Module name

Relocation record format (lines starting with *):
  * W0 W1 W2 W3  0  TYPE  ARG
  W0-W3: code words (same as normal)
  TYPE: relocation type (5 = external reference)
  ARG: 1-based index into module's EXT table

Usage:
  python3 lnk100.py [-o output.lm] [-s] input1.APO [input2.APO ...]
  -o FILE   Write linked load module (default: stdout as hex dump)
  -s        Print symbol table
  -S FILE   Write SimH deposit script for direct loading
"""

import sys, struct, argparse

# ── APO Parser ──────────────────────────────────────────────────────

class Module:
    def __init__(self, name):
        self.name = name
        self.entries = {}       # name → offset within module
        self.aentries = {}      # name → (offset, length, scope)
        self.code = []          # list of 64-bit words (int)
        self.relocs = []        # list of (word_index, type, ext_index)
        self.externs = []       # list of external symbol names
        self.pb_nspads = 0      # number of s-pad parameters
        self.pb_data = []       # parameter block data
        self.base_addr = 0      # assigned by linker

    def __repr__(self):
        return f"Module({self.name}, {len(self.code)} words, {len(self.externs)} exts)"


def parse_octal(s):
    """Parse an octal string."""
    s = s.strip()
    if not s:
        return 0
    neg = s.startswith('-')
    if neg:
        s = s[1:]
    val = int(s, 8)
    return -val if neg else val


def parse_apo(filename):
    """Parse an APO text file, return list of Modules."""
    modules = []
    current = None
    state = 'idle'
    ext_count = 0
    code_count = 0
    pb_count = 0
    pb_items = 0
    word_idx = 0
    code_start = 0

    # Handle both text and binary-with-text files
    try:
        with open(filename, 'r', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filename}: {e}", file=sys.stderr)
        return []

    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n\r')
        i += 1

        # Strip leading whitespace for field parsing
        stripped = line.strip()
        if not stripped:
            continue

        # Check for record markers
        if '***LSB' in line:
            state = 'idle'
            continue

        if '***TITLE' in line:
            state = 'title'
            continue

        if state == 'title':
            name = stripped
            current = Module(name)
            modules.append(current)
            state = 'module'
            continue

        if '***PB' in line or '***FPB' in line:
            # Parameter block: first field is item count, second is nspads
            fields = stripped.split()
            pb_items = parse_octal(fields[0]) if len(fields) > 0 else 0
            current.pb_nspads = parse_octal(fields[1]) if len(fields) > 1 else 0
            pb_count = 0
            state = 'pb'
            continue

        if state == 'pb':
            # Read PB data lines until we have pb_items worth
            fields = stripped.split()
            for f in fields:
                if f.startswith('*'):
                    break
                try:
                    current.pb_data.append(parse_octal(f))
                except ValueError:
                    pass
                pb_count += 1
            if pb_count >= pb_items:
                state = 'module'
            continue

        if '***AENTRY' in line:
            fields = stripped.split()
            # Format: "13 COUNT ***AENTRY" — fields[0]=type(13), fields[1]=count
            aentry_count = parse_octal(fields[1]) if len(fields) > 1 else 1
            state = 'aentry'
            aentry_remaining = aentry_count
            continue

        if state == 'aentry':
            if '***' in line:
                state = 'module'
                i -= 1
                continue
            fields = stripped.split()
            if len(fields) >= 4:
                name = fields[0]
                try:
                    offset = parse_octal(fields[1])
                    length = parse_octal(fields[2])
                    scope = parse_octal(fields[3])
                    current.aentries[name] = (offset, length, scope)
                except ValueError:
                    pass
            aentry_remaining -= 1
            if aentry_remaining <= 0:
                state = 'module'
            continue

        if '***ENTRY' in line:
            fields = stripped.split()
            # Format: "4 COUNT ***ENTRY" — fields[0]=type(4), fields[1]=count
            entry_count = parse_octal(fields[1]) if len(fields) > 1 else 1
            state = 'entry'
            entry_remaining = entry_count
            continue

        if state == 'entry':
            if '***' in line:
                state = 'module'
                i -= 1  # re-process this line in module state
                entry_remaining = 0
                continue
            fields = stripped.split()
            if len(fields) >= 2:
                name = fields[0]
                try:
                    offset = parse_octal(fields[1])
                    current.entries[name] = offset
                except ValueError:
                    pass
            entry_remaining -= 1
            if entry_remaining <= 0:
                state = 'module'
            continue

        # ***LEB (block type 7) ends the library.  LNK100.FTN stops
        # there -- "IF (BTYPE .EQ. 7) GO TO 800" -- and this parser did
        # not, so two libraries concatenated into one file silently
        # merged.  Honouring it changes nothing for a well-formed .APO,
        # where ***LEB is the last record; it only stops the parser
        # running past the end of a library.  (VADD.APO has no ***LEB
        # at all, which is exactly why it is not a usable library.)
        if '***LEB' in line:
            break

        if '***CODE' in line:
            fields = stripped.split()
            # fields[0]=type(0), fields[1]=word_count, fields[2]=reloc_count
            code_count = parse_octal(fields[1]) if len(fields) > 1 else 0
            # A module may hold SEVERAL ***CODE blocks -- DGNLIB's APFET has
            # two of 32 instructions each, with all its relocations in the
            # second.  The word index must therefore continue across blocks
            # within a module and only restart at ***TITLE, or every
            # relocation in a later block is applied one block too early.
            code_start = len(current.code)
            word_idx = code_start
            state = 'code'
            continue

        if state == 'code':
            if '***' in line:
                # Unexpected marker — back to module state
                state = 'module'
                i -= 1  # re-process this line
                continue

            is_reloc = stripped.startswith('*')
            if is_reloc:
                stripped = stripped[1:].strip()

            fields = stripped.split()
            if len(fields) >= 4:
                # Parse 4 octal 16-bit words
                try:
                    w0 = parse_octal(fields[0])
                    w1 = parse_octal(fields[1])
                    w2 = parse_octal(fields[2])
                    w3 = parse_octal(fields[3])
                except ValueError:
                    continue

                # Pack into 64-bit word
                word64 = ((w0 & 0xFFFF) << 48) | ((w1 & 0xFFFF) << 32) | \
                         ((w2 & 0xFFFF) << 16) | (w3 & 0xFFFF)
                current.code.append(word64)

                if is_reloc and len(fields) >= 7:
                    # Relocation: fields[4]=0, fields[5]=type, fields[6]=arg
                    rtype = parse_octal(fields[5])
                    rarg = parse_octal(fields[6])
                    current.relocs.append((word_idx, rtype, rarg))

                word_idx += 1

            if word_idx - code_start >= code_count:
                state = 'module'
            continue

        if '***EXT' in line:
            fields = stripped.split()
            # Format: "5 COUNT ***EXT" — fields[0]=type(5), fields[1]=count
            ext_count = parse_octal(fields[1]) if len(fields) > 1 else 0
            state = 'ext'
            continue

        if state == 'ext':
            if '***' in line:
                state = 'module'
                i -= 1  # re-process this line
                continue
            name = stripped
            if name:
                current.externs.append(name)
                ext_count -= 1
            if ext_count <= 0:
                state = 'module'
            continue

        if '***END' in line:
            state = 'end_name'
            continue

        if state == 'end_name':
            # Module name after END marker — just skip
            state = 'idle'
            continue

    return modules


# ── Linker ──────────────────────────────────────────────────────────

class Linker:
    def __init__(self, origin=0):
        self.origin = origin    # first PS address to allocate (overlay base)
        self.modules = []
        self.symbol_table = {}  # name → (module_index, offset, abs_addr)
        self.linked_code = []   # final list of 64-bit words
        self.entry_points = {}  # name → absolute PS address
        self.warnings = []

    def add_modules(self, modules):
        """Add parsed modules to the linker."""
        for mod in modules:
            self.modules.append(mod)

    def link(self):
        """Resolve symbols and produce linked output."""
        # Phase 1: Assign base addresses (sequential in PS from the origin)
        #
        # A module with NO ***CODE block occupies no program store and its
        # ***ENTRY records carry ABSOLUTE addresses -- that is what SYMLIB
        # is: 66 modules of pure $EQU, e.g.
        #
        #        4      1      ***ENTRY
        #   !DIV    10000      0      0
        #
        # Biasing those by a base address is meaningless, and produced
        # !ONE = 4146 instead of 4097 once any code-bearing module was
        # linked ahead of SYMLIB (4097 + the 49 words of VADD.APO).  The
        # AP then read the wrong table-memory word for its loop counter
        # and VADD stored one element instead of three.
        #
        # This never showed up against LNK100.FTN because both tools bias
        # the same way, and never showed up in the existing tests because
        # they link SYMLIB FIRST, where the bias is zero.
        addr = self.origin
        for mod in self.modules:
            mod.base_addr = addr if mod.code else 0
            addr += len(mod.code)

        # Phase 2: Build symbol table from AENTRY and ENTRY records
        for idx, mod in enumerate(self.modules):
            for name, (offset, length, scope) in mod.aentries.items():
                abs_addr = mod.base_addr + offset
                if name in self.symbol_table:
                    prev = self.symbol_table[name]
                    # Allow duplicate if same address (from library)
                    if prev[2] != abs_addr:
                        self.warnings.append(
                            f"Duplicate symbol '{name}': "
                            f"module {self.modules[prev[0]].name} @ {prev[2]} "
                            f"and {mod.name} @ {abs_addr}")
                self.symbol_table[name] = (idx, offset, abs_addr)

            for name, offset in mod.entries.items():
                abs_addr = mod.base_addr + offset
                if name in self.entry_points and self.entry_points[name] != abs_addr:
                    self.warnings.append(
                        f"Duplicate entry '{name}': {self.entry_points[name]} "
                        f"and {abs_addr} (module {mod.name})")
                self.entry_points[name] = abs_addr
                if name not in self.symbol_table:
                    self.symbol_table[name] = (idx, offset, abs_addr)

        # Phase 3: Resolve external references and apply relocations
        unresolved = []
        for mod in self.modules:
            for word_idx, rtype, rarg in mod.relocs:
                if rtype == 5:  # External reference
                    if rarg < 1 or rarg > len(mod.externs):
                        self.warnings.append(
                            f"Module {mod.name}: bad EXT index {rarg}")
                        continue
                    ext_name = mod.externs[rarg - 1]  # 1-based
                    if ext_name not in self.symbol_table:
                        unresolved.append((mod.name, ext_name))
                        continue

                    _, _, target_addr = self.symbol_table[ext_name]

                    # Apply relocation: patch the code word
                    # The relocation typically patches an address field in the
                    # 64-bit microword. For AP-120B, relocatable references
                    # are typically in the low 16 bits (VALUE field, bits 48-63)
                    # or in the branch displacement field.
                    #
                    # Looking at actual relocatable words like:
                    #   * 11014 0 0 0  0 5 2
                    # The word 11014,0,0,0 = 0x1208000000000000
                    # This encodes a JMP/JSR with target = 0 (to be patched).
                    # The VALUE field (low 16 bits) gets the target address.
                    #
                    # Similarly: * 40177 103000 2000 0  0 5 1
                    # The low 16 bits = 0, patched with target addr.
                    old_word = mod.code[word_idx]

                    # The VALUE field is not always an absolute address.
                    # All 867 relocations in the shipped libraries are
                    # type 5, so the record does not say which it is --
                    # the INSTRUCTION does.  A JMP/JSR carries a mode in
                    # its SPD subfield:
                    #
                    #   0 = absolute from VALUE   2 = TMA
                    #   1 = PC-relative           3 = SWR
                    #
                    # and VADD's "JSR SPUFLT" is mode 1.  The shipped HSR
                    # block proves the convention: it holds VALUE=013 (11)
                    # at PS[1] to reach SPUFLT at PS[12].  Writing the
                    # absolute address there sent the call 3 words past
                    # its target.
                    df  = (old_word >> 63) & 1
                    sop = (old_word >> 60) & 7
                    sps = (old_word >> 54) & 0xF
                    spd = (old_word >> 50) & 0xF
                    is_pcrel_jump = (df == 0 and sop == 1 and sps == 8
                                     and ((spd >> 1) & 3) == 1)
                    if is_pcrel_jump:
                        psa = mod.base_addr + word_idx
                        value = (target_addr - psa) & 0xFFFF
                    else:
                        value = target_addr & 0xFFFF

                    new_word = (old_word & ~0xFFFF) | value
                    mod.code[word_idx] = new_word

        if unresolved:
            for mod_name, ext_name in unresolved:
                self.warnings.append(
                    f"Unresolved: {ext_name} (referenced by {mod_name})")

        # Phase 4: Concatenate all code
        self.linked_code = []
        for mod in self.modules:
            self.linked_code.extend(mod.code)

        return len(unresolved) == 0

    def get_entry_address(self, name):
        """Get the absolute PS address for an entry point."""
        if name in self.entry_points:
            return self.entry_points[name]
        if name in self.symbol_table:
            return self.symbol_table[name][2]
        return None

    def print_map(self, f=sys.stderr):
        """Print linker map."""
        print(f"\n{'='*60}", file=f)
        print(f"LNK100 Link Map — {len(self.linked_code)} total words", file=f)
        print(f"{'='*60}", file=f)

        print(f"\nModules:", file=f)
        for mod in self.modules:
            print(f"  {mod.name:12s}  base={mod.base_addr:04o}  "
                  f"size={len(mod.code):3d}  "
                  f"exts={len(mod.externs)}  "
                  f"relocs={len(mod.relocs)}", file=f)

        print(f"\nEntry Points:", file=f)
        for name, addr in sorted(self.entry_points.items(),
                                  key=lambda x: x[1]):
            print(f"  {name:12s}  = {addr:04o} ({addr})", file=f)

        print(f"\nSymbol Table ({len(self.symbol_table)} symbols):", file=f)
        for name, (midx, off, addr) in sorted(self.symbol_table.items(),
                                               key=lambda x: x[1][2]):
            print(f"  {name:12s}  = {addr:04o}  "
                  f"(module {self.modules[midx].name}, offset {off:04o})",
                  file=f)

        if self.warnings:
            print(f"\nWarnings:", file=f)
            for w in self.warnings:
                print(f"  {w}", file=f)

        print(f"{'='*60}\n", file=f)


# ── Output Formats ──────────────────────────────────────────────────

def write_simh_script(linker, filename, entry_name=None):
    """Write a SimH deposit script that loads linked code into PS."""
    with open(filename, 'w') as f:
        f.write("; Linked AP microcode — generated by lnk100.py\n")
        f.write(f"; {len(linker.linked_code)} instructions\n")
        f.write(f"; Modules: {', '.join(m.name for m in linker.modules)}\n")
        f.write("\n")

        # Write parameter block info for the first module's entry
        if entry_name and entry_name in linker.symbol_table:
            addr = linker.get_entry_address(entry_name)
            f.write(f"; Entry point: {entry_name} = PS[{addr:04o}]\n\n")

        # Deposit code using FN DEP protocol (SimH deposits into page-zero
        # data, then a Nova program loads via DOA/DOAS)
        # For simplicity, write as raw PS deposits using examine/deposit
        # (requires the emulator to support direct PS access)
        #
        # Alternative: generate the Nova program to load via FN DEP.
        # For now, write a helper that sets up TMA and deposits directly.

        f.write("; Load microcode via FN DEP protocol\n")
        f.write("; This script assumes FPS device is enabled and uses\n")
        f.write("; a small Nova program at 0o100 to load PS.\n\n")

        # Page-zero data: FN command values
        f.write("; FN command constants\n")
        f.write("deposit 040 0\n")       # zero
        f.write("deposit 041 001003\n")  # FN_DEP | REGSEL_TMA
        f.write("deposit 042 000410\n")  # FN_DEP | PS(TMA) WORD=0
        f.write("deposit 043 000420\n")  # FN_DEP | PS(TMA) WORD=1
        f.write("deposit 044 000430\n")  # FN_DEP | PS(TMA) WORD=2
        f.write("deposit 045 000470\n")  # FN_DEP | PS(TMA) WORD=3 + INC TMA
        f.write("\n")

        # Deposit all microcode words into page-zero staging area
        # and generate the loader program
        # This is complex, so for now just output the raw 64-bit words
        # as comments for manual verification, plus a binary format.

        f.write("; Raw microcode (for reference):\n")
        for i, word in enumerate(linker.linked_code):
            w0 = (word >> 48) & 0xFFFF
            w1 = (word >> 32) & 0xFFFF
            w2 = (word >> 16) & 0xFFFF
            w3 = word & 0xFFFF
            f.write(f";   PS[{i:04o}]: {w0:06o},{w1:06o},{w2:06o},{w3:06o}\n")

        f.write(f"\n; Total: {len(linker.linked_code)} instructions\n")


def write_e_module(linker, filename):
    """Write the E command load module — manual 860-7441-000 section 4.4.

    Figure 4-3 shows the real format:

                      8.
        16384.  00000.  00000.  00048.
        16452.  00000.  00000.  00048.

    a leading count of program words, then four values per line, DECIMAL,
    zero padded to five digits, each followed by a period, two spaces
    between fields.  Not octal — 16384 is 040000 and 48 is 60.  Figure 4-4
    confirms the count is element one of the array: the A format emits
    "DATA CODE(1) / 8/".

    This file is read by SIM100 and DBG100.
    """
    def field(v):
        return "%05d." % (v & 0xFFFF)

    with open(filename, 'w') as f:
        f.write(" %s\n" % field(len(linker.linked_code)))
        for w in linker.linked_code:
            words = [(w >> 48) & 0xFFFF, (w >> 32) & 0xFFFF,
                     (w >> 16) & 0xFFFF, w & 0xFFFF]
            f.write(" %s\n" % "  ".join(field(x) for x in words))
    print("Wrote %s: %d instructions (E format)"
          % (filename, len(linker.linked_code)), file=sys.stderr)


def write_a_module(linker, filename, entry_name=None):
    """Write the A command load module — section 4.5, figure 4-4.

    Host FORTRAN: the routine's arguments (one per s-pad parameter on the
    first $ENTRY), an SLIST array in COMMON /SPARY/ with the arguments
    equivalenced into it, a CODE array whose first element is the program
    word count, and a CALL APEX(CODE, 0, SLIST, n).
    """
    name = entry_name
    if not name:
        for mod in linker.modules:
            if mod.aentries or mod.entries:
                name = (list(mod.aentries) + list(mod.entries))[0]
                break
    name = (name or "LMOD")[:6]
    nsp = 0
    for mod in linker.modules:
        if name in mod.aentries or name in mod.entries:
            nsp = mod.pb_nspads
            break
    ncode = len(linker.linked_code) * 4 + 1
    with open(filename, 'w') as f:
        args = ",".join("I%d" % (i + 1) for i in range(nsp))
        f.write("C* %s\n" % name)
        f.write("      SUBROUTINE %s(%s)\n" % (name, args) if nsp
                else "      SUBROUTINE %s\n" % name)
        f.write("      INTEGER CODE(%6d)\n" % ncode)
        for i in range(nsp):
            f.write("      INTEGER I%d,J%d\n" % (i + 1, i + 1))
        f.write("      INTEGER SLIST(16)\n")
        f.write("      COMMON /SPARY/SLIST\n")
        for i in range(nsp):
            f.write("      EQUIVALENCE (J%d,SLIST(%d))\n" % (i + 1, i + 1))
        f.write("      DATA CODE(1) /%6d/\n" % len(linker.linked_code))
        vals = []
        for w in linker.linked_code:
            vals += [(w >> 48) & 0xFFFF, (w >> 32) & 0xFFFF,
                     (w >> 16) & 0xFFFF, w & 0xFFFF]
        for i in range(0, len(vals), 4):
            grp = vals[i:i + 4]
            idx = ",".join("CODE(%6d)" % (i + j + 2) for j in range(len(grp)))
            f.write("      DATA %s/\n" % idx)
            f.write("     X %s/\n" % ",".join(":%06o" % v for v in grp))
        for i in range(nsp):
            f.write("      J%d=I%d\n" % (i + 1, i + 1))
        f.write("      CALL APEX(CODE,%6d,SLIST,%6d)\n" % (0, nsp))
        f.write("      RETURN\n      END\n")
    print("Wrote %s: A format, entry %s, %d s-pad args"
          % (filename, name, nsp), file=sys.stderr)


def write_load_module(linker, filename):
    """Write an FSLMLD-format load module.

    NOTE: this is LOD100's output format, not LNK100's.  LNK100's E and A
    commands produce the formats above.  Kept because the SimH tests and
    the DG driver work consume it.

    Array of 16-bit integers processed as 8-word records.  Header is
    [LMBUF(IPTR), COUNT, ADDR, PAGE, DEST, 0, 0, 0] followed by data words.
    FSLMLD computes TTYPE = LMBUF(IPTR) + 1 and dispatches:
      LMBUF=0 -> code/integer values (PS if DEST=0, MD if DEST=1)
      LMBUF=1 -> data block values
      LMBUF=2 -> info record (PPA, LMID)
      LMBUF=3 -> end record
    """
    words = []

    # Code record: load all linked code to PS starting at address 0
    # TYPE-1 = -1 (code to PS), but FSLMLD uses TYPE=TTYPE=LMBUF(IPTR)+1
    # So for TTYPE=1 (integer/code), LMBUF(IPTR) = 0
    code_size = len(linker.linked_code) * 4  # 4 x 16-bit words per instruction

    # Header: [0, count, addr, page+1, dest, 0, 0, 0]
    # For PS: dest=0, addr=0, count = total 16-bit words
    words.extend([0, code_size, 0, 1, 0, 0, 0, 0])

    # Code data: each 64-bit instruction as 4 x 16-bit words
    for instr in linker.linked_code:
        words.append((instr >> 48) & 0xFFFF)
        words.append((instr >> 32) & 0xFFFF)
        words.append((instr >> 16) & 0xFFFF)
        words.append(instr & 0xFFFF)

    # Info record: PPA start, PPA end, LMID
    words.extend([2, 0, 0, 0, 0, 0, 0, 0])  # TYPE-1=2 → info

    # End record: TYPE-1 = 3 → end
    words.extend([3, 0, 0, 0, 0, 0, 0, 0])

    # Write as binary (16-bit little-endian words)
    with open(filename, 'wb') as f:
        for w in words:
            f.write(struct.pack('<H', w & 0xFFFF))

    print(f"Wrote {filename}: {len(words)} words "
          f"({len(linker.linked_code)} instructions)", file=sys.stderr)


def write_c_header(linker, filename, entry_name=None):
    """Write a C header with the linked microcode as an array."""
    with open(filename, 'w') as f:
        f.write("/* Linked AP microcode — generated by lnk100.py */\n")
        f.write(f"/* Modules: {', '.join(m.name for m in linker.modules)} */\n")
        f.write(f"/* {len(linker.linked_code)} instructions */\n\n")
        f.write("#include <stdint.h>\n\n")

        if entry_name:
            addr = linker.get_entry_address(entry_name)
            if addr is not None:
                f.write(f"#define ENTRY_{entry_name.upper()} {addr}\n\n")

        # Entry point defines
        for name, addr in sorted(linker.entry_points.items()):
            cname = name.replace('!', 'C_').upper()
            f.write(f"#define ENTRY_{cname} {addr}  "
                    f"/* {addr:04o} */\n")
        f.write("\n")

        f.write(f"static const uint64_t ap_microcode"
                f"[{len(linker.linked_code)}] = {{\n")
        for i, word in enumerate(linker.linked_code):
            w0 = (word >> 48) & 0xFFFF
            w1 = (word >> 32) & 0xFFFF
            w2 = (word >> 16) & 0xFFFF
            w3 = word & 0xFFFF
            # Find which module this belongs to
            mod_name = ""
            for mod in linker.modules:
                if mod.base_addr <= i < mod.base_addr + len(mod.code):
                    if i == mod.base_addr:
                        mod_name = f"  /* {mod.name} */"
                    break
            f.write(f"    0x{word:016X}ULL,  "
                    f"/* {i:3d}: {w0:06o},{w1:06o},{w2:06o},{w3:06o} */"
                    f"{mod_name}\n")
        f.write("};\n")

    print(f"Wrote {filename}", file=sys.stderr)


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='LNK100 — FPS AP-120B/FPS-100 APO Linker')
    parser.add_argument('inputs', nargs='+', help='APO input files')
    parser.add_argument('-o', '--output', help='Output load module (FSLMLD format)')
    parser.add_argument('-E', '--e-module', help='E command load module (section 4.4)')
    parser.add_argument('-A', '--a-module', help='A command load module (section 4.5)')
    parser.add_argument('-S', '--simh', help='Output SimH deposit script')
    parser.add_argument('-C', '--c-header', help='Output C header with microcode array')
    parser.add_argument('-s', '--symbols', action='store_true',
                        help='Print symbol table / link map')
    parser.add_argument('-e', '--entry', help='Primary entry point name')
    args = parser.parse_args()

    # Parse all input files
    all_modules = []
    for filename in args.inputs:
        modules = parse_apo(filename)
        if not modules:
            print(f"Warning: no modules found in {filename}", file=sys.stderr)
        else:
            print(f"Parsed {filename}: {len(modules)} modules "
                  f"({', '.join(m.name for m in modules)})", file=sys.stderr)
        all_modules.extend(modules)

    if not all_modules:
        print("Error: no modules to link", file=sys.stderr)
        sys.exit(1)

    # Link
    linker = Linker()
    linker.add_modules(all_modules)
    success = linker.link()

    if args.symbols or not success:
        linker.print_map()

    if not success:
        print(f"Link failed: {sum(1 for w in linker.warnings if 'Unresolved' in w)} "
              f"unresolved symbols", file=sys.stderr)
        # Continue anyway — partial output may be useful

    # Output
    if args.output:
        write_load_module(linker, args.output)
    if args.e_module:
        write_e_module(linker, args.e_module)
    if args.a_module:
        write_a_module(linker, args.a_module, args.entry)

    if args.simh:
        write_simh_script(linker, args.simh, args.entry)

    if args.c_header:
        write_c_header(linker, args.c_header, args.entry)

    if not (args.output or args.simh or args.c_header):
        # Default: print summary
        linker.print_map(sys.stdout)

    print(f"\nLinked: {len(linker.linked_code)} instructions, "
          f"{len(linker.symbol_table)} symbols, "
          f"{len(linker.warnings)} warnings", file=sys.stderr)


if __name__ == '__main__':
    main()
