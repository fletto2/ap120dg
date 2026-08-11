#!/usr/bin/env python3
"""Run a routine from a shipped .APO OBJECT through the full link path.

    ./gen_apo_test.py VADD out.simh

gen_hsr_test.py runs microcode taken from the HSR wrappers -- already
linked, with its callees appended.  This runs the other path, the one
LNK100/LOD100 actually consume: the relocatable .APO object, linked
here by lnk100.py, externals resolved, then executed.

VADD.APO is the right vehicle.  It is not a library -- it opens ***LSB
and never emits ***LEB, so "LIB VADD.APO" fails and the install
references it nowhere -- but it is a self-contained BUNDLE: VADD (14
words, including the 2-word FVADD auto-call entry), SPUFLT (8) and
RESLVE (27).  Add SYMLIB for the absolute constants (!ONE, !TWO) and
the closure is complete.

A pass here means the chain

    .APS --ASM100--> .APO --link--> PS --execute--> correct numbers

holds, not just the HSR shortcut.
"""
import re
import struct
import sys
import os

sys.path.insert (0, os.path.dirname (os.path.abspath (__file__)))
from lnk100 import parse_apo, Linker

ROUTINE = sys.argv[1] if len(sys.argv) > 1 else "VADD"
SRC = os.path.join (os.path.dirname (os.path.abspath (__file__)),
                    "..", "software", "fps100sw")

SYMS = {}

LIBS = ("[327,010]BAALIB.APO", "[327,010]UTLLIB.APO",
        "[327,010]APFLIB.APO", "[327,010]SYMLIB.APO")

def link_routine (routine):
    """Link the routine's closure and return (code, entry address).

    VADD has a ready-made bundle in VADD.APO -- the only one FPS shipped --
    and that is the vehicle the original test used.  Every OTHER routine has
    to be pulled out of the real libraries the way LOD100 does it: FORCE the
    name, then LIB each library and let selective loading drag in the
    closure.  That exercises far more of the linker than one bundle can, and
    it is the same widening that found the multiplier defects on the HSR
    path -- testing one routine proves one routine.
    """
    if routine == "VADD":
        mods = []
        for f in ("[327,010]VADD.APO", "[327,010]SYMLIB.APO"):
            mods.extend (parse_apo (os.path.join (SRC, f)))
        ln = Linker (origin=0)
        ln.add_modules (mods)
        ln.link ()
    else:
        from lod100 import _load
        # FPS_LIBS overrides the library set, so the same execution test can
        # be run against the INSTALLED APLIB.LIB -- the library FPS's own
        # APL100.CMD builds -- instead of the tape sources.  That is the only
        # way to show the install produces working microcode rather than
        # merely a plausible-looking library.
        env = os.environ.get ("FPS_LIBS")
        if env:
            paths = env.split (os.pathsep)
        else:
            paths = [os.path.join (SRC, f) for f in LIBS]
        ln = _load (paths, 0, force={routine}, libs=paths)
    for w in ln.warnings:
        print ("  link warning:", w, file=sys.stderr)
    addr = ln.entry_points.get (routine)
    if addr is None:
        addr = ln.symbol_table[routine][2]
    global SYMS
    SYMS = ln.symbol_table
    return ln.linked_code, addr

linked, ENTRY = link_routine (ROUTINE)

# Load only the prefix through SPUFLT.  RESLVE is 27 words and is
# reachable only from the $SUBR auto-call entry (FVADD), which a
# user-directed call never executes -- but every word costs FOUR page-zero
# Nova constants, and page zero is 256 words.  All 49 instructions need
# 196 of them and push the s-pad parameters off the end, which is why the
# first attempt ran with SP=[0 0 0 0 0 0 0] and stored nothing.
# The link itself is over all three modules, so every symbol resolves.
PSLOAD = len (linked)
if "RESLVE" in [m for m in ("RESLVE",)]:
    pass
_resolve_end = None
for _name, (_i, _off, _abs) in sorted (SYMS.items(), key=lambda kv: kv[1][2]):
    if _name == "RESLVE":
        _resolve_end = _abs
if _resolve_end is not None:
    PSLOAD = _resolve_end
linked = linked[:PSLOAD]
print (f"linked {PSLOAD} of instructions loaded, {ROUTINE} entry at PS[{ENTRY}]",
       file=sys.stderr)

DEV_FPS = 0o55
PULSE_N = 0; PULSE_S = 1; PULSE_C = 2; PULSE_P = 3
SKPDN = 2
FN_DEP = 0o001000
FN_START = 0o040000

def dg_io(ac, code, pulse, dev):
    return (0b011 << 13) | (ac << 11) | (code << 8) | (pulse << 6) | dev
def dg_doa(ac, pulse, dev): return dg_io(ac, 2, pulse, dev)
def dg_dob(ac, pulse, dev): return dg_io(ac, 4, pulse, dev)
def dg_skp(test, dev):      return dg_io(0, 7, test, dev)
def dg_lda(ac, mode, disp): return (0b001 << 13) | (ac << 11) | (mode << 8) | (disp & 0xFF)
def dg_jmp(mode, disp):     return (0b000 << 13) | (mode << 8) | (disp & 0xFF)
def dg_halt():              return dg_io(0, 6, 0, 0o77)
def ieee32(f):
    b = struct.pack('>f', f)
    v = struct.unpack('>I', b)[0]
    return (v >> 16) & 0xFFFF, v & 0xFFFF
def fn_dep_ps(word, inc_tma=False):
    inc = 3 if inc_tma else 0
    return FN_DEP | (inc << 6) | (word << 4) | 0o10

hsr_words = []          # unused on this path
NSPADS = 7

code = list (linked)

# Append HALT at PS[20] — the RETURN at PS[11] will pop SRS to here
halt_word = (1 << 60) | (5 << 54)  # SOP=SPEC, SPS=HALT
code.append(halt_word)

# ── S-pad values ────────────────────────────────────────────────────
# VADD expects: SP[0]=A, SP[1]=I, SP[2]=B, SP[3]=J, SP[4]=C, SP[5]=K, SP[6]=N
# ── Per-routine calling convention ──────────────────────────────────
#
# Each routine's s-pad parameters are its own $EQU block in BAASRC.APS.
# They are not uniform: VADD takes seven (A,I,B,J,C,K,N), VSMUL six
# (the second operand is a scalar, not a vector), VMOV five, VCLR three.
# "spads" is the s-pad file as the routine expects it, "vin" the input
# vectors laid out from MD 0, and "cbase" where C starts.

A3 = [1.0, 2.0, 3.0]
B3 = [4.0, 5.0, 6.0]

ROUTINES = {
    #          spads                    vin        cbase  expected
    "VADD":  ([0, 1, 3, 1, 6, 1, 3],   A3 + B3,    6, [a + b for a, b in zip(A3, B3)]),
    "VSUB":  ([0, 1, 3, 1, 6, 1, 3],   A3 + B3,    6, [b - a for a, b in zip(A3, B3)]),
    "VMUL":  ([0, 1, 3, 1, 6, 1, 3],   A3 + B3,    6, [a * b for a, b in zip(A3, B3)]),
    # VSMUL: A,I,B,C,K,N -- B is the ADDRESS of a scalar, here MD 3.
    "VSMUL": ([0, 1, 3, 4, 1, 3],      A3 + [2.0], 4, [a * 2.0 for a in A3]),
    # VMOV: A,I,C,K,N
    "VMOV":  ([0, 1, 3, 1, 3],         A3,         3, list (A3)),
    # VCLR: C,K,N -- no input at all
    "VCLR":  ([0, 1, 3],               [],         0, [0.0, 0.0, 0.0]),
    # VNEG and VSQ take A,I,C,K,N like VMOV -- their own $EQU blocks in
    # BAASRC.APS say so -- with "C = -A" and the FORMULA line
    # "C(MK) = A(MI) * A(MI)".
    "VNEG":  ([0, 1, 3, 1, 3],         A3,         3, [-a for a in A3]),
    "VSQ":   ([0, 1, 3, 1, 3],         A3,         3, [a * a for a in A3]),
    }

if ROUTINE not in ROUTINES:
    raise SystemExit ("no calling convention recorded for %s -- add one to "
                      "ROUTINES from its $EQU block in BAASRC.APS" % ROUTINE)
spad_vals, vec_in, CBASE, test_c = ROUTINES[ROUTINE]

HOST_DATA = 0o600
HOST_RESULT = 0o620

# ── Generate SimH script ───────────────────────────────────────────

out = []
def emit(s): out.append(s)

emit(f"; {ROUTINE} from VADD.APO, linked: {len(linked)} instructions, entry PS[{ENTRY}]")
emit(f"; in={vec_in} -> C={test_c} at MD {CBASE}")
emit("set cpu 32K")
emit("set fps enabled")
emit("set fpsdma enabled")
emit("set fpsctl5 enabled")
emit("")

pz = {}
pz_next = 0o040

def pz_const(name, val):
    global pz_next
    pz[name] = pz_next
    emit(f"deposit {pz_next:03o} {val:06o}")
    pz_next += 1

pz_const("zero", 0)
pz_const("fn_dep_tma", FN_DEP | 3)     # REGSEL_TMA
pz_const("fn_dep_ps_w0", fn_dep_ps(0))
pz_const("fn_dep_ps_w1", fn_dep_ps(1))
pz_const("fn_dep_ps_w2", fn_dep_ps(2))
pz_const("fn_dep_ps_w3_inc", fn_dep_ps(3, inc_tma=True))
pz_const("fn_dep_psa", FN_DEP | 0)     # REGSEL_PSA
pz_const("fn_start", FN_START)
pz_const("fn_dep_spd", FN_DEP | 1)     # REGSEL_SPD
pz_const("fn_dep_spfn", FN_DEP | 5)    # REGSEL_SPFN
pz_const("dma_ctl_h2a", 0o300)
pz_const("dma_ctl_a2h", 0o340)
pz_const("wc_in", max (2 * len (vec_in), 1))
pz_const("wc_out", 2 * len (test_c))
pz_const("apma_zero", 0)
pz_const("apma_c", CBASE)
pz_const("host_in", HOST_DATA)
pz_const("host_out", HOST_RESULT)
pz_const("entry", ENTRY)

# Microcode words
for i, word in enumerate(code):
    for w in range(4):
        val = (word >> (48 - w*16)) & 0xFFFF
        pz_const(f"mc{i}_w{w}", val)

# S-pad values and addresses
for i, val in enumerate(spad_vals):
    pz_const(f"sp{i}", val)
for i in range(len(spad_vals)):
    pz_const(f"spa{i}", i)

emit("")

# Input/output data
emit(f"; Float data at {HOST_DATA:03o}")
addr = HOST_DATA
for v in vec_in:
    hi, lo = ieee32(v)
    emit(f"deposit {addr:03o} {hi:06o}")
    addr += 1
    emit(f"deposit {addr:03o} {lo:06o}")
    addr += 1
emit(f"; Result area at {HOST_RESULT:03o}")
for i in range(6):
    emit(f"deposit {HOST_RESULT+i:03o} 0")

# Pre-load SRS with return address → HALT at PS[20]
emit("")
# The routine's RETURN pops SRS, so the return address must be the
# index of the HALT appended after the code -- len(hsr_words), which is
# per-routine.  Hardcoding VADD's 20 sent VMOV (16 instructions) past
# its HALT into zeroed program store, where it ran the routine a SECOND
# time with the s-pads left over from the first: C had advanced from 3
# to 5, so the re-run stored at md[5..7] and overwrote C(2).  VADD only
# ever looked right because 20 happened to be its own length.
emit(f"; SRS[0] = {len(linked)} (the appended HALT), SRA = 1")
emit(f"deposit fps SRS[0] {len(linked):06o}")
emit("deposit fps SRA 1")

# ── Nova program ────────────────────────────────────────────────────

pc = 0o1000
prog = []
def inst(opcode):
    global pc
    prog.append((pc, opcode))
    pc += 1

# Phase 1: Load microcode (set TMA=0, then DEP all words)
inst(dg_lda(0, 0, pz["zero"]))
inst(dg_doa(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_dep_tma"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))

for i in range(len(code)):
    for w in range(4):
        inst(dg_lda(0, 0, pz[f"mc{i}_w{w}"]))
        inst(dg_doa(0, PULSE_N, DEV_FPS))
        fn = "fn_dep_ps_w3_inc" if w == 3 else f"fn_dep_ps_w{w}"
        inst(dg_lda(0, 0, pz[fn]))
        inst(dg_doa(0, PULSE_S, DEV_FPS))

# Phase 2: Load s-pad via two-step DEP
for i in range(len(spad_vals)):
    inst(dg_lda(0, 0, pz[f"spa{i}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_spd"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))
    inst(dg_lda(0, 0, pz[f"sp{i}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_spfn"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))

# Phase 3: DMA Host→AP
inst(dg_lda(0, 0, pz["apma_zero"]))
inst(dg_dob(0, PULSE_C, DEV_FPS))
inst(dg_lda(0, 0, pz["host_in"]))
inst(dg_dob(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["wc_in"]))
inst(dg_dob(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["dma_ctl_h2a"]))
inst(dg_doa(0, PULSE_C, DEV_FPS))
inst(dg_dob(0, PULSE_P, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS + 1))
inst(dg_jmp(1, 0xFF))

# Phase 4: START
inst(dg_lda(0, 0, pz["entry"]))
inst(dg_doa(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_dep_psa"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["fn_start"]))
inst(dg_doa(0, PULSE_S, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS))
inst(dg_jmp(1, 0xFF))

# Phase 5: DMA AP→Host
inst(dg_lda(0, 0, pz["apma_c"]))
inst(dg_dob(0, PULSE_C, DEV_FPS))
inst(dg_lda(0, 0, pz["host_out"]))
inst(dg_dob(0, PULSE_S, DEV_FPS))
inst(dg_lda(0, 0, pz["wc_out"]))
inst(dg_dob(0, PULSE_N, DEV_FPS))
inst(dg_lda(0, 0, pz["dma_ctl_a2h"]))
inst(dg_doa(0, PULSE_C, DEV_FPS))
inst(dg_dob(0, PULSE_P, DEV_FPS))
inst(dg_skp(SKPDN, DEV_FPS + 1))
inst(dg_jmp(1, 0xFF))
inst(dg_halt())

emit("")
for addr, opcode in prog:
    emit(f"deposit {addr:03o} {opcode:06o}")

emit("")
emit(f"go {0o1000:03o}")
for i, val in enumerate(test_c):
    hi, lo = ieee32(val)
    emit(f'echo "C[{i}] expected: {hi:06o},{lo:06o} (IEEE {val})"')
emit(f'echo "Actual:"')
emit(f"examine {HOST_RESULT:03o}-{HOST_RESULT+5:03o}")
emit("examine fps PSA")
emit("quit")

script = "\n".join(out) + "\n"
outfile = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test_hsr.simh"
with open(outfile, 'w') as f:
    f.write(script)
print(f"Generated {outfile}: {ROUTINE}, {len(code)} AP instructions, "
      f"{NSPADS} s-pads", file=sys.stderr)
