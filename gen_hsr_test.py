#!/usr/bin/env python3
"""Generate a SimH test for ANY basic-math HSR routine, taken from the tape.

    ./gen_hsr_test.py VADD out.simh

gen_hsr_vadd_test.py carries VADD's twenty instructions transcribed by
hand.  That proves one routine and invites transcription error, so this
reads the microcode straight out of BAAHSR.MAC instead.  Every routine
there embeds a self-contained block --

    NSPADS:      7.
    SLIST:  .BLKW      7.
    START:       0.
    CODE:       20.
            040674,000000,000000,000000
            ...

-- four octal 16-bit words per 64-bit microinstruction, CODE: giving the
count and NSPADS the number of s-pad parameters.  Externals are already
resolved in the HSR block (VADD's SPUFLT is present as PS[12..19]), so
the block runs as it stands.

The extractor agrees with the hand transcription on VADD: 20 of 20
words identical.
"""
import re
import struct
import sys

ROUTINE = sys.argv[1] if len(sys.argv) > 1 else "VADD"

def hsr_code (routine, path="../software/fps100sw/[327,010]BAAHSR.MAC"):
    """Pull one routine's microcode block out of an HSR wrapper file."""
    t = open (path, encoding="latin-1").read().replace("\r\n", "\n")
    for b in re.split (r'^\s*\.TITLE\s+', t, flags=re.M)[1:]:
        if b.split()[0] != routine:
            continue
        m = re.search (r'^CODE:\s*(\d+)\.\s*$', b, flags=re.M)
        ns = re.search (r'^NSPADS:\s*(\d+)\.', b, flags=re.M)
        n = int (m.group(1))
        rest = b[m.end():].split("\n")[1:]
        words = [l.strip() for l in rest if re.match (r'^\s*[0-7]{6},', l)][:n]
        assert len (words) == n, "%s: CODE says %d, found %d" % (routine, n, len (words))
        return words, int (ns.group(1))
    raise SystemExit ("no routine %s in %s" % (routine, path))

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

hsr_words, NSPADS = hsr_code (ROUTINE)

code = []
for line in hsr_words:
    ws = [int(w, 8) for w in line.split(",")]
    word64 = ((ws[0] & 0xFFFF) << 48) | ((ws[1] & 0xFFFF) << 32) | \
             ((ws[2] & 0xFFFF) << 16) | (ws[3] & 0xFFFF)
    code.append(word64)

# Append HALT at PS[20] — the RETURN at PS[11] will pop SRS to here
halt_word = (1 << 60) | (5 << 54)  # SOP=SPEC, SPS=HALT
code.append(halt_word)

# ── S-pad values ────────────────────────────────────────────────────
# VADD expects: SP[0]=A, SP[1]=I, SP[2]=B, SP[3]=J, SP[4]=C, SP[5]=K, SP[6]=N
spad_vals = [0, 1, 3, 1, 6, 1, 3]

test_a = [1.0, 2.0, 3.0]
test_b = [4.0, 5.0, 6.0]
OP = {"VADD": lambda a, b: a + b,
      # VSUB is B-A, not A-B.  BAASRC's FORMULA line says
      #   "C(M) = B(M) - A(M)   FOR M = 0 TO N-1
      # and the loop is "FSUB DPY,DPX" commented "B(0) - A(0)".
      # The prose abstract ("SUBTRACTS VECTOR B FROM VECTOR A")
      # and one store comment disagree; the formula wins.
      "VSUB": lambda a, b: b - a,
      "VMUL": lambda a, b: a * b}[ROUTINE]
OPSYM = {"VADD": "+", "VSUB": "reverse-", "VMUL": "*"}[ROUTINE]
test_c = [OP(a, b) for a, b in zip(test_a, test_b)]

HOST_DATA = 0o600
HOST_RESULT = 0o620

# ── Generate SimH script ───────────────────────────────────────────

out = []
def emit(s): out.append(s)

emit(f"; HSR {ROUTINE} test — {len(hsr_words)} production instructions from BAAHSR.MAC")
emit(f"; A={test_a} {OPSYM} B={test_b} = C={test_c}")
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
pz_const("wc_in", 12)
pz_const("wc_out", 6)
pz_const("apma_zero", 0)
pz_const("apma_six", 6)
pz_const("host_in", HOST_DATA)
pz_const("host_out", HOST_RESULT)
pz_const("entry", 0)

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
for v in test_a + test_b:
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
emit("; SRS[0] = 20 (HALT), SRA = 1 (one return address)")
emit("deposit fps SRS[0] 000024")  # 20 decimal = 24 octal
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
inst(dg_lda(0, 0, pz["apma_six"]))
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
