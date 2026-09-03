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

LIBS = ("[327,010]BAALIB.APO", "[327,010]BABLIB.APO", "[327,010]SIGLIB.APO",
        "[327,010]UTLLIB.APO",
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
            # LINK THE WAY THE INSTALL DOES: one CONCATENATED library, in
            # FPS's own APL100.CMD order, not the nine separate files.
            # `LIB` loops to a fixed point only WITHIN one file, so a
            # reference raised by a later library is never taken back to an
            # earlier one -- SIGLIB's ASPEC references SCJMA in BAALIB, and
            # with separate libraries that reference cannot close: the
            # unrelocated JMP has VALUE 0 and spins on itself forever.
            # refs/APLIB.APO is the concatenation test_lm_refs.py builds in
            # APL100.CMD's order; falling back to the separate files keeps
            # the harness working if it has not been generated yet.
            apl = os.path.join (os.path.dirname (os.path.abspath (__file__)),
                                "refs", "APLIB.APO")
            paths = ([apl] if os.path.exists (apl)
                     else [os.path.join (SRC, f) for f in LIBS])
        ln = _load (paths, 0, force={routine}, libs=paths)
    for w in ln.warnings:
        print ("  link warning:", w, file=sys.stderr)
    addr = ln.entry_points.get (routine)
    if addr is None:
        addr = ln.symbol_table[routine][2]
    global SYMS
    SYMS = ln.symbol_table
    return ln.linked_code, addr

# VDIV1 is VDIV with a different element count -- link the real routine.
LINK_NAME = "VDIV" if ROUTINE in ("VDIV1", "VDIV2", "VDIV3") else "VSQRT" if ROUTINE == "VSQRT2" else "VSIN" if ROUTINE in ("VSIN2", "VSIN3", "VSIN4", "VSIN5") else "VATAN" if ROUTINE == "VATAN2" else "CVMUL" if ROUTINE == "CVMUL2" else "SOLVEQ" if ROUTINE == "SOLVEQ2" else "MATINV" if ROUTINE == "MATINV2" else "EIGRS" if ROUTINE == "EIGRS3" else "CFFT" if ROUTINE in ("CFFT4", "CFFTI") else "HANN" if ROUTINE == "HANN2" else "ASPEC" if ROUTINE == "ASPEC1" else "ACORT" if ROUTINE == "ACORT4" else ROUTINE
linked, ENTRY = link_routine (LINK_NAME)

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
# Truncating at RESLVE drops the resolver stub, which is dead weight for a
# directly-entered routine -- but ONLY when RESLVE is the TAIL of the
# image.  VATAN links RESLVE at PS 16 with ATAN's 46 words and VFCL1's 11
# AFTER it, so the cut removed 101 instructions of genuinely needed code
# and the routine returned zeros.  That looked exactly like broken
# selective loading and cost five refuted hypotheses; the linker was
# right all along (it loads 117 words, no warnings).
if _resolve_end is not None and _resolve_end >= max(
        (_abs for (_i, _off, _abs) in SYMS.values()), default=0):
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
# The number of s-pad parameters is per-routine -- VADD has 7, VMOV 5,
# VCLR 3, VMA NINE -- so this is derived, not fixed.  It was a hardcoded 7
# used ONLY in the progress message while the staging loops over
# len(spad_vals), which made a nine-parameter routine report "7 s-pads"
# and look like a harness limit when the staging was correct all along.
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
    # VCLR -- C IS PRE-LOADED WITH NON-ZERO DATA so the routine must
    # actually clear it.  With no input and a destination in untouched
    # main data (which starts at zero), the expected all-zeros result would
    # be produced by a routine that did NOTHING -- the same
    # "what wrong implementation still passes this?" audit that found
    # VTSMUL's identity multiplier and VSBSBM's constant output.
    # SEEDED WITH 9s so the routine has something to destroy -- expecting
    # zeros in memory that starts zeroed passed a routine that did NOTHING
    # AT ALL, which is what this test did for most of its life.  And the
    # 5.0 at MD 3 is the OVERRUN guard: with the window exactly N, a clear
    # of N+1 elements is invisible.  Both halves are needed.
    "VCLR":  ([0, 1, 3],   [9.0, 9.0, 9.0, 5.0], 0,
              [0.0, 0.0, 0.0, 5.0]),
    # VNEG and VSQ take A,I,C,K,N like VMOV -- their own $EQU blocks in
    # BAASRC.APS say so -- with "C = -A" and the FORMULA line
    # "C(MK) = A(MI) * A(MI)".
    "VNEG":  ([0, 1, 3, 1, 3],         A3,         3, [-a for a in A3]),
    "VSQ":   ([0, 1, 3, 1, 3],         A3,         3, [a * a for a in A3]),
    # VSADD takes A,I,B,C,K,N like VSMUL -- its own $EQU block in
    # BAASRC.APS names them, with B "CONSTANT VECTOR B", i.e. the address
    # of a scalar (here MD 3).
    "VSADD": ([0, 1, 3, 4, 1, 3],      A3 + [2.0], 4, [a + 2.0 for a in A3]),
    # VDIV IS NOT RUNNABLE BY THIS HARNESS, and the source says why.
    # Its s-pads are known -- "S-PAD PARAMETERS / X = 0 / I = 1 / Y = 2 /
    # J = 3 / C = 4 / K = 5 / N = 6" -- and its abstract is
    # "C(M)=Y(M)/X(M)", so the convention below is right.  But the same
    # header block also demands
    #     "DATA PAD INITIALIZATIONS:  DPY=MASK / DPY(1)=1 / DPX(1)=-1"
    # and this harness sets up main data and the s-pads ONLY.  Run as-is
    # the routine never terminates: its Newton iteration starts from
    # uninitialised data pads.  Every routine tested so far is pure
    # add/multiply and needs no such state, which is why the gap did not
    # show until the first DIVIDE was tried.
    #
    # Enabling it means teaching the harness to preload the data pads --
    # worth doing, since VDIV is the only path to the DIVIDER and the
    # !DIV coefficient table, neither of which any test reaches today.
    # VDIV RUNS AND RETURNS now that the microcode is ATTACHed rather than
    # staged through page zero -- the first time the divider has terminated
    # here.  The answers are still wrong: expected 4.0/2.5/2.0, got
    # 8.0/0.0/4.77e-07.  The leading 8.0-for-4.0 is a factor of TWO, the
    # same signature as the multiplier scaling defect already recorded.
    # Left OUT of DEFAULT until it is right; enable it by name to work on
    # it:  python3 test_apo_exec.py VDIV
    "VDIV":  ([0, 1, 3, 1, 6, 1, 3],   A3 + B3,    6, [b / a for a, b in zip(A3, B3)]),
    # SINGLE ELEMENT.  VDIV is software-pipelined in four columns, so N=3
    # exercises the pipeline as well as the reciprocal; N=1 separates them.
    # Same layout -- X at 0, Y at 3, C at 6 -- so only the count changes.
    "VDIV1": ([0, 1, 3, 1, 6, 1, 1],   A3 + B3,    6, [B3[0] / A3[0]]),
    # SECOND DIVIDER CASE, chosen to separate a SCALE error from a BIAS one:
    # the same expected answer as VDIV1 (4.0) but operands two binary orders
    # up, X=2 Y=8.  A fixed-factor error keeps the ratio; an
    # exponent-dependent one does not.  With only one divider test, and one
    # that has never passed, there is no way to tell "closer" from
    # "differently wrong".
    "VDIV2": ([0, 1, 3, 1, 6, 1, 1],   [2.0,0,0, 8.0,0,0], 6, [4.0]),
    # X(2) made DISTINCTIVE, so a main-data read delivering one element late
    # shows up as 9.0 rather than 2.0.
    "VDIV3": ([0, 1, 3, 1, 6, 1, 1],   [1.0,9.0,9.0, 4.0,0,0], 6, [4.0]),
    # VSQRT -- the next routine that reads a COEFFICIENT TABLE, and the
    # first test of the !SQRT run.  Its $EQU block gives A=0 I=1 C=2 K=3
    # N=4, the same five-parameter shape as VMOV, and its FORMULA line is
    # C(M)=SQRT(A(M)).  Perfect squares keep the expected values exact.
    "VSQRT": ([0, 1, 6, 1, 3],  [1.0, 4.0, 9.0],  6,  [1.0, 2.0, 3.0]),
    # MANTISSA-DIVERSE inputs.  VSQRT indexes its coefficient table on the
    # mantissa, and 1.0 and 4.0 share one (0.5, index 0) -- so the default
    # case exercises only two distinct indices out of three values.  2.0,
    # 3.0 and 5.0 give mantissas 0.5, 0.75 and 0.625, three DIFFERENT
    # indices, and exponents 2, 2, 3 -- so parity varies too.
    "VSQRT2": ([0, 1, 6, 1, 3], [2.0, 3.0, 5.0], 6,
               [1.4142135623730951, 1.7320508075688772, 2.23606797749979]),
    # BREADTH.  "One routine proves one routine" is this project's own
    # lesson, and twelve add/multiply routines share most of their path.
    # VABS's $EQU block is A=0 I=1 C=2 K=3 N=4, the VMOV/VNEG shape, and
    # its abstract is "C(MK) = ABS(A(MI))" -- NEGATIVE inputs make it the
    # only routine besides VNEG that exercises the sign path, and unlike
    # VNEG it CONSUMES a negative rather than producing one.
    "VABS":  ([0, 1, 6, 1, 3],  [-1.0, 2.0, -3.0], 6, [1.0, 2.0, 3.0]),
    # NINE s-pad parameters -- wider than anything else here (VADD's seven
    # was the maximum), and a THREE-input routine.  Its $EQU block gives
    # A,I,B,J,C,K,D,L,N and the abstract is "D <= A*B+C COMPONENT-WISE".
    # A at MD 0, B at 3, C at 6, D at 9.
    # VLOG -- the OTHER coefficient-table routine, and the diagnostic that
    # says whether VSQRT's residue is specific to the sqrt table or general
    # to table-driven routines.  $EQU gives A,I,C,K,N (the VMOV shape);
    # FORMULA is "C(MK) = LOG (ABS(A(MI))".  Powers of e keep the expected
    # values exact-ish; the divider tolerance covers the iteration.
    # IT IS LOG BASE 10, and the tape says so: BAASRC's banner is
    # "VLOG = VECTOR LOGARITHM (BASE 10".  A first run against natural-log
    # expectations returned 0, 1, 2 -- which IS log10 of 1, 10, 100, so the
    # routine was right and the test was wrong.  Read the banner, not the
    # mnemonic.
    "VLOG":  ([0, 1, 6, 1, 3],  [1.0, 10.0, 100.0], 6, [0.0, 1.0, 2.0]),
    # VEXP and VSIN complete the transcendentals, both A,I,C,K,N.
    # FORMULA lines: "C(MK) = EXP ( A(MI) )" and the sine of A in RADIANS.
    "VEXP":  ([0, 1, 6, 1, 3],  [0.0, 1.0, 2.0],  6,
              [1.0, 2.718281828459045, 7.38905609893065]),
    "VSIN":  ([0, 1, 6, 1, 3],  [0.0, 0.5235987755982988, 1.5707963267948966],
              6, [0.0, 0.5, 1.0]),
    # VSIN5: four inputs APPROACHING PI/2, to tell a SPIKE exactly at the
    # U == SFFTSZ boundary from a trend that grows near it.  U is 3911,
    # 4093, 4095.8 and 4096 respectively.
    "VSIN5": ([0, 1, 6, 1, 4],  [1.5, 1.57, 1.5707, 1.5707963267948966],
              6, [0.9974949866040544, 0.9999996829318346, 0.9999999953605743, 1.0]),
    # VSIN4: separates "small D" from "fold boundary", which VSIN3 left
    # confounded -- PI/2 and PI/4 are BOTH near-integer U AND boundaries,
    # while PI/6 and PI/3 are neither.  These three inputs put U at
    # EXACTLY 1000, 1500 and 700 -- tiny D, ordinary table positions, no
    # quadrant step -- with PI/6 as the large-D control.
    "VSIN4": ([0, 1, 6, 1, 4],
              [0.38349519697400064, 0.575242795461001,
               0.26844663788180045, 0.5235987755982988],
              6, [0.3741640629738602, 0.5440385267341441,
                  0.2652340302872601, 0.49999999999999994]),
    # VCOS exercises the FFT fold's COSINE path where VSIN exercises the
    # sine path (bit 0 of the folded TMA selects between them), and it is
    # one of the seven routines using SCALE.  Convention is VMOV's.
    "VCOS":  ([0, 1, 6, 1, 3], [0.0, 0.7853981633974483, 1.0471975511965976], 6, [1.0, 0.7071067811865476, 0.5000000000000001]),
    # VATAN is the ONLY consumer of the !ATAN coefficient table.  VDIV,
    # VSQRT, VLOG, VSIN and VEXP cover !DIV, !SQRT, !LOG, !SNCS and !EXP;
    # !ATAN was the one function-coefficient run never exercised, and this
    # file records all six as RECONSTRUCTED from SIM100's partial ROM
    # image.  Inputs avoid atan(0)=0 so no expectation is degenerate.
    # MAXV -- "THIS OUTPUTS THE MAX ELEMENT OF A VECTOR", $ENTRY MAXV,4 with
    # A=0 I=1 C=2 N=3.  It is the only routine here that COMPARES elements,
    # so it exercises the float branch table's ordering arms on real data;
    # VMA reaches only BFGT, and as a loop countdown rather than a compare.
    # The max is deliberately in the MIDDLE, so a routine that kept the
    # first or the last element would pass a monotone vector and fail here.
    # It also writes the extremum's MD address into C+1, hence 2 outputs.
    "MAXV":  ([0, 1, 6, 3], [2.0, 7.0, 3.0], 6, [7.0]),
    # MINV -- MAXV's sibling, same A I C N convention.  The two-sided rule
    # this session established for BDBN (VATAN/VATAN2): after testing one
    # sense of a comparison, test the OTHER, since a routine that always
    # kept the larger would pass MAXV and fail here.  The extremum is again
    # in the MIDDLE so first/last-element behaviour also fails.
    "MINV":  ([0, 1, 6, 3], [7.0, 2.0, 5.0], 6, [2.0]),
    # HANN -- SIGLIB, the first routine here from a THIRD library, and its
    # header notes "THIS ROUTINE USES THE TABLE MEMORY COSINE TABLE" -- a
    # third independent consumer of the trig table after VSIN/VCOS (fold)
    # and CFFT (twiddles).  CALL HANN(A,I,C,K,N,F), F=0 unnormalized:
    #   FORMULA: C(MK) = W*A(MI)*(1.0 - COS((2PI*M)/N)),  W = 0.5
    # DERIVED FROM THE SOURCE, not fitted to the output: the denominator is
    # N (not N-1), which is exactly the ambiguity that kept HANN out until
    # the formula line was found.  With A all ones and N=4 the window is
    #   M=0: 0    M=1: 0.5    M=2: 1.0    M=3: 0.5
    "HANN":  ([0, 1, 4, 1, 4, 0], [1.0, 1.0, 1.0, 1.0], 4,
              [0.0, 0.5, 1.0, 0.5]),
    # HANN2 -- F=1, the NORMALIZED window, W = SQRT(8/3) = 0.816496581,
    # "power invariant during the windowing operation" with a peak value of
    # 1.633.  The two-sided rule again: F=0 alone cannot show the flag is
    # read at all, exactly as CVMUL's F=0 could not (and there F=1 turned
    # out to BE the default, which is how that flag's semantics surfaced).
    # VDBPWR -- SIGLIB.  "FORMULA: C(MK)=10.0 * LOG10 (A(MI)/B)", and B is
    # the ADDRESS OF A SCALAR reference (the VSMUL shape), here MD 3 = 1.0.
    # A = [1,10,100] gives exactly 0, 10, 20 dB -- powers of ten so the
    # expectation is exact rather than a log approximation, and it is a
    # SECOND consumer of the !LOG coefficient run after VLOG.
    "VDBPWR": ([0, 1, 3, 4, 1, 3], [1.0, 10.0, 100.0, 1.0], 4,
               [0.0, 10.0, 20.0]),
    # VAVLIN -- SIGLIB's running linear average, and the first ACCUMULATING
    # IN PLACE routine here: its formula READS C as well as writing it,
    #   "FORMULA: C(MK)=C(MK)*B/(B+1) + A(MI)/(B+1)
    # where B is the ADDRESS of the current frame count.  The harness clears
    # the result area, so C starts at 0 and the expression reduces exactly
    # to A/(B+1) -- with B=1 that is A/2, which is exact in binary.
    "VAVLIN": ([0, 1, 3, 4, 1, 3], [2.0, 4.0, 6.0, 1.0], 4,
               [1.0, 2.0, 3.0]),
    # ASPEC -- SIGLIB's auto-spectrum, CALL ASPEC(A,C,N): a COMPLEX source
    # and a REAL destination, the first routine here whose input and output
    # have DIFFERENT element widths (2 words in, 1 word out) and which
    # therefore has no stride parameters at all.
    #   "FORMULA:  C(M) = C(M) + A(2M)**2 + A(2M+1)**2
    # It ACCUMULATES into C like VAVLIN, so a cleared C gives |A|^2 exactly.
    #   A = [1+2i, 3+4i]  ->  [1+4, 9+16] = [5, 25]
    "ASPEC": ([0, 4, 2], [1.0, 2.0, 3.0, 4.0], 4, [5.0, 25.0]),
    "ASPEC1": ([0, 4, 1], [1.0, 2.0], 4, [5.0]),
    # CSPEC -- SIGLIB's cross-spectrum, CALL CSPEC(A,B,C,N), and its
    # formula spells the conjugate out rather than leaving it to a flag:
    #  "C(2M)+IC(2M+1) = (C..) + (A(2M)-IA(2M+1))*(B(2M)+IB(2M+1))
    # i.e. conj(A)*B accumulated into C -- the same product CVMUL computes
    # under F=-1, reached here through a completely different routine and
    # written explicitly, which CORROBORATES the CVMUL2 reading that its
    # own header contradicted.
    #   conj(1+2i)*(3+4i) = (1-2i)(3+4i) = 11 - 2i
    "CSPEC": ([0, 2, 4, 1], [1.0, 2.0, 3.0, 4.0], 4, [11.0, -2.0]),
    # TRANS -- SIGLIB's transfer function, CALL TRANS(A,B,C,N):
    #   "FORMULA:  C(2M)+IC(2M+1) = (B(2M)+IB(2M+1)) / A(M)
    # a COMPLEX vector divided by a REAL one, with A the autospectrum and B
    # the cross-spectrum.  It is the first routine here to reach the DIVIDER
    # through complex data -- VDIV is the only other divider consumer and it
    # is purely real -- and the operand widths differ again (1 word in A, 2
    # in B and C).
    #   (8+4i) / 2 = 4 + 2i
    "TRANS": ([0, 1, 4, 1], [2.0, 8.0, 4.0], 4, [4.0, 2.0]),
    "HANN2": ([0, 1, 4, 1, 4, 1], [1.0, 1.0, 1.0, 1.0], 4,
              [0.0, 0.816496581, 1.632993162, 0.816496581]),
    # VMAX -- FROM BABLIB, the first routine here out of a SECOND library.
    # Every other test links from BAALIB; "one library proves one library"
    # is this project's own lesson and the .APO path had only ever been
    # exercised on one.  BABLIB is also the library assembled by the LATER
    # ASM100 that writes ***FPB rather than ***PB, so this drives the
    # parameter-block spelling the linker had to accept.
    #   C(M*K) = MAX(A(M*I), B(M*J)), VADD's seven-parameter shape.
    #   max([1,5,3],[4,2,6]) = [4,5,6]
    "VMAX":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 3.0, 4.0, 2.0, 6.0], 6,
              [4.0, 5.0, 6.0]),
    # VMAXMG -- "C(MK) = MAX ( ABS(A(MI)), ABS(B(MJ)) )", the same
    # A I B J C K N shape.  It is the FIRST test to combine FABS with a
    # COMPARISON: VABS covers the one and VMAX/MINV the other, never
    # together.  The data makes the two disagree -- for element 1 the
    # LARGER magnitude belongs to the NEGATIVE operand, so a routine
    # comparing signed values keeps 3.0 and fails.
    "VMAXMG": ([0, 1, 3, 1, 6, 1, 3],
               [-5.0, 2.0, -1.0, 3.0, -7.0, 0.0], 6, [5.0, 7.0, 1.0]),
    # ACORT -- SIGLIB's autocorrelation, A C N M where N is the number of
    # LAGS and M the length of A.  "SIZE: 12 + TCONV (112) = 124", so it
    # is a 12-instruction shell over a 112-instruction convolution.
    #
    # THE FIRST NESTED ACCUMULATION HERE: one sum per lag, each over a
    # DIFFERENT number of terms --
    #     C(P) = SUM FROM Q=0 TO M-P-1 (A(P+Q) * A(Q))
    # so the inner loop's trip count SHRINKS as the outer advances, a
    # control shape no other routine in the suite has (DOTPR accumulates
    # once, MMUL's loops are both fixed).
    #
    # A = [1,2,3], M=3, N=2:
    #     lag 0 = 1*1 + 2*2 + 3*3 = 14
    #     lag 1 = 2*1 + 3*2       = 8
    # Integers throughout, so the answer is exact and needs no tolerance.
    "ACORT": ([0, 3, 2, 3], [1.0, 2.0, 3.0], 3, [14.0, 8.0]),
    # CCORT -- the CROSS-correlation sibling, A B C N M (five parameters
    # where ACORT has four), same TCONV closure.  ACORT correlates a
    # vector with ITSELF, so it cannot tell whether the second operand is
    # read at all; CCORT uses a different B and its answers change if the
    # two are confused.
    #     C(P) = SUM FROM Q=0 TO M-P-1 (A(P+Q) * B(Q))
    #     A=[1,2,3] B=[4,5,6] M=3 N=2:
    #         lag 0 = 1*4 + 2*5 + 3*6 = 32
    #         lag 1 = 2*4 + 3*5       = 23
    "CCORT": ([0, 3, 6, 2, 3], [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 6,
              [32.0, 23.0]),
    # ACORT4 / ACORF -- THE SAME FUNCTION BY TWO DIFFERENT ALGORITHMS,
    # both FPS's.  ACORT correlates in the TIME domain through TCONV;
    # ACORF "PERFORMS AUTO-CORRELATION USING FFT TECHNIQUES", zero-padding
    # and calling VCLR, RFFT, VMUL, CVMAGS, RFFTSC and VMOV -- 499 words
    # against ACORT's 124.  Run on identical data they must agree, which
    # is FPS's own code checking FPS's own code rather than either being
    # checked against arithmetic I did myself.
    #
    # ACORF's header states its two extra requirements outright:
    #     "M = ELEMENT COUNT FOR A (POWER OF 2)"
    #     "ROUTINE REQUIRES 2M WORDS FOR VECTOR A"
    # so M=4 with an EIGHT-word buffer -- it inserts M zeros itself and
    # transforms in place, destroying A.
    #
    # A = [1,2,3,4], M=4, N=2:
    #     lag 0 = 1+4+9+16          = 30
    #     lag 1 = 2*1 + 3*2 + 4*3   = 20
    "ACORT4": ([0, 8, 2, 4], [1.0, 2.0, 3.0, 4.0], 8, [30.0, 20.0]),
    # Entered through the ADC stub, so the s-pads carry only RESLVE's two
    # arguments -- the parameter block's address and its count -- and the
    # real parameters come from the block in main data (see MD_WORDS).
    "ACORF":  ([20, 4], [1.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.0], 8,
               [30.0, 20.0]),
    # VMIN -- BABLIB's elementwise minimum, VMAX's sibling and the same
    # A I B J C K N shape.  Two-sided again: a routine keeping the LARGER
    # would pass VMAX and fail here.  (Note the generated entry lists NN
    # "FLOATED VECTOR LENGTH" at s-pad 1 alongside I -- an internal alias
    # sharing the register, not a second parameter; the $ENTRY count of 7
    # and the A I B J C K N sequence are what matter.)
    #   min([1,5,3],[4,2,6]) = [1,2,3]
    "VMIN":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 3.0, 4.0, 2.0, 6.0], 6,
              [1.0, 2.0, 3.0]),
    # VCLIP -- BABLIB, CALL VCLIP(A,I,B,C,D,L,N) with B and C the ADDRESSES
    # of the smaller and larger scalar bounds:
    #   "FORMULA:  D(ML) = B      IF A(MI)<B
    #             (and = C if A(MI)>C, else A(MI) -- the standard clip)
    # The first routine here whose output is CONDITIONAL PER ELEMENT with
    # THREE outcomes, so one vector exercises all three arms at once.
    #   clip([1,5,9], 2, 7) = [2, 5, 7]
    "VCLIP": ([0, 1, 3, 4, 5, 1, 3], [1.0, 5.0, 9.0, 2.0, 7.0], 5,
              [2.0, 5.0, 7.0]),
    # VLIM -- a HARD limiter, and note it is NOT VCLIP: B is the threshold
    # to compare against and C the magnitude to emit, so the OUTPUT NEVER
    # CONTAINS THE INPUT.
    #   "FORMULA:  D(ML) = -C      IF A(MI)<B
    #             = C      IF A(MI)>=B
    # The boundary case matters, so A includes an element EQUAL to B --
    # ">=" and ">" would differ there, and only that element distinguishes
    # them.
    #   lim([1,5,9], B=5, C=100) = [-100, 100, 100]
    "VLIM":  ([0, 1, 3, 4, 5, 1, 3], [1.0, 5.0, 9.0, 5.0, 100.0], 5,
              [-100.0, 100.0, 100.0]),
    # LVGT -- a LOGICAL vector compare, producing 1.0/0.0 rather than an
    # arithmetic result:
    #   "THIS ALGORITHM DOES  C(mK) = 1.0  IF  A(mI)>B(mJ)
    #                         C(mK) = 0.0  IF  A(mI)=<B(mJ)
    # (its header says DOES, not FORMULA -- both are in the reference.)
    # B includes an element EQUAL to A so the ">" / ">=" boundary is
    # exercised: only that element distinguishes them.
    #   [1,5,9] > [5,5,5]  ->  [0, 0, 1]
    "LVGT":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 9.0, 5.0, 5.0, 5.0], 6,
              [0.0, 0.0, 1.0]),
    # LVGE / LVEQ / LVNE -- LVGT's siblings, same shape, each a different
    # comparison, all quoted from their own "THIS ALGORITHM DOES" headers:
    #   LVGE  1.0 IF A=>B      LVEQ  1.0 IF A=B      LVNE  1.0 IF A not=B
    # The SAME data [1,5,9] vs [5,5,5] gives a DIFFERENT answer for each of
    # the four, so together they pin the boundary element from every side:
    #   LVGT [0,0,1]   LVGE [0,1,1]   LVEQ [0,1,0]   LVNE [1,0,1]
    # A routine (or a branch arm) implementing the wrong sense cannot pass
    # all four.
    "LVGE":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 9.0, 5.0, 5.0, 5.0], 6,
              [0.0, 1.0, 1.0]),
    "LVEQ":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 9.0, 5.0, 5.0, 5.0], 6,
              [0.0, 1.0, 0.0]),
    "LVNE":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 5.0, 9.0, 5.0, 5.0, 5.0], 6,
              [1.0, 0.0, 1.0]),
    # LVNOT -- A I C K N, the logical NOT of a mask:
    #   "C(mK) = 1.0 IF A(mI)=0.0 ; = 0.0 IF A(mI)not=0.0
    "LVNOT": ([0, 1, 3, 1, 3], [0.0, 1.0, 0.0], 3, [1.0, 0.0, 1.0]),
    # VRAMP -- a GENERATOR: no input vector, only two scalar ADDRESSES.
    #   "FORMULA:  C(MK)=M*B+A          A = initial value, B = step
    #   A=1, B=2, N=3  ->  1, 3, 5
    # A=initial, B=step (both ADDRESSES), C=2, K=1, N=3 -> MD 2,3,4.
    # The 42.0 at MD 5 is the overrun guard; a fourth ramp element would
    # write 7.0 there.  Deliberately NOT 5.0, which is the last legitimate
    # value -- a sentinel that collides with real output reads ambiguously.
    "VRAMP": ([0, 1, 2, 1, 3], [1.0, 2.0, 0.0, 0.0, 0.0, 42.0], 2,
              [1.0, 3.0, 5.0, 42.0]),
    # VFILL -- the real counterpart of CVFILL, one scalar ADDRESS:
    #   "FORMULA:  C(MK)=A
    # THE READBACK WINDOW RUNS ONE PAST N, AND MD 4 HOLDS A SENTINEL.
    # A constant-output test whose window is exactly N cannot see an
    # OVERRUN: a routine filling N+1 elements writes 7.0 past the end and
    # every checked value still matches.  The 5.0 at MD 4 must survive.
    # Same weakness class as VSBSBM's constant output and VCLR's
    # clear-into-already-zero memory, both caught by this audit.
    "VFILL": ([0, 1, 1, 3], [7.0, 0.0, 0.0, 0.0, 5.0], 1,
              [7.0, 7.0, 7.0, 5.0]),
    # VLN -- the NATURAL logarithm, VLOG's sibling and the pair that makes
    # the base explicit.  VLOG is base 10 (its banner says so, and an
    # earlier run here scored it against natural logs and "failed" a
    # correct routine); VLN states "COMPUTES NATURAL LOGARITHM" and
    #   "FORMULA:  C(MK) = LN (ABS(A(MI))
    # Testing one says NOTHING about the other -- that is the whole point
    # of adding it.  ln(1)=0, ln(e)=1, ln(e^2)=2.
    # VATN2 -- the two-argument arctangent, "DOES C(M) = ARCTANGENT
    # ( B(M) / A(M) )".  Its header ALSO says "GIVES ANSWERS IN RADIANS
    # AROUND A FULL CIRCLE", and THAT IS NOT WHAT IT COMPUTES: the scalar
    # helper it calls states its own contract in APFSRC,
    #     "ALSO, DOES ATN2(X,Y) = ATAN(Y/X)
    # i.e. the arctangent OF THE RATIO, with no quadrant adjustment -- and
    # VATN2 is "3 LOCATIONS + VFCL2 (12) + ATN2 (74)", three instructions
    # that cannot add one.  Measured output matches ATAN(B/A) to the digit.
    # FOURTH shipped header contradicted by shipped code, after VSUB's
    # abstract, VLOG's mnemonic and CVMUL's conjugate formula.
    #   atan(1/1)=pi/4  atan(1/-1)=-pi/4  atan(-1/-1)=pi/4
    "VATN2": ([0, 1, 3, 1, 6, 1, 3],
              [1.0, -1.0, -1.0, 1.0, 1.0, -1.0], 6,
              [0.78539816339744828, -0.78539816339744828, 0.78539816339744828]),
    # VFRAC -- the NAME says fraction, the HEADER says otherwise:
    #   "THIS ALGORITHM TRUNCATES THE FRACTION OF FLOATING PT
    #   "NUMBERS ... IT PUTS THESE INTEGER FLOATING POINT NUMBERS IN C
    # i.e. it REMOVES the fraction and emits the integer part as a float --
    # the same result as VINT, under a name suggesting the opposite.
    # MEASURED: it returns the FRACTION -- [0.7, 0.3, 0.9] for
    # [1.7, 2.3, 3.9] -- so the MNEMONIC is right and the HEADER is wrong.
    # That is the FIFTH shipped header contradicted by shipped code here,
    # and the FIRST where the name was the better guide (VSUB, VLOG, CVMUL
    # and VATN2 all had misleading names or prose with correct formulas).
    # Read "TRUNCATES THE FRACTION" as "truncates OFF the integer part".
    # Tolerance: 0.7 and 0.9 are not exact in binary, and the readback is
    # float32.
    "VFRAC": ([0, 1, 3, 1, 3], [1.7, 2.3, 3.9], 3, [0.7, 0.3, 0.9]),
    # VTSMUL -- "Table-memory Scalar MULtiply": its scalar operand B is a
    # TABLE MEMORY ADDRESS, not a main-data one.
    #   "FORMULA:  C(MK) = A(MI) * B
    # THE FIRST TEST HERE WITH A TABLE-MEMORY OPERAND AS A PARAMETER.  The
    # harness cannot write TM (it is ROM in the emulator, and TMRAM is not
    # modelled), but it does not need to: `!ONE` at 4097 is verified in
    # this file as exactly 1.0 -- checked against SIM100's TMROM triple
    # (513,1024,0) and used by VDIV -- so B=4097 multiplies by one and the
    # answer is the input, exactly.
    # Uses TM 4098, NOT !ONE at 4097: multiplying by one makes the output
    # equal the input, so a routine that ignored the TM operand entirely
    # would pass.  4098 is the first entry of the !DIV reciprocal run and
    # is verified in this file as exactly 2.0 (SIM100's TMROM triple
    # (514,1024,0), and VDIV reads it as the seed for a mantissa of 0.5).
    #   [1,2,3] * 2 = [2,4,6]
    "VTSMUL": ([0, 1, 4098, 3, 1, 3], [1.0, 2.0, 3.0], 3, [2.0, 4.0, 6.0]),
    # VTSADD -- VTSMUL's sibling, same A I B C K N shape:
    #   "ADDS TO EACH ELEMENT OF VECTOR A THE TABLE MEMORY SCALAR
    #   "C(MK) = A(MI) + B
    # For an ADD the !ONE constant gives a real shift rather than the
    # identity a multiply-by-one would, so this is the stronger of the
    # pair: A + 1 = [2,3,4] distinguishes a working routine from one that
    # copies its input, which VTSMUL alone cannot.
    "VTSADD": ([0, 1, 4097, 3, 1, 3], [1.0, 2.0, 3.0], 3, [2.0, 3.0, 4.0]),
    # VSMA -- "THIS ALGORITHM DOES D<=A*B+C WHERE B IS A SCALAR AND A AND
    # C ARE VECTORS".  Eight parameters, A I B C J D K N, with B the
    # ADDRESS of the scalar.  It is VMA's scalar counterpart (VMA takes
    # three vectors) and so drives the multiplier with one operand held
    # constant across the loop rather than reloaded per element.
    #   A=[1,2,3] * 10 + C=[5,6,7]  ->  [15, 26, 37]
    # VAM / VMSB -- three-vector compound arithmetic, A I B J C K D L N.
    # They differ in ORDER OF OPERATIONS, not just operator: VAM adds THEN
    # multiplies, VMSB multiplies THEN subtracts, so the adder and
    # multiplier run in the opposite sequence through the pipelines.
    #   "DOES D <=(A+B)*C            (1+4)*10=50, (2+5)*20=140, (3+6)*30=270
    #   "DOES D <= A*B-C             1*4-10=-6, 2*5-20=-10, 3*6-30=-12
    "VAM":   ([0, 1, 3, 1, 6, 1, 9, 1, 3],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 20.0, 30.0], 9,
              [50.0, 140.0, 270.0]),
    # VSBM -- VAM's mirror: subtract THEN multiply.
    #   "DOES D <=(A-B)*C     (1-4)*10=-30, (2-5)*20=-60, (3-6)*30=-90
    # VMMA -- ELEVEN parameters and FOUR source vectors, the widest calling
    # convention in the suite:  "DOES E<= A*B+C*D
    # A I B J C K D L E M N, s-pads 0..10 -- E, M and N are written
    # "$EQU 8." / "9." / "10.", ASM100's DOTTED DECIMAL under $RADIX 8.
    #   [1,2]*[3,4] + [5,6]*[7,8] = [3+35, 8+48] = [38, 56]
    "VMMA":  ([0, 1, 2, 1, 4, 1, 6, 1, 8, 1, 2],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [38.0, 56.0]),
    # VMMSB -- VMMA's sibling, "DOES E<= A*B-C*D", identical eleven-
    # parameter shape.  The same data gives a completely different answer,
    # so the pair pins the sign of the second product:
    #   [1,2]*[3,4] - [5,6]*[7,8] = [3-35, 8-48] = [-32, -40]
    # VAAM / VSBSBM -- eleven parameters like VMMA/VMMSB, but the ADDS
    # come FIRST and feed ONE multiply, where VMMA does two multiplies into
    # one add.  Same operand count, opposite pipeline shape.
    #   " (A+B)*(C+D)=>E     (1+3)*(5+7)=48, (2+4)*(6+8)=84
    #   " (A-B)*(C-D)=>E     (1-3)*(5-7)= 4, (2-4)*(6-8)= 4
    # VSBSBM's answers are EQUAL, which is a weak discriminator on its own
    # -- but VAAM's differ, and the two share a code path, so the pair is
    # what makes either meaningful.
    # VSMSA -- "D <= A*B+C WHERE B,C ARE [scalars] AND A AND D ARE
    # VECTORS", seven parameters A I B C D L N.  BOTH scalars, where VSMA
    # has a scalar B and a VECTOR C -- so the two differ in operand KIND at
    # the same position, and the s-pad list is the only thing that says so.
    #   A=[1,2,3] * 10 + 5  ->  [15, 25, 35]
    # MTRANS -- matrix transpose, A I C K NC NR where NC is the columns of
    # A and NR its rows.  Matrices are COLUMN-MAJOR here (settled by MMUL,
    # which needed that correction), so a 2x3 stored [1,2,3,4,5,6] is
    #     A = [[1,3,5],
    #          [2,4,6]]
    # and its 3x2 transpose stored column-major is [1,3,5,2,4,6] -- a real
    # permutation, not the identity the same digits might suggest.
    # MVML3 -- a 3x3 matrix times a SERIES of 3-element vectors, nine
    # parameters A I B J JP C K KP N with SEPARATE strides WITHIN a vector
    # (J, K) and BETWEEN vectors (JP, KP).  Nothing else here has a
    # two-level stride.
    # A is diag(1,2,3) column-major so each output element is distinct and
    # a transposed or identity-confused matrix would fail:
    #   diag(1,2,3) * [7,8,9] = [7, 16, 27]
    # MATINV -- "INVERTS AN N-BY-N MATRIX BY GAUSSIAN ELIMINATION",
    # IN PLACE, with only two parameters: A (base) and N (dimension).
    # Its own note says "MATRICES ARE COLUMN-STORED" -- a THIRD independent
    # statement of the convention after MMUL and MTRANS.
    # A SOLVER whose expectation is nonetheless CLOSED FORM: the inverse of
    # a diagonal matrix is the reciprocal diagonal, and 2 and 4 invert
    # exactly in binary, so no tolerance and no reimplementation is needed.
    #   diag(2,4)^-1 = diag(0.5, 0.25)
    # MATINV -- NOT IN PLACE, despite taking only a base and a dimension:
    #   "NOTE: MATRICES ARE COLUMN-STORED.  THE BEGINNING OF THE
    #   "      OUTPUTTED MATRIX IS AT LOCATION APTR+N*N.
    # so with A at 0 and N=2 the inverse lands at MD 4.  A first attempt
    # read back from 0 and saw the INPUT (with a sign flipped by the
    # elimination), which looked like a routine that had failed halfway.
    # Singularity is reported in S-PAD 15, 0 otherwise.
    # A SOLVER with a CLOSED-FORM expectation: diag(2,4) inverts to
    # diag(0.5,0.25), exact in binary, so no tolerance and no
    # reimplementation of Gaussian elimination is needed to check it.
    "MATINV": ([0, 2], [2.0, 0.0, 0.0, 4.0], 4, [0.5, 0.0, 0.0, 0.25]),
    # SOLVEQ -- Gaussian elimination for simultaneous linear equations.
    # Its $EQU block is unusable (scratch aliases share s-pads 1 and 2
    # with N and the pointers), but the source gives the order outright:
    #   "FORTRAN CALL:  CALL SOLVEQ(A,N,B,M,ROWADD,X,STST)
    # ROWADD is a WORK VECTOR OF LENGTH 2*N and "MATRICES A AND B ARE
    # DESTROYED", so the layout needs five regions:
    #   A  0..3   diag(2,4) column-order      B  4..5   [8,12]
    #   ROWADD 6..9 (2*N=4)                   X 10..11  STST 12
    # Closed form despite being a solver: 2x=8, 4y=12  ->  x=4, y=3,
    # exact in binary, so no reimplementation of the elimination is needed.
    # EIGRS -- AMLLIB's eigenvalue solver, "DETERMINES THE EIGENVALUES [AND
    # EIGEN]VECTORS OF A REAL SYMMETRIC MATRIX ... BASED ON THE [EISPACK]
    # PROGRAM", calling TRED2 then IMTQL2.
    #   "FORTRAN CALL:  CALL EIGRS (NM,N,Z,E,D)
    # NM row dimension, N order, Z the matrix (eigenvectors on output),
    # E the sub-diagonal workspace, D the EIGENVALUES.
    # THE FIRST AMLLIB ROUTINE EXECUTED HERE -- the library with no
    # surviving manual, whose calling sequence became readable only when
    # the generator stopped truncating headers at 400 lines.
    # Closed form: the eigenvalues of a diagonal matrix are its diagonal.
    "EIGRS": ([2, 2, 0, 4, 6], [2.0, 0.0, 0.0, 4.0], 6, [2.0, 4.0]),
    # IMTQL2 -- the QL half of EIGRS, called directly:
    #   "FORTRAN CALL:   CALL IMTQL2 (NM,N,Z,E,D)
    # Z the eigenvector matrix (identity on input), E the SUB-diagonal,
    # D the diagonal and the eigenvalues on output.  A genuine TRIDIAGONAL
    # [[3,1],[1,3]] has eigenvalues 2 and 4, so unlike EIGRS's diagonal
    # case this exercises real QL iteration rather than a matrix already
    # in final form.  EISPACK leaves E(1) arbitrary and puts the
    # sub-diagonal in E(2..N).
    # TRED2 -- the Householder half of EIGRS, "TRIDIAGONIZES THE MATRIX":
    #   "FORTRAN CALL:  CALL TRED2 (NM,N,Z,E,D)
    # For a 2x2 symmetric matrix the input is ALREADY tridiagonal, so D
    # must come back as the diagonal unchanged -- a weak but unambiguous
    # check that the routine runs and writes where it says.  A 3x3 would
    # exercise the reflections properly but its expectation is no longer
    # closed form.
    #   [[3,1],[1,3]]  ->  D = [3, 3]
    "TRED2": ([2, 2, 0, 4, 6], [3.0, 1.0, 1.0, 3.0], 6, [3.0, 3.0]),
    # EIGRS3 -- a 3x3 that ACTUALLY NEEDS TRIDIAGONALISING, closing the
    # gap the TRED2 entry records: a 2x2 is already tridiagonal, so
    # nothing above exercised the Householder reflections.
    # J-form [[2,1,1],[1,2,1],[1,1,2]] = I + ones(3), whose eigenvalues are
    # 1+3=4 once and 1 twice -- EXACT, so a full 3x3 reduction plus QL
    # iteration is checked against algebra rather than an independent
    # implementation.  Z 0..8 (column-order, symmetric so it is its own
    # transpose), E 9..11, D 12..14.  IMTQL2 returns them ascending.
    "EIGRS3": ([3, 3, 0, 9, 12],
               [2.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 2.0], 12,
               [1.0, 1.0, 4.0]),
    "IMTQL2": ([2, 2, 0, 4, 6],
               [1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 3.0, 3.0], 6,
               [2.0, 4.0]),
    # MATINV2 -- a NON-DIAGONAL matrix, closing the same gap for MATINV
    # that EIGRS3 closed for EIGRS: a diagonal matrix has nothing to
    # eliminate, so the first case exercised the plumbing and not the
    # Gaussian elimination.
    #   A = [[1,1],[0,1]]  (unit upper triangular, column-stored [1,0,1,1])
    #   A^-1 = [[1,-1],[0,1]]                     column-stored [1,0,-1,1]
    # Exact in binary -- the elimination must actually cancel the
    # off-diagonal, and the answer needs no tolerance.
    "MATINV2": ([0, 2], [1.0, 0.0, 1.0, 1.0], 4, [1.0, 0.0, -1.0, 1.0]),
    # SOLVEQ2 -- a TRIANGULAR system, closing SOLVEQ's remaining weakness:
    # its first case is diagonal, so the elimination never eliminates and
    # the back-substitution never substitutes across rows.
    #   [[2,1],[0,2]] x = [4,6]      column-stored A = [2,0,1,2]
    #   2y = 6 -> y = 3 ;  2x + y = 4 -> x = 0.5      both exact
    "SOLVEQ2": ([0, 2, 4, 1, 6, 10, 12],
                [2.0, 0.0, 1.0, 2.0, 4.0, 6.0], 10, [0.5, 3.0]),
    "SOLVEQ": ([0, 2, 4, 1, 6, 10, 12],
               [2.0, 0.0, 0.0, 4.0, 8.0, 12.0], 10, [4.0, 3.0]),
    "MVML3": ([0, 1, 9, 1, 3, 12, 1, 3, 1],
              [1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 3.0, 7.0, 8.0, 9.0],
              12, [7.0, 16.0, 27.0]),
    "MTRANS": ([0, 1, 6, 1, 3, 2],
               [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 6,
               [1.0, 3.0, 5.0, 2.0, 4.0, 6.0]),
    "VSMSA": ([0, 1, 3, 4, 5, 1, 3],
              [1.0, 2.0, 3.0, 10.0, 5.0], 5,
              [15.0, 25.0, 35.0]),
    "VAAM":  ([0, 1, 2, 1, 4, 1, 6, 1, 8, 1, 2],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [48.0, 84.0]),
    # VSBSBM's data is now its OWN, not VAAM's.  Sharing them made both
    # outputs 4, so the test would have passed a routine computing any
    # constant -- recorded as a weakness when it was added, and closed
    # here.  A=[1,2] B=[3,5] C=[5,6] D=[7,10]:
    #   (1-3)*(5-7) = 4 ;  (2-5)*(6-10) = 12      distinct
    "VSBSBM": ([0, 1, 2, 1, 4, 1, 6, 1, 8, 1, 2],
               [1.0, 2.0, 3.0, 5.0, 5.0, 6.0, 7.0, 10.0], 8,
               [4.0, 12.0]),
    "VMMSB": ([0, 1, 2, 1, 4, 1, 6, 1, 8, 1, 2],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [-32.0, -40.0]),
    "VSBM":  ([0, 1, 3, 1, 6, 1, 9, 1, 3],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 20.0, 30.0], 9,
              [-30.0, -60.0, -90.0]),
    "VMSB":  ([0, 1, 3, 1, 6, 1, 9, 1, 3],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 20.0, 30.0], 9,
              [-6.0, -10.0, -12.0]),
    "VSMA":  ([0, 1, 3, 4, 1, 7, 1, 3],
              [1.0, 2.0, 3.0, 10.0, 5.0, 6.0, 7.0], 7,
              [15.0, 26.0, 37.0]),
    # VSWAP -- EXCHANGES two vectors, so it WRITES BOTH operands.  Every
    # other routine here has read-only sources; this one has none, and a
    # half-done swap (copying A over C without saving C) is the obvious
    # failure it must exclude.
    # The harness reads back from ONE base, so C is checked directly and A
    # is checked by the readback window extending over it: A at 0..2 and
    # C at 3..5, read from 0, expects the SWAPPED pair end to end.
    "VSWAP": ([0, 1, 3, 1, 3], [1.0, 2.0, 3.0, 7.0, 8.0, 9.0], 3,
              [1.0, 2.0, 3.0]),   # C receives A's values
    "VLN":   ([0, 1, 3, 1, 3], [1.0, 2.7182818284590451, 7.3890560989306495], 3, [0.0, 1.0, 2.0]),
    # VLMERG -- A I B J C K D L N, and it CONSUMES what the LV routines
    # produce, which is what that family is for:
    #   "D(mL) = A(mI)  IF  C(mK)not=0.0
    #   "D(mL) = B(mJ)  IF  C(mK)=0.0
    # The mask [1,0,1] selects A, B, A -- both arms and both sources in one
    # call, and swapping the sense would give [10,2,30] rather than a
    # near-miss.
    "VLMERG": ([0, 1, 3, 1, 6, 1, 9, 1, 3],
               [1.0, 2.0, 3.0, 10.0, 20.0, 30.0, 1.0, 0.0, 1.0], 9,
               [1.0, 20.0, 3.0]),
    # MMUL -- BABLIB's matrix multiply, $ENTRY MMUL, 9. with s-pads
    # A I B J C K NRC NCC NCA (the last is s-pad 10 OCTAL = 8).  The first
    # TWO-DIMENSIONAL routine here: everything else walks one vector with a
    # stride, while this runs a row/column pair of nested loops and, per its
    # own algorithm note, stages a COLUMN OF B in DPY(0..31) -- the first
    # test to use the data pads as a working buffer rather than a staging
    # slot or two.
    # MATRICES ARE COLUMN-MAJOR, the FORTRAN convention -- a first attempt
    # expecting row-major got [23,34,31,46] where it wanted [19,22,43,50],
    # and the measured answer is exactly the column-major product.  So the
    # words [1,2,3,4] are [[1,3],[2,4]] and [5,6,7,8] are [[5,7],[6,8]]:
    #   [[1,3],[2,4]] x [[5,7],[6,8]] = [[23,31],[34,46]]
    # which stored column-major is 23, 34, 31, 46.
    # CFFT -- BABLIB's complex FFT, and the trig table's INTENDED consumer.
    # VSIN reaches that table only by interpolating a quarter-period cosine;
    # the FFT indexes it as the twiddle-factor table SIM100 calls it, which
    # is what the FFT-mode quadrant fold (SIM100 40100) exists for.
    # $ENTRY CFFT,3 : C=0 base address (IN PLACE), N=1 complex points,
    # F=2 direction (1 forward, -1 inverse).
    #   N=2 is deliberate: bit-reversal is the identity there, so the
    #   expected output needs no assumption about output ordering.
    #   x = [3+0i, 1+0i]  ->  X = [4+0i, 2+0i]
    "CFFT":  ([0, 2, 1], [3.0, 0.0, 1.0, 0.0], 0, [4.0, 0.0, 2.0, 0.0]),
    # CFFT4 -- N=4, where the twiddle factor is -i and the trig table is
    # GENUINELY indexed.  N=2 passes with a twiddle of 1 and proves nothing
    # about the table.  x = [1,2,3,4] real:
    #   X = [10, -2+2i, -2, -2-2i]
    # CFFT TAKES ITS INPUT IN BIT-REVERSED ORDER and returns natural order
    # -- a decimation-in-time FFT.  Feeding [1,2,3,4] naturally returned the
    # DFT of [1,3,2,4] exactly, which is what settled it; the IMPULSE case
    # (CFFTI) had already shown the arithmetic and the twiddle table to be
    # right, and Table 3-2's 1/N is a single factor that cannot produce a
    # per-bin difference.  So the input here is [1,3,2,4] -- [1,2,3,4]
    # bit-reversed -- and the expectation is that sequence's textbook DFT.
    "CFFT4": ([0, 4, 1], [1.0, 0.0, 3.0, 0.0, 2.0, 0.0, 4.0, 0.0], 0,
              [10.0, 0.0, -2.0, 2.0, -2.0, 0.0, -2.0, -2.0]),
    # CFFTI -- N=4 with an IMPULSE at n=0.  Its DFT is [1,1,1,1], which is
    # the SAME in any output ordering, so it separates "the arithmetic is
    # wrong" from "the ordering is not what I assumed".  Table 3-2 says a
    # forward CFFT rescales by 1/N, a single factor, so it cannot explain
    # CFFT4's per-bin ratios (1, 1/2, 2, 1/2) either.
    "CFFTI": ([0, 4, 1], [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0,
              [1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]),
    "MMUL":  ([0, 1, 4, 1, 8, 1, 2, 2, 2],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [23.0, 34.0, 31.0, 46.0]),
    # DOTPR -- "DOES C = SUM ( A(MI) * B(MJ) ) FOR M = 0 TO N-1", with
    # A=0 I=1 B=2 J=3 C=4 N=5.  The first ACCUMULATING routine here: every
    # other one stores per element, so the running-sum loop shape and its
    # drain have never been executed.  1*4 + 2*5 + 3*6 = 32.
    "DOTPR": ([0, 1, 3, 1, 6, 3], [1.0, 2.0, 3.0, 4.0, 5.0, 6.0], 6, [32.0]),
    # CVADD -- the COMPLEX family, 25 routines nothing here has touched.
    # A complex element is TWO main-data words, real then imaginary, and the
    # store is the `ADD K,C; SETMA; MI<FA` / `INCMA; MI<FA` pair this file
    # documents as the reason MI and MA must address the SAME word -- a
    # pre-increment there would write the real part twice and never store
    # the imaginary.  So the increments are in WORDS and must be 2.
    #   A = [1+2i, 3+4i] at MD 0, B = [5+6i, 7+8i] at MD 4
    #   C = [6+8i, 10+12i] at MD 8
    # CVMUL -- $ENTRY CVMUL, 8. : A I B J C K N F, where F is the
    # COMPLEX CONJUGATE flag (0 = plain multiply).  A complex product needs
    # FOUR real multiplies and two adds per element, so it drives the
    # multiplier pipeline unlike anything else here.
    #   (1+2i)(5+6i) = -7 + 16i     (3+4i)(7+8i) = -11 + 52i
    "CVMUL": ([0, 2, 4, 2, 8, 2, 2, 0],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [-7.0, 16.0, -11.0, 52.0]),
    # CVMUL2 -- the SAME routine with F = -1, the CONJUGATE mode.  F is
    # PLUS OR MINUS ONE, not 0/1, and FPS's own header gives both formulas:
    #     F =  1   Im(C) = AI*BR + AR*BI      (the plain product)
    #     F = -1   conj(A) * B  -- see below, the header is WRONG here
    # so F=0 and F=1 both give the plain product -- a first attempt with
    # F=1 returned CVMUL's own answer and looked like the flag being
    # ignored.  Note Re(C) is the SAME in both modes, so this is not
    # conj(B) in the textbook sense and the expectation must come from the
    # routine's formula, not from complex algebra.
    #   -1 is written as 65535: the s-pad file is 16-bit.
    "CVMUL2": ([0, 2, 4, 2, 8, 2, 2, 65535],
               [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
               [17.0, -4.0, 53.0, -4.0]),
    # CVCONJ -- the complex conjugate, stated plainly in its own header:
    #   "FORMULA:  C(MK) + IC(MK+1) = A(MI) - IA(MI+1)
    # Found via the GENERATED docs/BAALIB.md rather than by grepping the
    # source, which is what that document is for.  A I C K N, the CVMOV
    # shape, with the increments in WORDS (2 for packed complex).
    # It is also a THIRD independent statement about conjugation, after
    # CVMUL2's measurement and CSPEC's formula -- and unlike CVMUL's
    # header, this one is CORRECT.
    #   conj(1+2i, 3+4i) = 1-2i, 3-4i
    "CVCONJ": ([0, 2, 4, 2, 2], [1.0, 2.0, 3.0, 4.0], 4,
               [1.0, -2.0, 3.0, -4.0]),
    # CVNEG / CVMOV -- same A I C K N shape, both straight out of
    # docs/BAALIB.md.  CVNEG negates BOTH parts where CVCONJ negates only
    # the imaginary, so the pair distinguishes a conjugate from a negation:
    # a routine doing either one would pass the other's test on real data.
    #   "FORMULA:  C(MK)+IC(MK+1) = -A(MI)-IA(MI+1)
    # CVFILL -- A is the ADDRESS of a complex CONSTANT (A(0) real, A(1)
    # imaginary), so it takes only A C K N.  Fills C with that constant:
    #   "FORMULA:  C(MK)+IC(MK+1) = A(0)+IA(1)
    # Sentinel one COMPLEX element past the end, for the reason on VFILL:
    # N=2 fills MD 2-5, so a routine writing a third element lands on MD 6
    # and the 5.0 there must survive.
    "CVFILL": ([0, 2, 2, 2], [7.0, 9.0, 0.0, 0.0, 0.0, 0.0, 5.0], 2,
               [7.0, 9.0, 7.0, 9.0, 5.0]),
    # CVRCIP -- "THE ELEMENT BY ELEMENT RECIPROCAL OF A COMPLEX VECTOR",
    # A I C K N, and "SIZE: 23 LOCATIONS + DIVIDE".  It is the FOURTH
    # consumer of the divider (after VDIV, TRANS and CRVDIV) and the first
    # to drive it from a complex operand: 1/(a+ib) = (a-ib)/(a**2+b**2),
    # so each element costs a magnitude and two divides.
    # The inputs are chosen so every reciprocal is EXACT in binary --
    # 1/2, 1/(4i) = -i/4 and 1/(1+i) = (1-i)/2 -- which keeps the case off
    # a tolerance it would otherwise need for a Newton-Raphson quotient.
    "CVRCIP": ([0, 2, 6, 2, 3],
               [2.0, 0.0, 0.0, 4.0, 1.0, 1.0], 6,
               [0.5, 0.0, 0.0, -0.25, 0.5, -0.5]),
    # CVMAGS -- complex magnitude SQUARED: complex in, REAL out, so the
    # source stride is 2 and the destination stride 1.
    #   |3+4i|^2 = 25,  |1+2i|^2 = 5
    "CVMAGS": ([0, 2, 4, 1, 2], [3.0, 4.0, 1.0, 2.0], 4, [25.0, 5.0]),
    # CRVMUL -- COMPLEX times REAL, the mixed-width multiply: A complex
    # (stride 2), B real (stride 1), C complex (stride 2).
    #   (1+2i)*10 = 10+20i,  (3+4i)*100 = 300+400i
    # CRVDIV -- COMPLEX divided by REAL, both parts by the same divisor:
    #   "FORMULA:  C(MK)+IC(MK+1) = (A(MI)/B(MJ))+I(A(MI+1)/B(MJ))
    # The THIRD divider consumer (after VDIV and TRANS) and the only one
    # dividing BOTH components of a complex value by one real.  Divisors
    # are powers of two so the quotients are exact.
    #   (1+2i)/2 = 0.5+1i,   (3+4i)/4 = 0.75+1i
    # CRVADD / CRVSUB -- a REAL added to or subtracted from BOTH components:
    #   "C(MK)+IC(MK+1) = (A(MI)+B(MJ))+I(A(MI+1)+B(MJ))
    #   "C(MK)+IC(MK+1) = (A(MI)-B(MJ))+I(A(MI+1)-B(MJ))
    # NOTE THE SENSE: CRVSUB is A-B, while this project records VSUB as
    # B-A (its own FORMULA line and its `FSUB DPY,DPX` agree on that, and
    # the abstract contradicts them).  So the two subtracts in this library
    # genuinely differ in direction, and testing one says nothing about the
    # other.
    # CVMA -- complex multiply-add, TEN parameters:
    #   "FORTRAN CALL: CALL CVMA(A,I,B,J,C,K,D,L,N,F)
    #   "FORMULA: (D(ML)+ID(ML+1))=(C(MK)+IC(MK+1)) + ...
    # (the formula line is truncated IN THE SOURCE; the FORTRAN CALL and
    # the routine's name give the rest -- D = C + A*B, with F the
    # normal/conjugate flag as in CVMUL, 1 = normal.)
    # THIS IS THE ROUTINE THAT EXPOSED THE $RADIX 8 BUG in mkmanual.py:
    # its N and F are `$EQU 10` and `$EQU 11`, i.e. s-pads 8 and 9.
    #   (1+2i)*(3+4i) = -5+10i;  + (10+20i) = 5+30i
    "CVMA": ([0, 2, 2, 2, 4, 2, 6, 2, 1, 1],
             [1.0, 2.0, 3.0, 4.0, 10.0, 20.0], 6, [5.0, 30.0]),
    "CRVADD": ([0, 2, 4, 1, 6, 2, 2],
               [1.0, 2.0, 3.0, 4.0, 10.0, 100.0], 6,
               [11.0, 12.0, 103.0, 104.0]),
    "CRVSUB": ([0, 2, 4, 1, 6, 2, 2],
               [1.0, 2.0, 3.0, 4.0, 10.0, 100.0], 6,
               [-9.0, -8.0, -97.0, -96.0]),
    "CRVDIV": ([0, 2, 4, 1, 6, 2, 2],
               [1.0, 2.0, 3.0, 4.0, 2.0, 4.0], 6,
               [0.5, 1.0, 0.75, 1.0]),
    "CRVMUL": ([0, 2, 4, 1, 6, 2, 2],
               [1.0, 2.0, 3.0, 4.0, 10.0, 100.0], 6,
               [10.0, 20.0, 300.0, 400.0]),
    # CVCOMB -- combines TWO REAL vectors into one complex vector, so its
    # inputs are 1-word and its output 2-word:
    #   "FORMULA:  C(MK)+IC(MK+1) = A(MI)+IB(MJ)
    "CVCOMB": ([0, 1, 2, 1, 4, 2, 2], [1.0, 2.0, 5.0, 6.0], 4,
               [1.0, 5.0, 2.0, 6.0]),
    "CVNEG": ([0, 2, 4, 2, 2], [1.0, 2.0, 3.0, 4.0], 4,
              [-1.0, -2.0, -3.0, -4.0]),
    #   "FORMULA:  C(MK)+IC(MK+1) = A(MI)+IA(MI+1)
    "CVMOV": ([0, 2, 4, 2, 2], [1.0, 2.0, 3.0, 4.0], 4,
              [1.0, 2.0, 3.0, 4.0]),
    "CVADD": ([0, 2, 4, 2, 8, 2, 2],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 8,
              [6.0, 8.0, 10.0, 12.0]),
    "VATAN": ([0, 1, 6, 1, 3], [0.5, 1.0, 2.0], 6, [0.4636476090008061, 0.7853981633974483, 1.1071487177940904]),
    # VATAN2 -- the SAME routine on NEGATIVE inputs, and it is the only test
    # here that makes `BDBN` BRANCH.  DIVIDE's `BDBN NEG "SEE IF X IS NEG"`
    # is taken only for a negative operand, so VATAN (positive) proves just
    # the not-taken half of the sense settled from SIM100 11604.  Reading
    # BDBN as branch-if-non-zero passed nothing and reading it as
    # branch-if-POSITIVE would pass VATAN and fail here.
    "VATAN2": ([0, 1, 6, 1, 3], [-0.5, -1.0, -2.0], 6,
               [-0.4636476090008061, -0.7853981633974483, -1.1071487177940904]),
    # VALOG is 10**x -- "C(MK) = 10. ** A(M(I))" -- and is one of the
    # seven SCALE users.  It is VEXP's base-10 sibling and reaches the
    # !EXP coefficient table by a different route, so it covers the
    # exponent path independently of VEXP's own entry sequence.
    "VALOG": ([0, 1, 6, 1, 3], [0.0, 1.0, 2.0], 6, [1.0, 10.0, 100.0]),
    # VAND is the dedicated routine for the FAND arm, which was rewritten
    # TWICE this session (mantissa-only per SIM100 500, then onto the
    # shared alignment helper).  Same identity trick as VOR: A AND A = A.
    "VAND":  ([0, 1, 3, 1, 6, 1, 3], [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
              6, [1.0, 2.0, 3.0]),
    # VINT takes the INTEGER PART, so it exercises FIX on real data with a
    # directly predictable answer -- FIX was a pass-through until this
    # session and is only otherwise reached through VEXP and VSIN.
    # Convention is VMOV's: A,I,C,K,N.
    "VINT":  ([0, 1, 6, 1, 3], [1.7, 2.3, 3.9], 6, [1.0, 2.0, 3.0]),
    # VOR exercises the FOR arm, which was corrected from SIM100 label 600
    # (mantissa-only, aligned) with NO test covering it.  A and B are the
    # SAME vector, so "C = B OR A" must be the identity -- which needs no
    # bit-level expectation and cannot be satisfied by a wrong mask or a
    # mis-aligned operand.  Convention is VADD's: A,I,B,J,C,K,N.
    "VOR":   ([0, 1, 3, 1, 6, 1, 3], [1.0, 2.0, 3.0, 1.0, 2.0, 3.0],
              6, [1.0, 2.0, 3.0]),
    # VSIN3: FIVE elements with PI/2 in the MIDDLE (fourth).  VSIN stores
    # "RESULT IN C(I-4)" -- a four-deep software pipeline on top of a
    # three-iteration INTROLOOP -- so with only three elements the suspect
    # operand and "the first stored element" cannot be told apart.  VSIN2
    # moved PI/2 to the front but that kept it FIRST, so it did not
    # discriminate.  This one does.
    "VSIN3": ([0, 1, 6, 1, 5],
              [0.5235987755982988, 0.7853981633974483, 1.0471975511965976,
               1.5707963267948966, 0.0],
              6, [0.5, 0.7071067811865476, 0.8660254037844386, 1.0, 0.0]),
    # VSIN2: the SAME inputs with PI/2 FIRST instead of last.  If the
    # 1.2e-6 residual follows the PI/2 operand it is the 40100 special
    # case; if it stays on the LAST element it is pipeline drain, the
    # shape VMA and HSR VADD both turned out to have.
    "VSIN2": ([0, 1, 6, 1, 3],  [1.5707963267948966, 0.5235987755982988, 0.0],
              6, [1.0, 0.5, 0.0]),
    "VMA":   ([0, 1, 3, 1, 6, 1, 9, 1, 3],
              [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 10.0, 20.0, 30.0],
              9, [14.0, 30.0, 48.0]),
    }

if ROUTINE not in ROUTINES:
    raise SystemExit ("no calling convention recorded for %s -- add one to "
                      "ROUTINES from its $EQU block in BAASRC.APS" % ROUTINE)
# RAW main-data words, deposited through FN DEP rather than the DMA float
# path: {routine: {md_address: raw_16_bit_value}}.  For addresses, integer
# indices and auto-directed-call parameter blocks.  Empty for every routine
# that takes its parameters in the s-pads, which is all of them so far.
MD_WORDS = {
    # ACORF is called through its AUTO-DIRECTED-CALL entry, so its
    # parameters arrive as a BLOCK OF ADDRESSES in main data rather than in
    # the s-pads.  RESLVE walks it: "SP(0) = ADDRESS OF BLOCK, SP(1) =
    # NUMBER OF PARAMETERS", loading consecutive s-pads with the addresses
    # and then dereferencing the ones its BITMAP marks as integers
    # (BITMAP = 14 octal = 0b1100, i.e. parameters 3 and 4 -- N and M).
    #
    #   MD  0-7   A, eight words (2M for M=4), written by the DMA as floats
    #   MD  8-9   C, the two lags
    #   MD 16     N = 2   raw integer
    #   MD 17     M = 4   raw integer
    #   MD 20-23  the parameter block: addresses of A, C, N, M
    "ACORF": {16: 2, 17: 4, 20: 0, 21: 8, 22: 16, 23: 17},
}

# Routines entered through the ADC STUB (module offset 0) instead of the
# user-directed entry (offset 2).  The stub does `LDSPI 17;DB=BITMAP` then
# `JSR RESLVE`, so SP(17) needs nothing from the harness.
ADC_ENTRY = {"ACORF"}

# An ADC-called routine is entered at its STUB, two words before the
# user-directed entry: `$SUBR Fxxxxx` assembles to `LDSPI 17;DB=BITMAP`
# then `JSR RESLVE`, and RESLVE returns to the user entry once it has
# unpacked the parameter block.  The (F@0, name@2) layout is universal --
# measured across all 99 modules that carry both names -- so ENTRY-2 is
# the stub wherever the module lands.
if ROUTINE in ADC_ENTRY:
    ENTRY = ENTRY - 2

spad_vals, vec_in, CBASE, test_c = ROUTINES[ROUTINE]

HOST_DATA = 0o600
# THE INPUT BUFFER MUST HOLD 2 WORDS PER FLOAT.  These were 16 words apart,
# which fits only EIGHT values -- fine while every routine took at most six
# (A3 + B3), and silently wrong for VMA's nine, whose ninth value landed ON
# the result area and never reached main data.  The symptom was a correct
# ADDRESS fetching a zero VALUE, which reads as an emulator fault and is
# not one.  Kept generous so a three-vector routine cannot overflow it.
HOST_RESULT = 0o700

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
# Raw main-data deposit -- see "Phase 3b" below.  Emitted only when the
# routine declares MD_WORDS, so page zero is untouched for every other
# routine (it is 256 words and each staged constant costs one).
if MD_WORDS.get(ROUTINE):
    pz_const("fn_dep_ma", FN_DEP | 2)      # REGSEL_MA
    pz_const("fn_dep_md", FN_DEP | 13)     # REGSEL_MD_MA
    for _n, (_a, _v) in enumerate(sorted(MD_WORDS[ROUTINE].items())):
        pz_const(f"mdaddr{_n}", _a & 0xFFFF)
        pz_const(f"mdval{_n}", _v & 0xFFFF)
pz_const("dma_ctl_h2a", 0o300)
pz_const("dma_ctl_a2h", 0o340)
pz_const("wc_in", max (2 * len (vec_in), 1))
pz_const("wc_out", 2 * len (test_c))
pz_const("apma_zero", 0)
pz_const("apma_c", CBASE)
pz_const("host_in", HOST_DATA)
pz_const("host_out", HOST_RESULT)
pz_const("entry", ENTRY)

# MICROCODE IS ATTACHED, NOT STAGED.  Page zero is 256 words, this
# harness starts at 0o040 and spends 18 words on control constants, and
# staging a microinstruction costs FOUR -- so only about 51 instructions
# fit and everything past that silently overwrites the s-pad setup.  VDIV
# is 79 instructions (316 words) and came out with SP=[.. 0 0 0 0 0],
# i.e. N=0, so it returned immediately via its own "BNE .+2 / ZDONE:
# RETURN  RETURN WHEN N=0".
#
# fps_attach calls fps_load_apo, which reads the line AFTER "***CODE" as
# "%o %o %o %o" -> load_addr, dummy, ps_size, md_size and loads the four
# octal words per line from there.  So write the LINKED image in that
# form and attach it.  NOTE a shipped .APO must NOT be attached: its line
# after ***CODE is the first code-word quad, which this loader would take
# as the load address.
APO_LOAD = "/tmp/fps_%s_linked.apo" % ROUTINE
with open (APO_LOAD, "w") as fh:
    fh.write ("     3      ***TITLE\n%s\n" % LINK_NAME)
    fh.write ("     0     %o      0      ***CODE\n" % len (code))
    fh.write ("%6o %6o %6o %6o\n" % (0, 0, len (code), 0))
    for word in code:
        fh.write ("%6o %6o %6o %6o\n" % ((word >> 48) & 0xFFFF,
                                          (word >> 32) & 0xFFFF,
                                          (word >> 16) & 0xFFFF,
                                          word & 0xFFFF))
emit ("att fps %s" % APO_LOAD)

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
for i in range(2*len(test_c)):
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

# Phase 1 is gone: the microcode arrives via "att fps", emitted below.

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

# Phase 3b: RAW MAIN-DATA WORDS, via the machine's own FN DEP protocol.
#
# The DMA path above writes main data through the FLOAT conversion, so it
# cannot lay down an ADDRESS or an integer INDEX -- which is what blocked
# the auto-directed-call parameter block (RESLVE reads "SP(0) = ADDRESS OF
# BLOCK, SP(1) = NUMBER OF PARAMETERS" and walks a block of addresses),
# `VINDEX`'s indirect-address mailbox and `SKYSOL`'s MAXA array.
#
# But FN DEP reaches main data directly: REGSEL_MA (2) sets the address
# and REGSEL_MD_MA (13) writes the word, exactly as REGSEL_SPD/REGSEL_SPFN
# do for the s-pads above.  That is the machine's own protocol, not a
# simulator backdoor, and the emulator implements both directions.
#
# It reaches the LOW 16 BITS of a 38-bit word, so addresses and small
# integers fit and a float does not -- which is why the DMA path exists
# alongside it rather than being replaced.
#
# Deposited AFTER the DMA so the transfer cannot overwrite these words.
for _n, (_a, _v) in enumerate(sorted(MD_WORDS.get(ROUTINE, {}).items())):
    inst(dg_lda(0, 0, pz[f"mdaddr{_n}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_ma"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))
    inst(dg_lda(0, 0, pz[f"mdval{_n}"]))
    inst(dg_doa(0, PULSE_N, DEV_FPS))
    inst(dg_lda(0, 0, pz["fn_dep_md"]))
    inst(dg_doa(0, PULSE_S, DEV_FPS))

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
# The readback window must follow the VECTOR LENGTH, not be fixed at
# three values -- a five-element job read 6 words and reported "no
# readback", which looks like a failure to execute and is not.
emit(f"examine {HOST_RESULT:03o}-{HOST_RESULT+2*len(test_c)-1:03o}")
emit("examine fps PSA")
emit("quit")

script = "\n".join(out) + "\n"
outfile = sys.argv[2] if len(sys.argv) > 2 else "/tmp/test_hsr.simh"
with open(outfile, 'w') as f:
    f.write(script)
print(f"Generated {outfile}: {ROUTINE}, {len(code)} AP instructions, "
      f"{len(spad_vals)} s-pads", file=sys.stderr)
